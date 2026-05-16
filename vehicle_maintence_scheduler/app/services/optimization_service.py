"""
optimization_service.py — 0/1 Knapsack Dynamic Programming Optimizer.

Solves the Vehicle Maintenance Scheduling problem using the classic
0/1 Knapsack algorithm via bottom-up Dynamic Programming.

Problem Mapping:
    - Duration  = Weight  (hours required for each task)
    - Impact    = Value   (operational importance score)
    - MechanicHours = Capacity (available hours at the depot)

Goal: Maximize total operational impact without exceeding mechanic-hours.

Time Complexity:  O(n * W) where n = tasks, W = capacity
Space Complexity: O(n * W) — full DP table for backtracking
"""

import sys
import os
import time
import logging
from typing import List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from logging_middleware.logger.logger import Log
from ..models.schemas import Vehicle, SelectedTask, ScheduleResult

logger = logging.getLogger(__name__)


class OptimizationService:
    """
    Implements the 0/1 Knapsack Dynamic Programming solution
    for optimal vehicle maintenance scheduling.
    """

    @staticmethod
    def solve_knapsack(
        vehicles: List[Vehicle],
        capacity: int,
        depot_id: int
    ) -> ScheduleResult:
        """
        Solves the 0/1 Knapsack problem for a given depot.

        Args:
            vehicles: List of vehicle maintenance tasks (items).
            capacity: Available mechanic-hours at the depot (knapsack capacity).
            depot_id: Identifier for the depot being optimized.

        Returns:
            ScheduleResult containing optimally selected tasks,
            maximum impact, and total hours used.
        """
        n = len(vehicles)

        Log("backend", "info", "service",
            f"Knapsack DP: depot {depot_id} {n}t {capacity}h")

        start_time = time.time()

        # ─── Edge Cases ─────────────────────────────────────────
        if n == 0 or capacity <= 0:
            Log("backend", "warn", "service",
                f"Depot {depot_id}: empty, no tasks")
            return ScheduleResult(
                depotId=depot_id,
                maxImpact=0,
                totalHoursUsed=0,
                availableHours=capacity,
                selectedTasks=[],
                totalTasksConsidered=n,
                utilizationPercent=0.0,
            )

        # ─── Build DP Table ─────────────────────────────────────
        # dp[i][w] = max impact using first i items with capacity w
        Log("backend", "debug", "service",
            f"DP table: {n+1}x{capacity+1} cells")

        dp = [[0] * (capacity + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            weight = vehicles[i - 1].Duration   # Duration = Weight
            value = vehicles[i - 1].Impact      # Impact = Value

            for w in range(capacity + 1):
                if weight <= w:
                    dp[i][w] = max(
                        dp[i - 1][w],                    # Skip this task
                        dp[i - 1][w - weight] + value    # Include this task
                    )
                else:
                    dp[i][w] = dp[i - 1][w]  # Can't fit, skip

        max_impact = dp[n][capacity]

        # ─── Backtrack to Find Selected Tasks ───────────────────
        Log("backend", "debug", "service",
            f"Backtracking: max_impact={max_impact}")

        selected_tasks = []
        w = capacity

        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                # This task was included in the optimal solution
                task = vehicles[i - 1]
                selected_tasks.append(SelectedTask(
                    taskId=task.TaskID,
                    duration=task.Duration,
                    impact=task.Impact,
                ))
                w -= task.Duration

        # Reverse to maintain original order
        selected_tasks.reverse()

        total_hours_used = sum(t.duration for t in selected_tasks)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        utilization = round((total_hours_used / capacity) * 100, 1) if capacity > 0 else 0.0

        # ─── Log Results ────────────────────────────────────────
        Log("backend", "info", "service",
            f"Depot {depot_id}: impact={max_impact} {elapsed_ms}ms")

        return ScheduleResult(
            depotId=depot_id,
            maxImpact=max_impact,
            totalHoursUsed=total_hours_used,
            availableHours=capacity,
            selectedTasks=selected_tasks,
            totalTasksConsidered=n,
            utilizationPercent=utilization,
        )

    @staticmethod
    def optimize_all_depots(
        depots: list,
        vehicles: List[Vehicle]
    ) -> List[ScheduleResult]:
        """
        Runs knapsack optimization for every depot.

        Args:
            depots: List of Depot objects.
            vehicles: List of Vehicle maintenance tasks (shared across depots).

        Returns:
            List of ScheduleResult, one per depot.
        """
        Log("backend", "info", "service",
            f"Optimizing {len(depots)} depots {len(vehicles)} tasks")

        results = []
        for depot in depots:
            result = OptimizationService.solve_knapsack(
                vehicles=vehicles,
                capacity=depot.MechanicHours,
                depot_id=depot.ID,
            )
            results.append(result)

        total_impact = sum(r.maxImpact for r in results)
        Log("backend", "info", "service",
            f"All depots done: impact={total_impact}")

        return results
