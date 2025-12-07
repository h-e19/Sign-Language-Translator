from fastapi import FastAPI, Depends, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException
from fastapi import Body
from pydantic import BaseModel
from fastapi import UploadFile, File, Form, HTTPException, Request

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
    phoneNumber: Optional[str] = None

class PhoneLoginRequest(BaseModel):
    idToken: str
    name: Optional[str] = None  # Only needed for first-time signup

class CreateTrackRequest(BaseModel):
    trackName: str
    description: str
    image_path: Optional[str]
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

@app.get("/verify-email")
def read_verify_email():
    return FileResponse("static/verify-email.html")

@app.get("/tracklist")
def read_tracklist():
    return FileResponse("static/tracklist.html")

@app.get("/trackopen")
def read_trackedit():
    return FileResponse("static/trackopen.html")

@app.post("/api/login/learner")
async def login_learner(request: LoginRequest, response: Response):
    """Login for learners only"""
    try:
        result = auth.verify_token(request.idToken)

        if result['success']:
            uid = result['uid']

            # Check email verification status
            verification_status = auth.check_email_verified(uid)
            if verification_status['success'] and not verification_status['emailVerified']:
                return {
                    "success": False,
                    "error": "Please verify your email before logging in",
                    "requiresEmailVerification": True
                }

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

            # Check email verification status
            verification_status = auth.check_email_verified(uid)
            if verification_status['success'] and not verification_status['emailVerified']:
                return {
                    "success": False,
                    "error": "Please verify your email before logging in",
                    "requiresEmailVerification": True
                }

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
async def signup_learner(request: SignupRequest):
    """Create learner Firestore document"""
    try:
        # Verify token first
        result = auth.verify_token(request.idToken)

        if result['success']:
            uid = result['uid']

            # Create Firestore document with phone number
            create_result = auth.create_learner_doc(uid, request.name, request.phoneNumber)

            if not create_result['success']:
                raise HTTPException(status_code=400, detail=create_result['error'])

            # Send verification email (Firebase handles this automatically)
            # The email verification link is sent when user signs up with email/password

            # Don't set session cookie yet - wait for email verification
            # Return success with flag to show verification page
            return {
                "success": True,
                "requiresEmailVerification": True,
                "message": "Please check your email to verify your account"
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/signup/expert")
async def signup_expert(request: SignupRequest):
    """Create expert Firestore document"""
    try:
        result = auth.verify_token(request.idToken)

        if result['success']:
            uid = result['uid']

            # Create Firestore document with phone number
            create_result = auth.create_expert_doc(uid, request.name, request.phoneNumber)

            if not create_result['success']:
                raise HTTPException(status_code=400, detail=create_result['error'])

            # Send verification email (Firebase handles this automatically)
            # The email verification link is sent when user signs up with email/password

            # Don't set session cookie yet - wait for email verification
            # Return success with flag to show verification page
            return {
                "success": True,
                "requiresEmailVerification": True,
                "message": "Please check your email to verify your account"
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/login/phone")
async def login_phone(request: PhoneLoginRequest, response: Response):
    """Phone number login - works for both learners and experts"""
    try:
        result = auth.verify_token(request.idToken)

        if result['success']:
            uid = result['uid']
            user_data = auth.get_user_data(uid)

            # Get phone number from Firebase Auth user
            firebase_user = auth.auth.get_user(uid)
            phone_number = firebase_user.phone_number

            # If user doesn't exist in Firestore with this Firebase Auth UID
            if not user_data:
                # Check if an existing user already has this phone number
                existing_user = auth.find_user_by_phone(phone_number)

                if existing_user:
                    # User exists with this phone number but different Firebase Auth UID
                    # This happens when they signed up with email and now logging in with phone
                    existing_uid = existing_user.get('uid')

                    # Create a new Firestore document for the phone auth UID
                    # that points to the same user data
                    user_ref = auth.db.collection('users').document(uid)
                    user_ref.set({
                        'type': existing_user.get('type'),
                        'name': existing_user.get('name'),
                        'email': existing_user.get('email'),
                        'phoneNumber': phone_number,
                        'authMethod': 'phone',
                        'originalUid': existing_uid,  # Reference to original account
                        'enrolledTracks': existing_user.get('enrolledTracks', []),
                        'tracks': existing_user.get('tracks', []),
                        'createdAt': existing_user.get('createdAt')
                    })

                    # Also update the original user document
                    link_result = auth.link_phone_to_existing_user(existing_uid, phone_number)
                    if not link_result['success']:
                        raise HTTPException(status_code=400, detail=link_result['error'])

                    # Get the newly created user data
                    user_data = auth.get_user_data(uid)

                else:
                    # No existing user with this phone number - new user
                    if not request.name:
                        return {"success": False, "error": "Name required for first-time login", "requiresName": True}

                    # For phone auth, default to learner
                    user_type = "learner"

                    create_result = auth.create_user_doc_phone(uid, request.name, user_type, phone_number)

                    if not create_result['success']:
                        raise HTTPException(status_code=400, detail=create_result['error'])

                    user_data = auth.get_user_data(uid)

            # Set session cookie with the phone auth ID token
            response.set_cookie(
                key="session_token",
                value=request.idToken,
                httponly=True,
                max_age=3600
            )

            return {"success": True, "userType": user_data.get('type')}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
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
                expert_id=uid,
                track_name=track_data.trackName,
                description=track_data.description,
                image_path=track_data.image_path,
                media_urls=track_data.mediaUrls
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

from auth import db

from cloudinary_config import cloudinary
from cloudinary.uploader import upload as cloudinary_upload
import shutil
import os,tempfile

@app.post("/api/expert/tracks/{track_id}/content")
async def upload_track_content(track_id: str, request: Request, file: UploadFile, name: str = Form(...)):
    
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = auth.verify_token(token)
    if not result['success']:
        raise HTTPException(status_code=401, detail="Invalid token")
    expert_uid = result['uid']

    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        with open(tmp.name, "wb") as f:
            shutil.copyfileobj(file.file, f)

        upload_result = cloudinary_upload(
            tmp.name,
            resource_type="video",
            folder=f"tracks/{expert_uid}/{track_id}/"
        )
        video_url = upload_result.get("secure_url")
        if not video_url:
            raise HTTPException(status_code=500, detail="Upload failed")

        media_obj = {"name": name, "url": video_url}
        res = tracks.append_media_to_track(expert_uid, track_id, media_obj)
        if not res.get("success"):
            raise HTTPException(status_code=500, detail=res.get("error", "Failed to update track"))

        return {"success": True, "url": video_url, "name": name}
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        
@app.put("/api/expert/tracks/{track_id}")
async def update_track(track_id: str, data: dict = Body(...), request: Request = None):
    token = request.cookies.get("session_token") if request else None
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = auth.verify_token(token)
    if not result['success']:
        raise HTTPException(status_code=401, detail="Invalid token")
    expert_uid = result['uid']

    res = tracks.update_track_metadata(expert_uid, track_id, data)
    if not res['success']:
        raise HTTPException(status_code=400, detail=res.get('error', 'Failed to update'))
    return {"success": True}
