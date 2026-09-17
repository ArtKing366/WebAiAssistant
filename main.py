import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
import redis

app = FastAPI(title="AI Web Assistant")

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

STATIC_DIR = Path(__file__).parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


class ChatRequest(BaseModel):
    session_id: str
    text:str


@app.get("/")
def get_response():
    return FileResponse(STATIC_DIR / "index.html")



@app.post("/chat")
def post_response(request: ChatRequest):
    return {"reply": f"You wrote: {request.text}"}
    

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)





