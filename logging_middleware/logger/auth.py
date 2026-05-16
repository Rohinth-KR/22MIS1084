import os
import requests
import logging
from dotenv import set_key
from .config import settings

logger = logging.getLogger(__name__)

class TokenManager:
    """Reusable token manager to handle registration and authentication securely."""
    
    def __init__(self, env_path=".env"):
        # Default to root .env file
        self.env_path = os.path.join(os.getcwd(), env_path)

    def register(self):
        """Registers the user using the registration API."""
        payload = {
            "email": settings.EMAIL,
            "name": settings.NAME,
            "mobileNo": settings.MOBILE_NO,
            "githubUsername": settings.GITHUB_USERNAME,
            "rollNo": settings.ROLL_NO,
            "accessCode": settings.ACCESS_CODE
        }
        
        try:
            response = requests.post(settings.REGISTRATION_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            client_id = data.get("clientID")
            client_secret = data.get("clientSecret")
            
            if client_id and client_secret:
                set_key(self.env_path, "CLIENT_ID", client_id)
                set_key(self.env_path, "CLIENT_SECRET", client_secret)
                settings.CLIENT_ID = client_id
                settings.CLIENT_SECRET = client_secret
                logger.info("Successfully registered and stored client credentials.")
                return client_id, client_secret
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            
        return None, None

    def authenticate(self):
        """Authenticates using the auth API to receive Bearer access token."""
        if not settings.CLIENT_ID or not settings.CLIENT_SECRET:
            logger.error("Missing CLIENT_ID or CLIENT_SECRET for authentication.")
            return None
            
        payload = {
            "email": settings.EMAIL,
            "name": settings.NAME,
            "rollNo": settings.ROLL_NO,
            "accessCode": settings.ACCESS_CODE,
            "clientID": settings.CLIENT_ID,
            "clientSecret": settings.CLIENT_SECRET
        }
        
        try:
            response = requests.post(settings.AUTH_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            access_token = data.get("access_token") or data.get("accessToken") or data.get("token")
            if access_token:
                set_key(self.env_path, "ACCESS_TOKEN", access_token)
                settings.ACCESS_TOKEN = access_token
                logger.info("Successfully authenticated and stored access token.")
                return access_token
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            
        return None

    def get_valid_token(self):
        """Retrieves a valid token, running auth flows if necessary."""
        if settings.ACCESS_TOKEN:
            return settings.ACCESS_TOKEN
            
        if not settings.CLIENT_ID or not settings.CLIENT_SECRET:
            self.register()
            
        return self.authenticate()
