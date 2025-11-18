import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

#Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)

security = HTTPBearer()

async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Firebase ID token from Authorization header"""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")

async def get_current_user(request: Request):
    """Get current user from cookie token"""
    token = request.cookies.get("firebase_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_current_expert(request: Request):
    """Get current expert from cookie token"""
    token = request.cookies.get("firebase_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
