from fastapi import FastAPI
import uvicorn
from .routes.inbox_routes import router as inbox_router
from logging_middleware.middleware import RemoteLoggingMiddleware

app = FastAPI(title="Notification Priority Inbox", version="1.0.0")

# Add the centralized remote logging middleware
app.add_middleware(RemoteLoggingMiddleware)

# Include the inbox router
app.include_router(inbox_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "priority-inbox"}

if __name__ == "__main__":
    uvicorn.run("notification_app_be.app.main:app", host="127.0.0.1", port=8002, reload=True)
