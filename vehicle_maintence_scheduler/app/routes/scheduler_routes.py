"""
scheduler_routes.py — API routes for the Vehicle Maintenance Scheduler.

Exposes REST endpoints that internally fetch depot/vehicle data from the
evaluation API, run 0/1 Knapsack optimization, and return optimal schedules.

Endpoints:
    GET /health              — Service health check
    GET /depots              — List all depots from evaluation API
    GET /vehicles            — List all vehicle tasks from evaluation API
    GET /schedule/{depot_id} — Optimized schedule for a specific depot
    GET /schedule/all        — Optimized schedules for all depots
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from fastapi import APIRouter, HTTPException
from logging_middleware.logger.logger import Log

from ..services.depot_service import DepotService
from ..services.vehicle_service import VehicleService
from ..services.optimization_service import OptimizationService
from ..models.schemas import (
    ScheduleResult,
    AllSchedulesResult,
    DepotListResponse,
    VehicleListResponse,
    HealthResponse,
)

router = APIRouter()


# ─── Health Check ───────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check endpoint."""
    Log("backend", "info", "route", "GET /health check")
    return HealthResponse(
        status="healthy",
        service="vehicle-maintenance-scheduler",
        version="1.0.0",
    )


# ─── Depot Endpoints ───────────────────────────────────────────────────

@router.get("/depots", response_model=DepotListResponse)
async def list_depots():
    """Fetches and returns all depots from the evaluation API."""
    Log("backend", "info", "route", "GET /depots")

    try:
        depots = DepotService.fetch_all_depots()
        Log("backend", "info", "controller", f"Returning {len(depots)} depots")
        return DepotListResponse(depots=depots, count=len(depots))

    except Exception as e:
        Log("backend", "error", "controller", f"Depot list fail: {str(e)[:20]}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch depots: {str(e)}")


# ─── Vehicle Endpoints ─────────────────────────────────────────────────

@router.get("/vehicles", response_model=VehicleListResponse)
async def list_vehicles():
    """Fetches and returns all vehicle maintenance tasks from the evaluation API."""
    Log("backend", "info", "route", "GET /vehicles")

    try:
        vehicles = VehicleService.fetch_all_vehicles()
        valid_vehicles = VehicleService.validate_tasks(vehicles)
        Log("backend", "info", "controller",
            f"Returning {len(valid_vehicles)} vehicles")
        return VehicleListResponse(vehicles=valid_vehicles, count=len(valid_vehicles))

    except Exception as e:
        Log("backend", "error", "controller", f"Vehicle list fail: {str(e)[:18]}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch vehicles: {str(e)}")


# ─── Schedule Endpoints ────────────────────────────────────────────────

@router.get("/schedule/all", response_model=AllSchedulesResult)
async def get_all_schedules():
    """
    Computes optimal maintenance schedules for ALL depots.
    Fetches live data, runs 0/1 Knapsack DP, returns results.
    """
    Log("backend", "info", "route", "GET /schedule/all")
    start = time.time()

    try:
        # Fetch live data from evaluation APIs
        depots = DepotService.fetch_all_depots()
        vehicles = VehicleService.fetch_all_vehicles()
        valid_vehicles = VehicleService.validate_tasks(vehicles)

        Log("backend", "info", "service",
            f"{len(depots)} depots, {len(valid_vehicles)} tasks")

        # Run optimization for all depots
        results = OptimizationService.optimize_all_depots(depots, valid_vehicles)

        elapsed = round((time.time() - start) * 1000, 2)
        Log("backend", "info", "controller",
            f"All schedules done in {elapsed}ms")

        return AllSchedulesResult(
            schedules=results,
            totalDepots=len(results),
        )

    except Exception as e:
        Log("backend", "error", "controller", f"Schedule fail: {str(e)[:20]}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/schedule/{depot_id}", response_model=ScheduleResult)
async def get_schedule_for_depot(depot_id: int):
    """
    Computes optimal maintenance schedule for a SPECIFIC depot.

    Path Parameters:
        depot_id: Integer ID of the depot to optimize.
    """
    Log("backend", "info", "route", f"GET /schedule/{depot_id}")

    # Validation
    if depot_id <= 0:
        Log("backend", "warn", "handler", f"Bad depot_id: {depot_id}")
        raise HTTPException(status_code=400, detail=f"Invalid depot ID: {depot_id}")

    start = time.time()

    try:
        # Fetch depot info
        depot = DepotService.fetch_depot_by_id(depot_id)
        Log("backend", "info", "service",
            f"Depot {depot_id}: {depot.MechanicHours}h cap")

        # Fetch vehicle tasks
        vehicles = VehicleService.fetch_all_vehicles()
        valid_vehicles = VehicleService.validate_tasks(vehicles)

        Log("backend", "info", "service",
            f"Optimize: {len(valid_vehicles)}t {depot.MechanicHours}h")

        # Run knapsack optimization
        result = OptimizationService.solve_knapsack(
            vehicles=valid_vehicles,
            capacity=depot.MechanicHours,
            depot_id=depot_id,
        )

        elapsed = round((time.time() - start) * 1000, 2)
        Log("backend", "info", "controller",
            f"Depot {depot_id} done in {elapsed}ms")

        return result

    except ValueError as e:
        Log("backend", "warn", "handler", f"Depot not found: {str(e)[:20]}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        Log("backend", "error", "controller",
            f"Depot {depot_id} fail: {str(e)[:20]}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")
