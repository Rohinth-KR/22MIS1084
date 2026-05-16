# 22MIS1084 - Backend Evaluation

This repository contains the backend evaluation submission for 22MIS1084.

## Repository Structure

```
22MIS1084/
├── logging_middleware/              # Phase 1 & 2: Auth + Logging Middleware
│   ├── middleware.py                # FastAPI auto-logging middleware
│   └── logger/
│       ├── auth.py                  # TokenManager (register + authenticate)
│       ├── config.py                # Settings from environment variables
│       └── logger.py                # Centralized Log() function
│
├── vehicle_maintence_scheduler/     # Phase 3: Vehicle Maintenance Scheduler
│   └── app/
│       ├── main.py                  # FastAPI microservice entry point
│       ├── config.py                # Scheduler configuration
│       ├── models/schemas.py        # Pydantic data models
│       ├── routes/scheduler_routes.py  # REST API endpoints
│       ├── services/
│       │   ├── depot_service.py     # Depot data fetching
│       │   ├── vehicle_service.py   # Vehicle task fetching
│       │   └── optimization_service.py  # 0/1 Knapsack DP solver
│       └── utils/api_client.py      # Authenticated HTTP client
│
├── notification_system_design.md    # Phase 4: Notification System Design
├── auth_manager.py                  # Standalone auth runner
├── main.py                          # Phase 2 logging demo app
├── test_logger.py                   # Logger test suite
├── requirements.txt                 # Python dependencies
└── .gitignore                       # Ignores .env, venv, __pycache__, etc.
```

## Phases

- Phase 1: Registration & Authentication Setup (Complete)
- Phase 2: Logging Middleware with Remote Log() Function (Complete)
- Phase 3: Vehicle Maintenance Scheduler Microservice (Complete)
- Phase 4: Notification System Design (Pending)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Phase 1: Run registration/auth
python auth_manager.py

# Phase 2: Test remote logging
python test_logger.py

# Phase 3: Start vehicle scheduler (port 8001)
python -m vehicle_maintence_scheduler.app.main
```

## Phase 3 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Service health check |
| GET | /depots | List all depots from eval API |
| GET | /vehicles | List all vehicle tasks from eval API |
| GET | /schedule/{depot_id} | Optimal schedule for a specific depot |
| GET | /schedule/all | Optimal schedules for all depots |

## Algorithm

**0/1 Knapsack Dynamic Programming** — maximizes operational impact within mechanic-hour constraints per depot.

- Duration = Weight | Impact = Value | MechanicHours = Capacity
- Time: O(n * W) | Space: O(n * W)
