from pydantic import BaseModel
from datetime import datetime

class NotificationItem(BaseModel):
    ID: str
    Type: str
    Message: str
    Timestamp: str

class NotificationResponse(BaseModel):
    notifications: list[NotificationItem]

class PriorityNotification(BaseModel):
    id: str
    type: str
    message: str
    timestamp: datetime
    priority_score: float
