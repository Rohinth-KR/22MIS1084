"""
main.py — FastAPI Application with Production-Grade Remote Logging

Demonstrates comprehensive logging integration across:
  - API entry points (routes)
  - Service execution
  - Validation failures
  - Exception handling
  - Middleware auto-logging

Every log is sent to the remote evaluation server via the
centralized Log() function. No print() or console logging is used.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from logging_middleware import RemoteLoggingMiddleware, Log


# ─── App Setup ──────────────────────────────────────────────────────────

app = FastAPI(
    title="22MIS1084 — Backend Evaluation",
    description="Phase 2: Logging Middleware Demo",
    version="1.0.0",
)

# Attach the logging middleware — auto-logs every request/response
app.add_middleware(RemoteLoggingMiddleware)


# ─── Startup / Shutdown Events ──────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    Log("backend", "info", "config", "Application startup — middleware and logging initialized")
    Log("backend", "info", "config", "Remote logging connected to evaluation server")


@app.on_event("shutdown")
async def on_shutdown():
    Log("backend", "info", "config", "Application shutdown — graceful termination")


# ─── Health Check Route ─────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint with route-level logging."""
    Log("backend", "info", "route", "Health check endpoint called")
    return {"status": "healthy", "service": "logging-middleware"}


# ─── Demo Routes — Showcasing Logging at Every Layer ────────────────────

@app.get("/api/vehicles")
async def get_vehicles():
    """Demonstrates logging in routes and service layer."""
    Log("backend", "info", "route", "GET /api/vehicles — request received")

    # Service layer logging
    Log("backend", "info", "service", "Fetching vehicle list from data source")

    vehicles = [
        {"id": "V001", "name": "Bus A", "status": "active"},
        {"id": "V002", "name": "Truck B", "status": "maintenance"},
        {"id": "V003", "name": "Van C", "status": "active"},
    ]

    Log("backend", "info", "service", f"Successfully fetched {len(vehicles)} vehicles")
    Log("backend", "debug", "controller", "Serializing vehicle response payload")

    return {"data": vehicles, "count": len(vehicles)}


@app.get("/api/vehicles/{vehicle_id}")
async def get_vehicle_by_id(vehicle_id: str):
    """Demonstrates validation failure logging."""
    Log("backend", "info", "route", f"GET /api/vehicles/{vehicle_id} — request received")

    # Validation
    if not vehicle_id.startswith("V"):
        Log("backend", "warn", "handler", f"Validation failed: invalid vehicle_id format '{vehicle_id}'")
        raise HTTPException(status_code=400, detail=f"Invalid vehicle ID format: {vehicle_id}")

    mock_db = {
        "V001": {"id": "V001", "name": "Bus A", "status": "active", "mileage": 45000},
        "V002": {"id": "V002", "name": "Truck B", "status": "maintenance", "mileage": 120000},
    }

    # Repository layer logging
    Log("backend", "info", "repository", f"Querying vehicle store for ID: {vehicle_id}")

    vehicle = mock_db.get(vehicle_id)
    if not vehicle:
        Log("backend", "warn", "repository", f"Vehicle not found in store: {vehicle_id}")
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")

    Log("backend", "info", "service", f"Vehicle {vehicle_id} retrieved successfully")
    return {"data": vehicle}


@app.get("/api/optimize")
async def run_optimization(strategy: str = Query(default="greedy", regex="^(greedy|dp|genetic)$")):
    """Demonstrates optimization execution logging."""
    Log("backend", "info", "route", f"GET /api/optimize — strategy={strategy}")
    Log("backend", "info", "service", f"Starting optimization with strategy: {strategy}")

    # Simulate optimization steps
    Log("backend", "debug", "service", "Loading depot and vehicle constraints")
    Log("backend", "debug", "service", "Computing optimal schedule matrix")
    Log("backend", "info", "service", f"Optimization complete using {strategy} strategy — 3 schedules generated")

    return {
        "strategy": strategy,
        "schedules_generated": 3,
        "status": "optimized",
    }


@app.get("/api/external-fetch")
async def fetch_external_data():
    """Demonstrates API fetch logging and retry awareness."""
    Log("backend", "info", "route", "GET /api/external-fetch — initiating external API call")
    Log("backend", "info", "service", "Attempting to fetch data from external depot API")

    # Simulating an API fetch scenario
    try:
        Log("backend", "debug", "utils", "Building request headers with Bearer token")
        Log("backend", "info", "service", "External API responded with 200 OK")
        return {"source": "external_depot_api", "records": 15, "status": "success"}
    except Exception as e:
        Log("backend", "error", "service", f"External API fetch failed: {str(e)}")
        Log("backend", "warn", "utils", "Retry mechanism triggered — attempt 1 of 3")
        raise HTTPException(status_code=502, detail="External API unavailable")


@app.get("/api/error-demo")
async def error_demo():
    """Demonstrates exception and fatal error logging."""
    Log("backend", "info", "route", "GET /api/error-demo — triggering intentional error")
    Log("backend", "warn", "controller", "This endpoint intentionally raises an exception for testing")

    # This will be caught by the middleware and logged as fatal
    raise ValueError("Intentional error for testing middleware exception logging")


@app.get("/api/db-check")
async def db_health():
    """Demonstrates database layer logging."""
    Log("backend", "info", "route", "GET /api/db-check — database health check")
    Log("backend", "info", "db", "Pinging database connection pool")
    Log("backend", "debug", "db", "Connection pool: 5 active, 3 idle, 0 waiting")
    Log("backend", "info", "db", "Database health check passed")

    return {"database": "healthy", "pool_active": 5, "pool_idle": 3}


# ─── Global Exception Handler ──────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Logs all HTTP exceptions before returning the response."""
    Log(
        "backend", "warn", "handler",
        f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ─── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    Log("backend", "info", "config", "Starting server on http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
