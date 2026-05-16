"""
config.py — Configuration for Vehicle Maintenance Scheduler Microservice.

Loads environment variables and defines API endpoints for
the evaluation server's depot and vehicle APIs.
"""

import os
import sys
from dotenv import load_dotenv

# Load .env from project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))


class SchedulerSettings:
    """Centralized configuration for the scheduler microservice."""

    # Evaluation server base URL
    BASE_URL = "http://4.224.186.213/evaluation-service"

    # API endpoints
    DEPOT_API_URL = f"{BASE_URL}/depots"
    VEHICLE_API_URL = f"{BASE_URL}/vehicles"

    # Auth credentials (loaded from root .env)
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

    # App settings
    HOST = os.getenv("SCHEDULER_HOST", "127.0.0.1")
    PORT = int(os.getenv("SCHEDULER_PORT", "8001"))


scheduler_settings = SchedulerSettings()
