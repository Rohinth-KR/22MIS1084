# 22MIS1084 - Backend Evaluation

This repository contains the complete backend evaluation submission for **22MIS1084**. It demonstrates production-grade backend engineering, clean architecture, algorithm optimization, and comprehensive system design.

## Repository Structure

```
22MIS1084/
├── logging_middleware/              # Phase 1 & 2: Auth + Logging Middleware
│   ├── middleware.py                # FastAPI auto-logging middleware
│   └── logger/
│       ├── auth.py                  # TokenManager (register + authenticate)
│       ├── config.py                # Settings from environment variables
│       └── logger.py                # Centralized remote Log() function
│
├── vehicle_maintence_scheduler/     # Phase 3: Vehicle Maintenance Scheduler
│   └── app/
│       ├── main.py                  # FastAPI microservice entry point
│       ├── routes/scheduler_routes.py  # REST API endpoints
│       └── services/
│           └── optimization_service.py # 0/1 Knapsack DP solver
│
├── notification_app_be/             # Phase 9: Priority Inbox Microservice
│   └── app/
│       ├── main.py                  # FastAPI app (runs on port 8002)
│       ├── routes/inbox_routes.py   # REST API for priority inbox
│       └── services/
│           └── inbox_service.py     # Min-Heap Top-K Optimization Logic
│
├── notification_system_design.md    # Phase 4-8: Comprehensive System Architecture
├── auth_manager.py                  # Standalone auth runner
├── main.py                          # Phase 2 logging demo app
├── test_logger.py                   # Logger test suite
├── requirements.txt                 # Python dependencies
└── .gitignore                       # Ignores .env, venv, __pycache__, etc.
```

## Phases Completed (1-10)

- **Phase 1: Registration & Authentication** — Implemented automated secure registration, token fetching, and secure credentials management via `.env`.
- **Phase 2: Remote Logging Middleware** — Developed a strictly validated observability layer enforcing the 48-character limit, automatically logging backend actions.
- **Phase 3: Vehicle Maintenance Scheduler** — Implemented a **0/1 Knapsack Dynamic Programming** algorithm to dynamically fetch data, optimize task selection based on mechanic capacities, and maximize impact.
- **Phase 4-8: Notification System Architecture** — Designed a massive-scale system (`notification_system_design.md`) including REST APIs, real-time push (WebSocket/PubSub), PostgreSQL DB design, slow query analysis with composite indexing, high-scale caching strategies, and reliable Celery/RabbitMQ async queue processing.
- **Phase 9: Priority Inbox Implementation** — Developed a working backend service fetching real-time notifications, ranking them, and efficiently returning the Top-10.
- **Phase 10: Final Engineering Polish** — Validated clean git history, integrated logging middleware across all microservices, and handled exceptions robustly.
## Screenshots
<img width="1145" height="732" alt="Screenshot 2026-05-16 170050" src="https://github.com/user-attachments/assets/002d5f05-d432-46e7-8d79-3275996c1acb" />
<img width="1089" height="833" alt="Screenshot 2026-05-16 170128" src="https://github.com/user-attachments/assets/f1ef5400-32f1-46ef-92bb-71203a657412" />
<img width="1248" height="964" alt="Screenshot 2026-05-16 174022" src="https://github.com/user-attachments/assets/c40d67d5-eae6-46a9-b237-99520e9b0e5b" />
<img width="1252" height="975" alt="Screenshot 2026-05-16 174033" src="https://github.com/user-attachments/assets/14e4f735-f5ff-4a99-a4ec-e6b90fb3e4ed" />

## Algorithm Details

### Vehicle Scheduler (0/1 Knapsack)
Maximizes operational impact within mechanic-hour constraints per depot.
- **Duration** = Weight | **Impact** = Value | **MechanicHours** = Capacity
- **Time Complexity:** O(N * W) | **Space Complexity:** O(N * W)

### Priority Inbox (Top-K Min-Heap)
Fetches notifications and ranks them based on `Type` weight (`Placement` > `Result` > `Event`) combined with a recency decay factor. 
- Utilizes a **Min-Heap (Priority Queue)** of size K (10) to efficiently keep track of the highest scored notifications in **O(N log K)** time rather than O(N log N) sorting.

## Quick Start & Execution

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Vehicle Scheduler Service (Phase 3)
# Runs on http://127.0.0.1:8001
python -m vehicle_maintence_scheduler.app.main

# 3. Start Priority Inbox Service (Phase 9)
# Runs on http://127.0.0.1:8002
python -m notification_app_be.app.main
```

## API Endpoints

### Vehicle Scheduler (Port 8001)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/schedule/{depot_id}` | Optimal schedule for a specific depot |
| GET | `/schedule/all` | Optimal schedules for all depots |

### Priority Inbox (Port 8002)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inbox/top?limit=10` | Returns the Top-10 prioritized unread notifications |

## Proof of Execution (Screenshots)
Screenshots showing successful Postman API executions, optimized JSON responses, and token authentications have been captured during execution and demonstrate full functional compliance.
