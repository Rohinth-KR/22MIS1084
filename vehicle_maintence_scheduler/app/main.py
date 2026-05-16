"""
main.py — Vehicle Maintenance Scheduler Microservice Entry Point.

A production-grade FastAPI microservice that:
  1. Fetches depot and vehicle data from the evaluation server APIs
  2. Runs 0/1 Knapsack Dynamic Programming optimization
  3. Returns optimally scheduled maintenance tasks per depot

Architecture:
  - Routes layer     → scheduler_routes.py
  - Service layer    → depot_service.py, vehicle_service.py, optimization_service.py
  - Models layer     → schemas.py (Pydantic validation)
  - Utils layer      → api_client.py (authenticated HTTP client)
  - Middleware layer  → RemoteLoggingMiddleware (Phase 2)
  - Config layer     → config.py (environment variables)

Usage:
    python -m vehicle_maintence_scheduler.app.main
    OR
    cd vehicle_maintence_scheduler && python -m app.main
"""

import sys
import os

# Ensure project root is on path for logging_middleware imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from logging_middleware import RemoteLoggingMiddleware, Log
from .routes.scheduler_routes import router
from .config import scheduler_settings


# ─── App Setup ──────────────────────────────────────────────────────────

app = FastAPI(
    title="Vehicle Maintenance Scheduler",
    description=(
        "Microservice for optimizing vehicle maintenance schedules using "
        "0/1 Knapsack Dynamic Programming. Fetches live data from the "
        "evaluation server and computes optimal task selection per depot."
    ),
    version="1.0.0",
)

# Attach Phase 2 logging middleware — auto-logs every request/response
app.add_middleware(RemoteLoggingMiddleware)

# Register routes
app.include_router(router)


# ─── Lifecycle Events ──────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    Log("backend", "info", "config",
        "Scheduler started, logging active")
    Log("backend", "info", "config",
        "Remote logging connected")


@app.on_event("shutdown")
async def on_shutdown():
    Log("backend", "info", "config", "Scheduler shutting down")


# ─── Global Exception Handler ──────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    Log("backend", "error", "handler",
        f"Unhandled: {str(exc)[:30]}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


# ─── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    Log("backend", "info", "config",
        f"Starting scheduler on {scheduler_settings.HOST}:{scheduler_settings.PORT}")
    uvicorn.run(
        "vehicle_maintence_scheduler.app.main:app",
        host=scheduler_settings.HOST,
        port=scheduler_settings.PORT,
        reload=True,
    )
