import os

class Config:
    # Flask ke liye secret key (Render ke Environment Variables se aayegi)
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-secret-key-change-me")
    
    # Session filesystem par save hoga
    SESSION_TYPE = "filesystem"
    
    # Flask-Session ke liye permanent session
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
    # Upload size limit (10MB)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
