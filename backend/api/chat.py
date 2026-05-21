"""
MediBot AI — Chat API Router
Handles real-time AI chat with context memory, RAG, and session management
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import logging

from core.auth import get_current_user
from core.ai_engine import ai_engine
from core.database import db_insert, db_find_many, db_update_one
from ml.disease_predictor import predict_from_text, check_emergency
from rag.rag_engine import rag_engine

router = APIRouter()
logger = logging.getLogger("medibot.chat")

# ─── Schemas ──────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for context memory")
    use_rag: bool = Field(True, description="Use RAG retrieval")


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Conversation"


class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# ─── In-memory session cache (for fast context retrieval) ─────────────────────
_session_cache: Dict[str, List[Dict]] = {}

GREETING_TRIGGERS = {"hi", "hello", "hey", "good morning", "good evening", "greetings", "howdy"}

GREETING_RESPONSE = """👋 **Hello! I'm MediBot AI** — your Advanced Healthcare Assistant.

I can help you with:
- 🔍 **Symptom analysis** and possible conditions
- 💊 **Health advice** and precautions
- 📋 **Medical information** and education
- 🚨 **Emergency guidance** when needed

**To get started**, simply describe your symptoms in natural language:
> *"I have a fever, sore throat, and body aches for 2 days"*

---
⚠️ *I am an AI assistant, not a replacement for professional medical advice. Always consult a qualified doctor for diagnosis and treatment.*"""


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/send")
async def send_message(
    body: ChatMessage,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """
    Main chat endpoint with:
    - Conversation memory (session context)
    - RAG medical knowledge retrieval
    - AI generation (Gemini/OpenAI/Groq) with rule-based fallback
    - Emergency detection
    - ML disease prediction
    """
    message = body.message.strip()
    user_id = user.get("user_id", "guest")

    # ── Greeting ──────────────────────────────────────────────────────────────
    if message.lower().rstrip("!.,?") in GREETING_TRIGGERS:
        return {
            "reply": GREETING_RESPONSE,
            "session_id": body.session_id or str(uuid.uuid4()),
            "provider": "system",
            "is_emergency": False,
            "predictions": [],
        }

    # ── Emergency check ───────────────────────────────────────────────────────
    is_emergency = check_emergency(message)

    # ── Session management ────────────────────────────────────────────────────
    session_id = body.session_id or str(uuid.uuid4())
    if session_id not in _session_cache:
        # Load from DB
        history = await db_find_many(
            "messages",
            {"session_id": session_id, "user_id": user_id},
            limit=20,
        )
        _session_cache[session_id] = [
            {"role": m["role"], "content": m["content"]}
            for m in sorted(history, key=lambda x: x.get("created_at", ""))
        ]

    conversation_history = _session_cache[session_id]

    # ── RAG retrieval ─────────────────────────────────────────────────────────
    rag_context = None
    if body.use_rag and rag_engine.available:
        rag_context = await rag_engine.retrieve(message, k=3)

    # ── Run ML prediction (in background for UX speed) ────────────────────────
    ml_result = predict_from_text(message)

    # ── Build AI messages ─────────────────────────────────────────────────────
    ai_messages = conversation_history.copy()

    # Enrich prompt with ML findings
    enriched_message = message
    if ml_result["predictions"]:
        top = ml_result["predictions"][0]
        enriched_message += (
            f"\n\n[System context for AI: ML model suggests '{top['display_name']}' "
            f"with {top['confidence']}% confidence. "
            f"Matched symptoms: {', '.join(top['matched_symptoms'])}. "
            f"Severity: {top['severity']}. Use this to inform your response.]"
        )

    if is_emergency:
        enriched_message = f"[EMERGENCY SYMPTOMS DETECTED] {message}"

    ai_messages.append({"role": "user", "content": enriched_message})

    # ── AI generation ─────────────────────────────────────────────────────────
    ai_result = await ai_engine.chat(
        messages=ai_messages,
        context=rag_context,
        temperature=0.2 if is_emergency else 0.4,
    )

    reply = ai_result["reply"]
    provider = ai_result.get("provider", "unknown")

    # ── Update context window ─────────────────────────────────────────────────
    conversation_history.append({"role": "user", "content": message})
    conversation_history.append({"role": "assistant", "content": reply})
    # Keep last 20 messages in memory
    _session_cache[session_id] = conversation_history[-20:]

    # ── Persist to DB in background ───────────────────────────────────────────
    msg_id = str(uuid.uuid4())
    background_tasks.add_task(
        _persist_messages,
        user_id=user_id,
        session_id=session_id,
        user_message=message,
        bot_reply=reply,
        provider=provider,
        msg_id=msg_id,
        ml_predictions=ml_result["predictions"][:1],
        is_emergency=is_emergency,
    )

    return {
        "reply": reply,
        "session_id": session_id,
        "message_id": msg_id,
        "provider": provider,
        "is_emergency": is_emergency,
        "predictions": ml_result["predictions"][:3],
        "extracted_symptoms": ml_result.get("extracted_symptoms", []),
        "rag_used": rag_context is not None,
    }


@router.get("/sessions")
async def list_sessions(user: dict = Depends(get_current_user)):
    """Get all chat sessions for the current user."""
    user_id = user.get("user_id", "guest")
    sessions = await db_find_many("sessions", {"user_id": user_id}, limit=50)
    return {"sessions": sessions}


@router.post("/sessions")
async def create_session(
    body: SessionCreateRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new chat session."""
    user_id = user.get("user_id", "guest")
    session = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": body.title,
        "message_count": 0,
        "last_message": None,
    }
    session_id = await db_insert("sessions", session)
    return {"session_id": session_id, "title": body.title}


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    """Get full message history for a session."""
    user_id = user.get("user_id", "guest")
    messages = await db_find_many(
        "messages",
        {"session_id": session_id, "user_id": user_id},
        limit=100,
    )
    return {"messages": messages, "session_id": session_id}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: dict = Depends(get_current_user),
):
    """Clear session from memory and DB."""
    _session_cache.pop(session_id, None)
    return {"deleted": True, "session_id": session_id}


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    user: dict = Depends(get_current_user),
):
    """Submit rating/feedback for a bot response."""
    await db_update_one(
        "messages",
        {"_id": body.message_id},
        {"feedback_rating": body.rating, "feedback_comment": body.comment},
    )
    return {"success": True}


# ─── Background helpers ───────────────────────────────────────────────────────

async def _persist_messages(**kwargs):
    try:
        user_id = kwargs["user_id"]
        session_id = kwargs["session_id"]

        await db_insert("messages", {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "role": "user",
            "content": kwargs["user_message"],
        })
        await db_insert("messages", {
            "_id": kwargs["msg_id"],
            "user_id": user_id,
            "session_id": session_id,
            "role": "assistant",
            "content": kwargs["bot_reply"],
            "provider": kwargs["provider"],
            "ml_predictions": kwargs["ml_predictions"],
            "is_emergency": kwargs["is_emergency"],
        })
        await db_update_one(
            "sessions",
            {"_id": session_id, "user_id": user_id},
            {
                "last_message": kwargs["user_message"][:80],
                "message_count": 1,
                "updated_at": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"Persist messages error: {e}")
