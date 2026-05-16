import requests
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..services.inbox_service import PriorityInboxService
from ..models.schemas import PriorityNotification, NotificationResponse
from logging_middleware.logger.auth import TokenManager
from logging_middleware.logger.config import settings
from logging_middleware.logger.logger import Log

router = APIRouter(prefix="/inbox", tags=["Priority Inbox"])
inbox_service = PriorityInboxService()
token_manager = TokenManager()

def get_notifications_from_api() -> NotificationResponse:
    token = token_manager.get_valid_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{settings.EVALUATION_BASE_URL}/evaluation-service/notifications"
    
    Log("backend", "info", "utils", "Fetching notifs from EVAL API")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        Log("backend", "warn", "utils", "Token expired, refreshing for notifs")
        token = token_manager.authenticate()
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        
    if response.status_code != 200:
        Log("backend", "error", "utils", f"Notif API failed: {response.status_code}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications from external API")
        
    data = response.json()
    return NotificationResponse(**data)

@router.get("/top", response_model=List[PriorityNotification])
def get_top_notifications(limit: int = 10):
    """
    Fetches all notifications and returns the top K prioritized ones.
    Priority: Placement > Result > Event (with recency tie-breaking).
    """
    try:
        Log("backend", "info", "controller", f"Fetching top {limit} notifications")
        response_data = get_notifications_from_api()
        
        # Rank them
        top_k = inbox_service.get_top_notifications(response_data.notifications, top_k=limit)
        
        Log("backend", "info", "controller", f"Successfully ranked notifs")
        return top_k
        
    except Exception as e:
        Log("backend", "error", "controller", "Failed to rank notifs")
        raise HTTPException(status_code=500, detail=str(e))
