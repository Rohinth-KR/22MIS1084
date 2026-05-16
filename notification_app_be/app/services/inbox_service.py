import heapq
from datetime import datetime
from typing import List
from ..models.schemas import NotificationItem, PriorityNotification

class PriorityInboxService:
    def __init__(self):
        # Weights according to requirement: Placement > Result > Event
        self.type_weights = {
            "Placement": 100.0,
            "Result": 50.0,
            "Event": 10.0
        }

    def _calculate_score(self, item: NotificationItem) -> float:
        """
        Calculates a priority score based on Type weight + Time decay.
        Score = Base Weight + (Time weight)
        Newer notifications get a slight boost within their category.
        """
        base_weight = self.type_weights.get(item.Type, 0.0)
        
        try:
            # Parse timestamp to datetime
            dt = datetime.strptime(item.Timestamp, "%Y-%m-%d %H:%M:%S")
            # Convert to a relative timestamp boost (newer = higher score)
            # Using timestamp float, normalized somewhat so it doesn't overpower the base weight
            # Boost range: roughly 0 to 1 based on recent time differences
            current_ts = datetime.utcnow().timestamp()
            item_ts = dt.timestamp()
            
            # Simple decay: penalize older items by taking (item_ts / 1e10)
            # This ensures items of the SAME type are ordered by time,
            # but the time boost is small enough (< 1.0) that it NEVER overrides the base_weight difference (e.g. 50 vs 100)
            time_boost = item_ts / 1e10
            
            return base_weight + time_boost
        except ValueError:
            return base_weight

    def get_top_notifications(self, notifications: List[NotificationItem], top_k: int = 10) -> List[PriorityNotification]:
        """
        Uses a Min-Heap to find the Top-K notifications efficiently in O(N log K) time.
        """
        # Min-heap stores tuples of (score, tie_breaker, notification)
        # We want to keep the top K, so we maintain a min-heap of size K.
        # If we see an item with a higher score than the heap's minimum, we push and pop.
        
        heap = []
        
        for idx, item in enumerate(notifications):
            score = self._calculate_score(item)
            dt = datetime.strptime(item.Timestamp, "%Y-%m-%d %H:%M:%S")
            
            # Heap stores: (score, idx (tie breaker), Notification object)
            entry = (score, idx, item, dt)
            
            if len(heap) < top_k:
                heapq.heappush(heap, entry)
            else:
                # Only push if the current score is higher than the lowest score in the heap
                if score > heap[0][0]:
                    heapq.heappushpop(heap, entry)
                    
        # Extract from heap and sort descending by score
        # Heap elements are ordered from lowest score to highest, so we sort reversed.
        top_items = sorted(heap, key=lambda x: x[0], reverse=True)
        
        result = []
        for score, _, item, dt in top_items:
            result.append(PriorityNotification(
                id=item.ID,
                type=item.Type,
                message=item.Message,
                timestamp=dt,
                priority_score=round(score, 6)
            ))
            
        return result
