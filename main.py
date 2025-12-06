from fastapi import FastAPI, Depends, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException
from fastapi import Body
from pydantic import BaseModel
from typing import List, Optional
import auth
import tracks


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class LoginRequest(BaseModel):
    idToken: str

class SignupRequest(BaseModel):
    idToken: str
    name: str

class CreateTrackRequest(BaseModel):
    trackName: str
    description: str
    mediaUrls: Optional[List[str]] = []

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

@app.get("/tracklist")
def read_tracklist():
    return FileResponse("static/tracklist.html")

@app.get("/trackedit")
def read_trackedit():
    return FileResponse("static/trackedit.html")

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
    
    result = auth.verify_token(token)
    if not result['success']:
        raise HTTPException(status_code=401, detail="Invalid token")

    learner_id = result['uid']
    
    # Get enrolled track IDs
    enrolled_tracks = tracks.get_learner_tracks(learner_id)
    
    # Fetch full track details for each enrolled track
    track_details = []
    for t in enrolled_tracks:
        track_info = tracks.get_track_by_id(t['trackId'])
        if track_info:
            track_details.append({
                "track_id": track_info.get("trackId"),
                "track_name": track_info.get("track_name"),
                "image_path": track_info.get("image_path"),
                "progress": t.get("progress", 0)
            })

    return track_details

@app.delete("/api/user/tracks/{track_id}")
async def remove_track(track_id: str, request: Request):
    """Remove a track from user's enrolled tracks"""
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = auth.verify_token(token)
        if result['success']:
            uid = result['uid']
            
            #  Implement the actual removal logic in your auth.py or tracks.py
            auth.remove_user_track(uid, track_id)
            
            return {"success": True, "message": "Track removed"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/expert")
async def get_expert_info(request: Request):
    """Get current expert's information"""
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = auth.verify_token(token)
        
        if result['success']:
            uid = result['uid']
            user_data = auth.get_user_data(uid)

            print(f"User data from Firestore: {user_data}")
            
            if not user_data:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "success": True,
                "name": user_data.get('name'),
                "email": user_data.get('email'),
                "type": user_data.get('type')
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expert/tracks")
async def get_expert_tracks(request: Request):
    """Get user's tracks"""
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = auth.verify_token(token)
        if result['success']:
            uid = result['uid']
            user_data = auth.get_user_data(uid)
            
            if user_data:
                # For expert, get Tracks
                tracks = user_data.get('tracks', [])
                return {"success": True, "tracks": tracks}
            else:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@app.post("/api/expert/tracks")
async def add_expert_track(track_data: CreateTrackRequest, request: Request):
    """Expert creates a new track"""
    token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = auth.verify_token(token)
        
        if result['success']:
            uid = result['uid']
            
            user_data = auth.get_user_data(uid)
            if user_data.get('type') != 'expert':
                raise HTTPException(status_code=403, detail="Only experts can create tracks")
            
            # Create the track
            track_result = tracks.create_track(
                uid, 
                track_data.trackName, 
                track_data.description, 
                track_data.mediaUrls
            )
            
            if track_result['success']:
                return {
                    "success": True, 
                    "trackId": track_result['trackId'],
                    "message": "Track created successfully"
                }
            else:
                raise HTTPException(status_code=500, detail=track_result.get('error', 'Failed to create track'))
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/api/expert/tracks/{track_id}")
async def delete_track(track_id: str, request: Request):
    """Delete a track"""
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        result = auth.verify_token(token)
        
        if result['success']:
            uid = result['uid']
            
            # Delete the track
            delete_result = tracks.delete_track(uid, track_id)
            
            if delete_result['success']:
                return {"success": True, "message": "Track deleted"}
            else:
                raise HTTPException(status_code=500, detail=delete_result.get('error'))
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
# get all tracks
@app.get("/api/tracks")
async def api_get_all_tracks():
    all_tracks = tracks.get_all_tracks()
    return {"tracks": all_tracks}

# learner's enrolled tracks
@app.get("/api/user/enrollments")
async def api_get_user_enrollments(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = auth.verify_token(token)
    if not result['success']:
        raise HTTPException(status_code=401, detail="Invalid token")

    uid = result['uid']
    enrolled_tracks = tracks.get_learner_tracks(uid)
    return {"enrolledTracks": enrolled_tracks}

@app.post("/api/user/enrollments")
async def api_enroll_in_track(request: Request, payload: dict = Body(...)):
    """Enroll learner in a track"""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify token
    result = auth.verify_token(token)
    if not result['success']:
        raise HTTPException(status_code=401, detail="Invalid token")

    learner_id = result['uid']
    track_id = payload.get("trackId")
    expert_id = payload.get("expertId")

    if not track_id or not expert_id:
        raise HTTPException(status_code=400, detail="trackId and expertId required")

    # Call tracks.py function
    res = tracks.enroll_in_track(learner_id, track_id, expert_id)
    if not res['success']:
        raise HTTPException(status_code=400, detail=res['error'])

    return res

# get track to edit in trackedit
@app.get("/api/expert/tracks/{track_id}")
def get_track(track_id: str):
    track = tracks.get_track_by_id(track_id)  
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track
