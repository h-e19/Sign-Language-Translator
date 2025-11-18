from fastapi import FastAPI, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException
from pydantic import BaseModel
from auth import get_current_user
from auth import get_current_expert



app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class Tick(BaseModel):
    tick: int 

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/user_dashboard")
async def read_dashboard(request: Request):
    # Verify user is authenticated via cookie
    try:
        user = await get_current_user(request)
        return FileResponse("static/user_dashboard.html")
    except:
        return RedirectResponse(url="/login", status_code=302)


@app.get("/expert_dashboard")
async def read_expert_dashboard(request: Request):
    try:
        user = await get_current_expert(request)
        return FileResponse("static/expert_dashboard.html")
    except:
        return RedirectResponse(url="/login", status_code=302)


@app.get("/login")
def read_login():
    return FileResponse("static/login.html")

@app.get("/signup")
def read_signup():
    return FileResponse("static/signup.html")

@app.get("/forgotpassword")
def read_forgotpassword():
    return FileResponse("static/forgotpassword.html")

@app.post("/")
def process(tick: Tick):
    return {"message": f"This is processed tick: {tick.tick}"}

#### API ENDPOINT ####
@app.get("/api/user")
async def get_user_info(request: Request):
    # return current user info
    try:
        user = await get_current_user(request)

        return {
            "user_name": user.get("name", "Unkown"),
            "user_email": user.get("email", "No email")
        }
    except Exception as e:
        return {"error": "Failed to get user info"}, 401
    
@app.get("/api/user/tracks")
async def get_user_tracks(request: Request):
    """
    Returns the current user's enrolled tracks
    """
    try:
        user = await get_current_user(request)
        
        # TODO: Replace this with actual database query
        # For now, returning dummy data
        
        user_tracks = [
            {"track_id": 1, "track_name": "Alphabets", "progress": 10, "image_path": "static/images/placeholder1.png"},
            {"track_id": 2, "track_name": "Foods", "progress": 25, "image_path": "static/images/placeholder1.png"},
            {"track_id": 3, "track_name": "Sports", "progress": 50, "image_path": "static/images/placeholder1.png"}
        ]
        
        return user_tracks
        
    except Exception as e:
        return {"error": "Failed to get tracks"}, 401
    
@app.delete("/api/user/tracks/{track_id}")
async def delete_user_track(request: Request, track_id: int):
    try:
        user = await get_current_user(request)

        #TODO: Delete from Tracks_Enrolled
        #something like DELETE FROM TRACKS_ENROLLED
        #               WHERE LEARNER_ID = USER_ID AND TRACK_ID = track_id

        #right now just do this
        return {"message": f"Successfully removed track {track_id}"}
    
    except Exception as e:
        raise HTTPException(status_code=401, detail="Failed to remove track")

@app.get("/api/expert")
async def get_expert_info(request: Request):
    # return current expert info
    try:
        expert = await get_current_expert(request)

        return {
            "user_name": expert.get("name", "Unkown"),
            "user_email": expert.get("email", "No email")
        }
    except Exception as e:
        return {"error": "Failed to get expert info"}, 401
    
@app.get("/api/expert/tracks")
async def get_expert_tracks(request: Request):
    """
    Returns the current expert's uploaded tracks
    """
    try:
        expert = await get_current_expert(request)
        
        #TODO: Replace this with actual database query
        #For now, returning dummy data
        
        expert_tracks = [
            {"track_id": 1, "track_name": "Planets", "image_path": "static/images/placeholder1.png"},
            {"track_id": 2, "track_name": "Books", "image_path": "static/images/placeholder1.png"},
            {"track_id": 3, "track_name": "Animals", "image_path": "static/images/placeholder1.png"},
            {"track_id": 4, "track_name": "Colors", "image_path": "static/images/placeholder1.png"}
        
        ]
        
        return expert_tracks
        
    except Exception as e:
        return {"error": "Failed to get tracks"}, 401
    
@app.delete("/api/expert/tracks/{track_id}")
async def delete_expert_track(request: Request, track_id: int):
    try:
        expert = await get_current_expert(request)

        #TODO: Delete from Tracks_Enrolled
        #something like DELETE FROM TRACKS_ENROLLED
        #               WHERE LEARNER_ID = USER_ID AND TRACK_ID = track_id

        #right now just do this
        return {"message": f"Successfully removed track {track_id}"}
    
    except Exception as e:
        raise HTTPException(status_code=401, detail="Failed to remove track")
    