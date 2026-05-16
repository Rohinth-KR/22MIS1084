"""
vehicle_service.py — Service layer for fetching vehicle task data from evaluation API.

Fetches vehicle maintenance tasks dynamically from the protected evaluation server.
No hardcoded data. All requests are authenticated with Bearer token.
"""

import sys
import os
import logging
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from logging_middleware.logger.logger import Log
from ..utils.api_client import api_client
from ..config import scheduler_settings
from ..models.schemas import Vehicle

logger = logging.getLogger(__name__)


class VehicleService:
    """Service responsible for fetching and managing vehicle task data."""

    @staticmethod
    def fetch_all_vehicles() -> List[Vehicle]:
        """
        Fetches all vehicle maintenance tasks from the evaluation server API.

        Returns:
            List of Vehicle objects with TaskID, Duration, and Impact.

        Raises:
            Exception: If the API call fails after token refresh retry.
        """
        Log("backend", "info", "service", "Fetching vehicles from eval API")

        try:
            data = api_client.get(scheduler_settings.VEHICLE_API_URL)
            raw_vehicles = data.get("vehicles", [])

            if not raw_vehicles:
                Log("backend", "warn", "service", "Vehicle API: empty list")
                return []

            vehicles = [Vehicle(**v) for v in raw_vehicles]

            Log("backend", "info", "service",
                f"Fetched {len(vehicles)} vehicles OK")

            # Log summary statistics
            total_duration = sum(v.Duration for v in vehicles)
            total_impact = sum(v.Impact for v in vehicles)
            Log("backend", "debug", "service",
                f"Tasks: dur={total_duration}h imp={total_impact}")

            return vehicles

        except Exception as e:
            Log("backend", "error", "service", f"Vehicle fetch fail: {str(e)[:18]}")
            raise

    @staticmethod
    def validate_tasks(vehicles: List[Vehicle]) -> List[Vehicle]:
        """
        Validates fetched vehicle tasks, filtering out any with invalid data.

        Args:
            vehicles: Raw list of Vehicle objects.

        Returns:
            Filtered list of valid Vehicle objects.
        """
        valid = []
        for v in vehicles:
            if v.Duration <= 0:
                Log("backend", "warn", "handler",
                    f"Skip task: bad duration {v.Duration}")
                continue
            if v.Impact < 0:
                Log("backend", "warn", "handler",
                    f"Skip task: neg impact {v.Impact}")
                continue
            valid.append(v)

        skipped = len(vehicles) - len(valid)
        if skipped > 0:
            Log("backend", "warn", "handler",
                f"Filtered {skipped}/{len(vehicles)} tasks")

        return valid
