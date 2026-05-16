import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

class Settings:
    REGISTRATION_URL = "http://4.224.186.213/evaluation-service/register"
    AUTH_URL = "http://4.224.186.213/evaluation-service/auth"
    LOGGING_API_URL = "http://4.224.186.213/evaluation-service/logs"
    
    # Credentials
    EMAIL = os.getenv("EMAIL")
    NAME = os.getenv("NAME")
    MOBILE_NO = os.getenv("MOBILE_NO")
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
    ROLL_NO = os.getenv("ROLL_NO")
    ACCESS_CODE = os.getenv("ACCESS_CODE")
    
    # Generated Tokens
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

settings = Settings()
