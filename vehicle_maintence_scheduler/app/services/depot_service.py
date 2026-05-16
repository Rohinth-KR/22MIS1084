"""
depot_service.py — Service layer for fetching depot data from evaluation API.

Fetches depot information dynamically from the protected evaluation server.
No hardcoded data. All requests are authenticated with Bearer token.
"""

import sys
import os
import logging
from typing import List

# Ensure root is on path for logging_middleware imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from logging_middleware.logger.logger import Log
from ..utils.api_client import api_client
from ..config import scheduler_settings
from ..models.schemas import Depot

logger = logging.getLogger(__name__)


class DepotService:
    """Service responsible for fetching and managing depot data."""

    @staticmethod
    def fetch_all_depots() -> List[Depot]:
        """
        Fetches all depots from the evaluation server API.

        Returns:
            List of Depot objects with ID and MechanicHours.

        Raises:
            Exception: If the API call fails after token refresh retry.
        """
        Log("backend", "info", "service", "Fetching depots from eval API")

        try:
            data = api_client.get(scheduler_settings.DEPOT_API_URL)
            raw_depots = data.get("depots", [])

            if not raw_depots:
                Log("backend", "warn", "service", "Depot API: empty list")
                return []

            depots = [Depot(**d) for d in raw_depots]

            Log("backend", "info", "service",
                f"Fetched {len(depots)} depots OK")

            for depot in depots:
                Log("backend", "debug", "service",
                    f"Depot {depot.ID}: {depot.MechanicHours}h avail")

            return depots

        except Exception as e:
            Log("backend", "error", "service", f"Depot fetch fail: {str(e)[:20]}")
            raise

    @staticmethod
    def fetch_depot_by_id(depot_id: int) -> Depot:
        """
        Fetches a specific depot by ID.

        Args:
            depot_id: The depot identifier to look up.

        Returns:
            Depot object if found.

        Raises:
            ValueError: If depot ID is not found.
        """
        Log("backend", "info", "service", f"Looking up depot ID={depot_id}")

        depots = DepotService.fetch_all_depots()
        for depot in depots:
            if depot.ID == depot_id:
                Log("backend", "info", "service",
                    f"Found depot {depot_id}: {depot.MechanicHours}h")
                return depot

        Log("backend", "warn", "service", f"Depot {depot_id} not found")
        raise ValueError(f"Depot with ID {depot_id} not found")
