"""
test_logger.py — Standalone test script for the remote logging system.

Sends test logs across all valid levels and packages to verify the
centralized Log() function is working correctly with the evaluation server.

Usage:
    python test_logger.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logging_middleware.logger.logger import Log, ALLOWED_LEVELS, ALLOWED_PACKAGES


def main():
    print("=" * 60)
    print("  Phase 2 -- Remote Logger Test Suite")
    print("=" * 60)

    # ── Test 1: Basic logging across all levels ─────────────────
    print("\n[Test 1] Logging across all levels (sync mode)")
    print("-" * 50)

    test_messages = {
        "debug":  "Debug-level diagnostic: checking internal state",
        "info":   "Service initialized and ready to accept requests",
        "warn":   "Token expires in 5 minutes, consider refreshing",
        "error":  "Failed to connect to external depot API",
        "fatal":  "Critical: database connection pool exhausted",
    }

    for level, message in test_messages.items():
        result = Log("backend", level, "service", message, sync=True)
        status = "SENT" if result else "FAILED"
        icon = "+" if result else "x"
        print(f"  [{level.upper():5s}] {icon} {status} : {message[:55]}")
        time.sleep(0.5)

    # ── Test 2: Logging across different packages ───────────────
    print("\n[Test 2] Logging from different packages")
    print("-" * 50)

    package_tests = [
        ("route",       "GET /api/vehicles endpoint invoked"),
        ("controller",  "Request validated and forwarded to service"),
        ("service",     "Business logic executed, 3 results returned"),
        ("repository",  "Query executed on vehicles collection"),
        ("db",          "Connection acquired from pool, 4 remaining"),
        ("middleware",  "Request processed in 12.5ms"),
        ("handler",     "HTTP 404: vehicle V999 not found"),
        ("auth",        "Bearer token validated, user authenticated"),
        ("config",      "Environment loaded, 8 variables configured"),
        ("utils",       "Date parsing: ISO 8601 format validated"),
        ("cache",       "Cache miss for key depot:D1, fetching from DB"),
        ("cron_job",    "Scheduled maintenance check triggered"),
        ("domain",      "Vehicle entity state transition to maintenance"),
    ]

    for package, message in package_tests:
        result = Log("backend", "info", package, message, sync=True)
        icon = "+" if result else "x"
        print(f"  {icon} [{package:12s}] {message[:55]}")
        time.sleep(0.5)

    # ── Test 3: Validation enforcement ──────────────────────────
    print("\n[Test 3] Validation enforcement (should reject invalid inputs)")
    print("-" * 50)

    invalid_tests = [
        ("frontend", "info",    "service",   "Should reject: invalid stack"),
        ("backend",  "verbose", "service",   "Should reject: invalid level"),
        ("backend",  "info",    "frontend",  "Should reject: invalid package"),
        ("backend",  "info",    "service",   ""),  # truly empty message
    ]

    for stack, level, package, message in invalid_tests:
        result = Log(stack, level, package, message, sync=True)
        status = "+ REJECTED" if not result else "x ACCEPTED (bad!)"
        print(f"  {status} : stack={stack}, level={level}, pkg={package}")
        time.sleep(0.3)

    # ── Summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  All tests complete -- remote logs dispatched to server")
    print("=" * 60)
    print(f"\n  Target API : http://4.224.186.213/evaluation-service/logs")
    print("  Auth       : Bearer token (auto-refreshed)")
    print("  Validation : Strict lowercase, predefined values only\n")


if __name__ == "__main__":
    main()
