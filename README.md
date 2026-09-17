# AI Web Assistant

A lightweight AI chat application built with **FastAPI, Redis, and Google Gemini**.

**Live demo:** https://webaiassistant-production.up.railway.app

## Features

* Multi-turn AI conversations
* Session-based chat history
* Redis storage with 1-hour TTL
* Context token usage tracking
* Clear chat history
* Browser session management with `localStorage`
* Dockerized and deployed on Railway

## Tech Stack

| Technology         | Purpose              |
| ------------------ | -------------------- |
| Python 3.12        | Backend              |
| FastAPI            | Web API              |
| Google Gemini      | AI model             |
| Redis              | Conversation history |
| Pydantic           | Data validation      |
| Vanilla JavaScript | Frontend             |
| Docker             | Containerization     |
| Railway            | Deployment           |

## Architecture

```text
Browser
   ↓
FastAPI
   ├── Redis → chat history
   └── Gemini → AI response
```

## Project Structure

```text
WebAiAssistant/
├── main.py
├── static/
│   └── index.html
├── requirements.txt
├── Dockerfile
└── .env
```

## Local Setup

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
GEMINI_API_KEY=your_api_key
REDIS_URL=redis://localhost:6379
```

Run the application:

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Redis must be running locally.

## API

### `GET /`

Returns the web interface.

### `POST /chat`

Sends a message and returns the Gemini response.

```json
{
  "session_id": "uuid",
  "text": "Hello!"
}
```

### `DELETE /chat/{session_id}`

Deletes the conversation history for the specified session.

## Deployment

The application is deployed on **Railway**.

Required environment variables:

```text
GEMINI_API_KEY
REDIS_URL
```

`PORT` is provided automatically by Railway.
