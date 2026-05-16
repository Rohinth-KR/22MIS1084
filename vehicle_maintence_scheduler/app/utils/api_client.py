"""
api_client.py — Reusable authenticated HTTP client for evaluation server APIs.

Provides a centralized, token-aware HTTP client that handles Bearer token
attachment, automatic token refresh on 401, and consistent error handling.
"""

import requests
import logging
from ..config import scheduler_settings

logger = logging.getLogger(__name__)


class EvalAPIClient:
    """
    Authenticated HTTP client for the evaluation server.
    Handles token refresh automatically on 401 Unauthorized.
    """

    def __init__(self):
        self._token = scheduler_settings.ACCESS_TOKEN
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def _get_headers(self) -> dict:
        """Builds authorization headers with current token."""
        return {"Authorization": f"Bearer {self._token}"}

    def _refresh_token(self) -> bool:
        """Re-authenticates to get a fresh access token."""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
        from logging_middleware.logger.auth import TokenManager

        tm = TokenManager()
        new_token = tm.authenticate()
        if new_token:
            self._token = new_token
            scheduler_settings.ACCESS_TOKEN = new_token
            logger.info("Token refreshed successfully.")
            return True
        logger.error("Token refresh failed.")
        return False

    def get(self, url: str, params: dict = None) -> dict:
        """
        Sends an authenticated GET request.
        Auto-retries with fresh token on 401 Unauthorized.

        Args:
            url: The API endpoint URL.
            params: Optional query parameters.

        Returns:
            Parsed JSON response as dict.

        Raises:
            requests.exceptions.HTTPError: On non-recoverable HTTP errors.
            ConnectionError: On network failures.
        """
        try:
            response = self._session.get(
                url, headers=self._get_headers(), params=params, timeout=10
            )

            # Auto-refresh on 401
            if response.status_code == 401:
                logger.warning("Received 401 -- refreshing token and retrying...")
                if self._refresh_token():
                    response = self._session.get(
                        url, headers=self._get_headers(), params=params, timeout=10
                    )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            raise


# Singleton client instance
api_client = EvalAPIClient()
