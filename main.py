from fastapi import FastAPI, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from auth import get_current_user



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