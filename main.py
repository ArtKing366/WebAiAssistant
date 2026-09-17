import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel
import redis


app = FastAPI(title="AI Web Assistant")

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.6-flash"

# Получаем ограничения модели один раз при запуске приложения
model_info = client.models.get(model=MODEL_NAME)
INPUT_TOKEN_LIMIT = model_info.input_token_limit


STATIC_DIR = Path(__file__).parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


class ChatRequest(BaseModel):
    session_id: str
    text: str


redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)


def history_key(session_id) -> str:
    return f"chat:{session_id}"


@app.get("/")
def get_response():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat")
def post_response(request: ChatRequest):
    key = history_key(request.session_id)

    raw = redis_client.get(key)

    if raw is None:
        history = []
    else:
        history = json.loads(raw)

    history.append({
        "role": "user",
        "content": request.text
    })

    gemini_history = []

    for message in history:
        gemini_history.append(
            types.Content(
                role="model" if message["role"] == "assistant" else "user",
                parts=[
                    types.Part(text=message["content"])
                ]
            )
        )

    # Считаем, сколько токенов занимает текущий input
    token_response = client.models.count_tokens(
        model=MODEL_NAME,
        contents=gemini_history
    )

    input_tokens = token_response.total_tokens

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=gemini_history
    )

    reply = response.text

    history.append({
        "role": "assistant",
        "content": reply
    })

    redis_client.setex(
        key,
        3600,
        json.dumps(history)
    )

    tokens_left = max(
        INPUT_TOKEN_LIMIT - input_tokens,
        0
    )

    return {
        "reply": reply,
        "context": {
            "used": input_tokens,
            "limit": INPUT_TOKEN_LIMIT,
            "left": tokens_left
        }
    }


@app.delete("/chat/{session_id}")
def clear_chat(session_id: str):
    key = history_key(session_id)

    redis_client.delete(key)

    return {"message": "Chat history cleared"}