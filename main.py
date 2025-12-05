from fastapi import FastAPI, Depends, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException
from pydantic import BaseModel
import auth
import tracks


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class LoginRequest(BaseModel):
    idToken: str

class SignupRequest(BaseModel):
    idToken: str
    name: str

@app.get("/")
def read_root():
    return FileResponse("static/landing.html")

@app.get("/login/learner")
def read_login_learner():
    return FileResponse("static/login_learner.html")

@app.get("/login/expert")
def read_login_expert():
    return FileResponse("static/login_expert.html")

@app.get("/signup/learner")  # FIXED: was "leaner"
def read_signup_learner():
    return FileResponse("static/signup_learner.html")

@app.get("/signup/expert")
def read_signup_expert():
    return FileResponse("static/signup_expert.html")

@app.get("/forgotpassword")
def read_forgotpassword():
    return FileResponse("static/forgotpassword.html")

@app.post("/api/login/learner")
async def login_learner(request: LoginRequest, response: Response):
    """Login for learners only"""
    try:
        result = auth.verify_token(request.idToken)
        
        if result['success']:
            uid = result['uid']
            user_data = auth.get_user_data(uid)
            
            # CHECK if they're actually a learner
            if user_data.get('type') != 'learner':
                return {"success": False, "error": "Invalid account type. Please use expert login."}
            
            response.set_cookie(
                key="session_token",
                value=request.idToken,
                httponly=True,
                max_age=3600
            )
            
            return {"success": True, "userType": "learner"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/login/expert")
async def login_expert(request: LoginRequest, response: Response):
    """Login for experts only"""
    try:
        result = auth.verify_token(request.idToken)
        
        if result['success']:
            uid = result['uid']
            user_data = auth.get_user_data(uid)
            
            # CHECK if they're actually an expert
            if user_data.get('type') != 'expert':
                return {"success": False, "error": "Invalid account type. Please use learner login."}
            
            response.set_cookie(
                key="session_token",
                value=request.idToken,
                httponly=True,
                max_age=3600
            )
            
            return {"success": True, "userType": "expert"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@app.post("/api/signup/learner")
async def signup_learner(request: SignupRequest, response: Response):
    """Create learner Firestore document"""
    try:
        # Verify token first
        result = auth.verify_token(request.idToken)
        
        if result['success']:
            uid = result['uid']
            
            # Create Firestore document
            auth.create_learner_doc(uid, request.name)
            
            response.set_cookie(
                key="session_token",
                value=request.idToken,
                httponly=True,
                max_age=3600
            )
            
            return {"success": True}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/signup/expert")
async def signup_expert(request: SignupRequest, response: Response):
    """Create expert Firestore document"""
    try:
        result = auth.verify_token(request.idToken)
        
        if result['success']:
            uid = result['uid']
            auth.create_expert_doc(uid, request.name)
            
            response.set_cookie(
                key="session_token",
                value=request.idToken,
                httponly=True,
                max_age=3600
            )
            
            return {"success": True}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        return {"success": False, "error": str(e)}

# Protected routes - ONLY ONE DEFINITION EACH
@app.get("/user_dashboard")
async def user_dashboard(request: Request):
    """Learner dashboard"""
    token = request.cookies.get("session_token")
    
    if not token:
        return RedirectResponse(url="/login/learner", status_code=302)  # FIXED: was /login/user
    
    try:
        result = auth.verify_token(token)
        if result['success']:
            return FileResponse("static/user_dashboard.html")
        else:
            return RedirectResponse(url="/login/learner", status_code=302)  # FIXED
    except:
        return RedirectResponse(url="/login/learner", status_code=302)  # FIXED

@app.get("/expert_dashboard")
async def expert_dashboard(request: Request):
    """Expert dashboard"""
    token = request.cookies.get("session_token")
    
    if not token:
        return RedirectResponse(url="/login/expert", status_code=302)
    
    try:
        result = auth.verify_token(token)
        if result['success']:
            return FileResponse("static/expert_dashboard.html")
        else:
            return RedirectResponse(url="/login/expert", status_code=302)
    except:
        return RedirectResponse(url="/login/expert", status_code=302)

@app.post("/api/logout")
async def logout(response: Response):
    """Logout user"""
    response.delete_cookie("session_token")
    return {"success": True}

@app.get("/api/user")
async def get_user(request: Request):
    """Get current user info"""
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = auth.verify_token(token)
        if result['success']:
            uid = result['uid']
            user_data = auth.get_user_data(uid)
            
            if user_data:
                return {
                    "success": True,
                    "user_email": user_data.get('email'),
                    "name": user_data.get('name'),
                    "type": user_data.get('type')
                }
            else:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/api/user/tracks")
async def get_user_tracks(request: Request):
    """Get user's enrolled tracks"""
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = auth.verify_token(token)
        if result['success']:
            uid = result['uid']
            user_data = auth.get_user_data(uid)
            
            if user_data:
                # For learners, get enrolledTracks
                track_ids = user_data.get('enrolledTracks', [])
                
                # TODO: Fetch actual track details from your tracks collection
                # For now, return empty list or mock data
                tracks = []
                
                # If you have a tracks module/function to get track details:
                # for track_id in track_ids:
                #     track_info = tracks.get_track_by_id(track_id)
                #     tracks.append(track_info)
                
                return tracks
            else:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.delete("/api/user/tracks/{track_id}")
async def remove_track(track_id: int, request: Request):
    """Remove a track from user's enrolled tracks"""
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = auth.verify_token(token)
        if result['success']:
            uid = result['uid']
            
            # TODO: Implement the actual removal logic in your auth.py or tracks.py
            # auth.remove_user_track(uid, track_id)
            
            return {"success": True, "message": "Track removed"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))