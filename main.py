from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

   
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class Tick(BaseModel):
    tick: int

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/user_dashboard")
def read_root():
    return FileResponse("static/user_dashboard.html")


@app.post("/")
def process(tick: Tick):
    return {"message": f"This is processed tick: {tick.tick}"}