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

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
HISTORY_TTL = 3600
SYSTEM_PROMPT = (
    "Ты ассистент для изучения английского языка. "
    "Объясняй слова и грамматику просто, давай перевод и примеры предложений. "
    "Отвечай на языке пользователя, если он пишет по-русски."
)

app = FastAPI(title="AI Web Assistant")
client = OpenAI(api_key=OPENAI_API_KEY)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    session_id: str
    text: str


def history_key(session_id: str) -> str:
    return f"chat:{session_id}"


def get_history(session_id: str) -> list[dict]:
    raw = redis_client.get(history_key(session_id))
    if not raw:
        return []
    return json.loads(raw)


def save_history(session_id: str, history: list[dict]) -> None:
    redis_client.setex(history_key(session_id), HISTORY_TTL, json.dumps(history))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat")
def chat(payload: ChatRequest) -> dict:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    history = get_history(payload.session_id)
    history.append({"role": "user", "content": text})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {exc}") from exc

    reply = response.choices[0].message.content or ""
    history.append({"role": "assistant", "content": reply})
    save_history(payload.session_id, history)
    return {"reply": reply}


@app.delete("/chat/{session_id}")
def clear_chat(session_id: str) -> dict:
    redis_client.delete(history_key(session_id))
    return {"status": "cleared"}
