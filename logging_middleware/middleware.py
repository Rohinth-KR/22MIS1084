import time
import asyncio
import logging
import requests
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Import the newly created modules to adhere to the checklist structure
from .logger.config import settings
from .logger.auth import TokenManager

logger = logging.getLogger("LoggingMiddleware")

class RemoteLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.token_manager = TokenManager()

    def _send_log(self, log_data: dict):
        """
        Synchronous function to send logs to the evaluation server.
        Runs in a separate thread to avoid blocking the main FastAPI event loop.
        """
        token = self.token_manager.get_valid_token()
        if not token:
            logger.warning("No ACCESS_TOKEN available. Logging middleware cannot authenticate with evaluation server.")
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(settings.LOGGING_API_URL, json=log_data, headers=headers, timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send remote log: {e}")
            if e.response is not None:
                logger.error(f"Server responded with: {e.response.text}")

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            log_data = {
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2)
            }
            
            # Send log asynchronously
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, self._send_log, log_data)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            log_data = {
                "method": request.method,
                "url": str(request.url),
                "status_code": 500,
                "process_time_ms": round(process_time * 1000, 2),
                "error": str(e)
            }
            
            # Send log asynchronously before bubbling up the error
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, self._send_log, log_data)
            
            raise e
