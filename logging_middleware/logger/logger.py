"""
logger.py — Centralized Remote Logging Module (Production-Grade)

Provides the reusable Log() function that sends structured log entries
to the evaluation server's remote logging API via POST request with
Bearer token authentication.

This is NOT a console logger — it is a centralized remote observability system.

Usage:
    from logging_middleware.logger import Log

    Log("backend", "info", "service", "Fetched vehicle data successfully")
"""

import logging
import threading
import requests
from typing import Optional

from .config import settings
from .auth import TokenManager

# Internal Python logger — used ONLY for meta-logging (errors within the logging system itself)
_internal = logging.getLogger("RemoteLogger")

# ─── Allowed Values (strict validation) ─────────────────────────────────

ALLOWED_STACKS = frozenset({"backend"})

ALLOWED_LEVELS = frozenset({"debug", "info", "warn", "error", "fatal"})

ALLOWED_PACKAGES = frozenset({
    "cache",
    "controller",
    "cron_job",
    "db",
    "domain",
    "handler",
    "repository",
    "route",
    "service",
    "auth",
    "config",
    "middleware",
    "utils",
})

# ─── Singleton Token Manager ────────────────────────────────────────────

_token_manager = TokenManager()

# ─── Validation ─────────────────────────────────────────────────────────

def _validate(stack: str, level: str, package: str, message: str) -> list[str]:
    """Validates all four fields against allowed values. Returns list of error strings."""
    errors = []

    if stack not in ALLOWED_STACKS:
        errors.append(f"Invalid stack '{stack}'. Allowed: {sorted(ALLOWED_STACKS)}")
    if level not in ALLOWED_LEVELS:
        errors.append(f"Invalid level '{level}'. Allowed: {sorted(ALLOWED_LEVELS)}")
    if package not in ALLOWED_PACKAGES:
        errors.append(f"Invalid package '{package}'. Allowed: {sorted(ALLOWED_PACKAGES)}")
    if not message or not isinstance(message, str) or not message.strip():
        errors.append("Message must be a non-empty string.")

    return errors

# ─── Core Transport ─────────────────────────────────────────────────────

def _send_log(payload: dict, _retried: bool = False) -> bool:
    """
    Sends a single log payload to the remote logging API.
    Auto-refreshes the token and retries once on 401 Unauthorized.
    Returns True on success, False on failure.
    """
    token = _token_manager.get_valid_token()
    if not token:
        _internal.warning("No ACCESS_TOKEN available — cannot send remote log.")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            settings.LOGGING_API_URL,
            json=payload,
            headers=headers,
            timeout=5,
        )
        response.raise_for_status()
        _internal.debug(f"Remote log sent: [{payload['level']}] {payload['package']} — {payload['message']}")
        return True
    except requests.exceptions.HTTPError as e:
        # Auto-refresh token on 401 and retry once
        if e.response is not None and e.response.status_code == 401 and not _retried:
            _internal.warning("Token expired -- re-authenticating automatically...")
            settings.ACCESS_TOKEN = None  # Force re-auth
            new_token = _token_manager.authenticate()
            if new_token:
                _internal.info("Token refreshed successfully -- retrying log.")
                return _send_log(payload, _retried=True)
        resp_text = e.response.text if e.response is not None else "no response body"
        _internal.error(f"Failed to send remote log ({e.response.status_code}): {resp_text}")
        return False
    except requests.exceptions.RequestException as e:
        _internal.error(f"Failed to send remote log: {e}")
        return False

# ─── Public API ──────────────────────────────────────────────────────────

def Log(stack: str, level: str, package: str, message: str, *, sync: bool = False) -> bool:
    """
    Centralized remote logging function.

    Sends a structured log entry to the evaluation server's logging API
    with Bearer token authentication. All values are validated and enforced
    to be lowercase.

    Args:
        stack:   Must be "backend".
        level:   One of "debug", "info", "warn", "error", "fatal".
        package: One of the allowed backend packages (e.g. "service", "controller", "route").
        message: Descriptive log message for diagnosing real-world issues.
        sync:    If True, blocks until the log is sent. Default False (non-blocking).

    Returns:
        True if the log was accepted (validation passed). Does NOT guarantee delivery
        when sync=False, as the log is dispatched on a background thread.

    Example:
        Log("backend", "info", "service", "Vehicle data fetched for depot D1")
        Log("backend", "error", "db", "Connection pool exhausted", sync=True)
    """
    # Enforce lowercase and strip whitespace
    stack = str(stack).lower().strip()
    level = str(level).lower().strip()
    package = str(package).lower().strip()
    message = str(message).strip()

    # Validate strictly
    errors = _validate(stack, level, package, message)
    if errors:
        for err in errors:
            _internal.error(f"Log validation failed: {err}")
        return False

    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message,
    }

    if sync:
        # Blocking — wait for the request to complete
        return _send_log(payload)
    else:
        # Non-blocking — fire and forget on a daemon thread
        thread = threading.Thread(target=_send_log, args=(payload,), daemon=True)
        thread.start()
        return True


# ─── Convenience Wrappers ───────────────────────────────────────────────
# These make logging even cleaner throughout the application.

def log_debug(package: str, message: str, **kwargs) -> bool:
    """Shortcut: Log('backend', 'debug', package, message)"""
    return Log("backend", "debug", package, message, **kwargs)


def log_info(package: str, message: str, **kwargs) -> bool:
    """Shortcut: Log('backend', 'info', package, message)"""
    return Log("backend", "info", package, message, **kwargs)


def log_warn(package: str, message: str, **kwargs) -> bool:
    """Shortcut: Log('backend', 'warn', package, message)"""
    return Log("backend", "warn", package, message, **kwargs)


def log_error(package: str, message: str, **kwargs) -> bool:
    """Shortcut: Log('backend', 'error', package, message)"""
    return Log("backend", "error", package, message, **kwargs)


def log_fatal(package: str, message: str, **kwargs) -> bool:
    """Shortcut: Log('backend', 'fatal', package, message)"""
    return Log("backend", "fatal", package, message, **kwargs)
