"""
Smart CLI Chatbot — API version
Wraps the persona/session logic from chatbot.py behind a FastAPI HTTP API
so it can be hosted on Render and called remotely (e.g. from PowerShell).
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------- Config ----------------------

HF_TOKEN = os.getenv("HF_TOKEN")
API_KEY = os.getenv("API_KEY")  # optional shared-secret to protect your endpoint
MODEL = "auto"
CONTEXT_LIMIT = 10000

client = OpenAI(
    base_url="https://freellmapi-seyc.onrender.com/v1",
    api_key=HF_TOKEN,
)

PERSONAS = {
    "professional": (
        "You are a professional assistant. "
        "Be concise, formal, and precise. "
        "Avoid casual language. Get straight to the point."
    ),
    "casual": (
        "You are a chill, friendly buddy. "
        "Use casual language, be warm and fun. "
        "Use short sentences. Occasionally use 'lol', 'btw', 'tbh'."
    ),
    "socratic": (
        "You are a Socratic tutor. Never give direct answers. "
        "Instead, ask guiding questions that help the user "
        "arrive at the answer themselves. "
        "Be patient and encouraging."
    ),
}

# ---------------------- In-memory session store ----------------------
# NOTE: this resets whenever the Render instance restarts / spins down
# (expected on the free tier). Fine for a personal tool; swap for
# Postgres later if you need history to survive restarts.

SESSIONS: dict[str, dict] = {}


def new_session(persona_key: str = "professional", custom_prompt: Optional[str] = None) -> str:
    session_id = str(uuid.uuid4())
    system_prompt = custom_prompt if custom_prompt else PERSONAS.get(persona_key, PERSONAS["professional"])
    SESSIONS[session_id] = {
        "persona": persona_key if not custom_prompt else "custom",
        "messages": [{"role": "system", "content": system_prompt}],
        "input_tokens": 0,
        "output_tokens": 0,
        "created_at": datetime.now().isoformat(),
    }
    return session_id


def estimate_tokens(messages: list) -> int:
    total_chars = sum(len(m["content"]) for m in messages)
    return total_chars // 4


# ---------------------- API models ----------------------

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None       # omit to start a new session
    persona: Optional[str] = "professional"  # professional | casual | socratic
    custom_prompt: Optional[str] = None      # overrides persona if set (new sessions only)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    persona: str
    context_pct: float
    total_input_tokens: int
    total_output_tokens: int


# ---------------------- App ----------------------

app = FastAPI(title="Smart CLI Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_auth(x_api_key: Optional[str]):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


@app.get("/", response_class=PlainTextResponse)
def root():
    import platform

    text = f"""Smart CLI Chatbot API is running

Example PowerShell usage:
$body = @{{ message = "Hello, testing" }} | ConvertTo-Json
Invoke-RestMethod -Uri "https://llm-chatbot-yb0c.onrender.com/chat" -Method Post -ContentType "application/json" -Body $body

System:
OS: {platform.system()}
OS Version: {platform.release()}
Platform: {platform.platform()}
Python Version: {platform.python_version()}

Personas: {", ".join(PERSONAS.keys())}
"""
    return text


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL, "active_sessions": len(SESSIONS)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_api_key: Optional[str] = Header(default=None)):
    check_auth(x_api_key)

    if not HF_TOKEN:
        raise HTTPException(status_code=500, detail="HF_TOKEN not configured on the server")

    # Get or create session
    if req.session_id and req.session_id in SESSIONS:
        session = SESSIONS[req.session_id]
        session_id = req.session_id
    else:
        session_id = new_session(req.persona or "professional", req.custom_prompt)
        session = SESSIONS[session_id]

    messages = session["messages"]
    messages.append({"role": "user", "content": req.message})

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            messages=messages,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream model error: {e}")

    reply = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    if completion.usage:
        session["input_tokens"] += completion.usage.prompt_tokens
        session["output_tokens"] += completion.usage.completion_tokens

    ctx_used = estimate_tokens(messages)

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        persona=session["persona"],
        context_pct=round((ctx_used / CONTEXT_LIMIT) * 100, 1),
        total_input_tokens=session["input_tokens"],
        total_output_tokens=session["output_tokens"],
    )


@app.get("/session/{session_id}")
def get_session(session_id: str, x_api_key: Optional[str] = Header(default=None)):
    check_auth(x_api_key)
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/session/{session_id}")
def delete_session(session_id: str, x_api_key: Optional[str] = Header(default=None)):
    check_auth(x_api_key)
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        return {"deleted": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))