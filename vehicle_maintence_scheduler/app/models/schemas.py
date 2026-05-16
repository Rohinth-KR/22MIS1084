"""
schemas.py — Pydantic models for request/response validation.

Defines strongly-typed data models for depots, vehicles, tasks,
and optimization results used throughout the microservice.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ─── Input Models (from Evaluation API) ─────────────────────────────────

class Depot(BaseModel):
    """Represents a maintenance depot with limited mechanic-hours."""
    ID: int = Field(..., description="Unique depot identifier")
    MechanicHours: int = Field(..., ge=0, description="Available mechanic-hours per day")


class Vehicle(BaseModel):
    """Represents a vehicle maintenance task with duration and impact."""
    TaskID: str = Field(..., description="Unique task identifier (UUID)")
    Duration: int = Field(..., ge=0, description="Maintenance duration in hours (knapsack weight)")
    Impact: int = Field(..., ge=0, description="Operational impact score (knapsack value)")


# ─── Output Models (API Responses) ──────────────────────────────────────

class SelectedTask(BaseModel):
    """A task selected by the optimization algorithm."""
    taskId: str = Field(..., description="Task UUID")
    duration: int = Field(..., description="Hours required")
    impact: int = Field(..., description="Operational impact score")


class ScheduleResult(BaseModel):
    """Optimization result for a single depot."""
    depotId: int = Field(..., description="Depot identifier")
    maxImpact: int = Field(..., description="Maximum total impact score achieved")
    totalHoursUsed: int = Field(..., description="Total mechanic-hours consumed")
    availableHours: int = Field(..., description="Total mechanic-hours available at this depot")
    selectedTasks: List[SelectedTask] = Field(..., description="List of optimally selected tasks")
    totalTasksConsidered: int = Field(0, description="Total tasks evaluated")
    utilizationPercent: float = Field(0.0, description="Percentage of available hours utilized")


class AllSchedulesResult(BaseModel):
    """Optimization results for all depots."""
    schedules: List[ScheduleResult]
    totalDepots: int
    algorithm: str = "0/1 Knapsack Dynamic Programming"


class DepotListResponse(BaseModel):
    """Response for listing all depots."""
    depots: List[Depot]
    count: int


class VehicleListResponse(BaseModel):
    """Response for listing all vehicle tasks."""
    vehicles: List[Vehicle]
    count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
