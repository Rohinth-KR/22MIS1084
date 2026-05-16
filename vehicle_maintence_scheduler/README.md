# Vehicle Maintenance Scheduler Microservice

A production-grade FastAPI microservice that solves the optimal vehicle maintenance scheduling problem using **0/1 Knapsack Dynamic Programming**.

## Architecture

```
vehicle_maintence_scheduler/
├── app/
│   ├── main.py                          # FastAPI entry point
│   ├── config.py                        # Environment configuration
│   ├── models/
│   │   └── schemas.py                   # Pydantic data models
│   ├── routes/
│   │   └── scheduler_routes.py          # REST API endpoints
│   ├── services/
│   │   ├── depot_service.py             # Depot data fetching
│   │   ├── vehicle_service.py           # Vehicle task fetching
│   │   └── optimization_service.py      # 0/1 Knapsack DP solver
│   └── utils/
│       └── api_client.py                # Authenticated HTTP client
└── README.md
```

## Algorithm

**0/1 Knapsack Dynamic Programming**
- Duration = Weight (hours per task)
- Impact = Value (operational importance)
- MechanicHours = Capacity (depot constraint)

Time Complexity: O(n * W) | Space Complexity: O(n * W)

## Usage

```bash
cd 22MIS1084
python -m vehicle_maintence_scheduler.app.main
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Service health check |
| GET | /depots | List all depots |
| GET | /vehicles | List all vehicle tasks |
| GET | /schedule/{depot_id} | Optimal schedule for a depot |
| GET | /schedule/all | Optimal schedules for all depots |
