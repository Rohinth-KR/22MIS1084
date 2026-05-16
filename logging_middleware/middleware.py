"""
middleware.py — Production-Grade FastAPI Logging Middleware

Intercepts every HTTP request/response and automatically sends structured
remote logs to the evaluation server using the centralized Log() function.

Logs captured:
  - Request entry (method, path, client IP)
  - Response completion (status code, processing time)
  - Unhandled exceptions (stack trace, error details)

Usage:
    from logging_middleware import RemoteLoggingMiddleware

    app = FastAPI()
    app.add_middleware(RemoteLoggingMiddleware)
"""

import time
import traceback
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from .logger.logger import Log


class RemoteLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that provides automatic request/response logging
    to the remote evaluation server. Every API call is tracked.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        method = request.method
        path = request.url.path
        client = request.client.host if request.client else "unknown"

        # ── Log: Request Entry ──────────────────────────────────
        Log(
            "backend", "info", "middleware",
            f"{method} {path} from {client[:15]}"
        )

        try:
            response = await call_next(request)
            process_time_ms = round((time.time() - start_time) * 1000, 2)

            # ── Log: Request Completion ─────────────────────────
            level = "info" if response.status_code < 400 else "warn"
            if response.status_code >= 500:
                level = "error"

            Log(
                "backend", level, "middleware",
                f"{method} {path} {response.status_code} {process_time_ms}ms"
            )

            # Attach timing header for observability
            response.headers["X-Process-Time-Ms"] = str(process_time_ms)
            return response

        except Exception as exc:
            process_time_ms = round((time.time() - start_time) * 1000, 2)
            error_trace = traceback.format_exc()

            # ── Log: Unhandled Exception ────────────────────────
            Log(
                "backend", "fatal", "middleware",
                f"Exception {method} {path} {process_time_ms}ms"
            )
            Log(
                "backend", "error", "middleware",
                f"{str(exc)[:48]}"
            )

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )
