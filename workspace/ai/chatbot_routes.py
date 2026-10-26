"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - AI module
chatbot_routes.py - Gemini-powered chatbot, emotion-aware via MoodLog.

Setup:
    pip install google-genai
    export GEMINI_API_KEY="your_free_key_from_aistudio.google.com"
"""

import os
from flask import Blueprint, request, jsonify
from google import genai

from database import SessionLocal, MoodLog

GEMINI_MODEL = "gemini-3.5-flash"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

SYSTEM_INSTRUCTION = """You are the supportive chatbot inside "AI-Empowered Mental Health Awareness Website with AI Chatbot", a
student mental wellness app. Your role:
- Be warm, empathetic, and encouraging, never clinical or robotic.
- You are NOT a therapist and cannot diagnose conditions. If the user
  describes something that sounds like it needs professional support,
  gently encourage them to talk to a counselor, doctor, or trusted person,
  without being preachy about it every single message.
- Keep responses conversational and reasonably short (2-5 sentences)
  unless the user asks for more detail.
- You will sometimes be told the user's most recently logged mood. Use it
  to inform your tone, but don't robotically restate it back at them
  every message.
"""

CRISIS_KEYWORDS = [
    "kill myself", "suicide", "end my life", "want to die",
    "hurt myself", "self harm", "self-harm", "no reason to live",
]

CRISIS_RESPONSE = (
    "I'm really glad you told me this, and I want you to know you don't "
    "have to go through this alone. If you're in immediate danger, please "
    "contact your local emergency number right now. You can also reach a "
    "crisis line to talk to someone immediately - would you like me to "
    "share a helpline for your region?"
)

_user_sessions = {}  # {email: chat_session}


def contains_crisis_language(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in CRISIS_KEYWORDS)


def get_latest_emotion(user_email: str):
    db = SessionLocal()
    try:
        row = db.query(MoodLog).filter(MoodLog.user_email == user_email)\
                 .order_by(MoodLog.created_at.desc()).first()
        return row.emotion if row else None
    finally:
        db.close()


def get_or_create_session(user_email: str, latest_emotion: str):
    if user_email not in _user_sessions:
        instruction = SYSTEM_INSTRUCTION
        if latest_emotion:
            instruction += f"\n\nThe user's most recently logged mood was: {latest_emotion}."
        _user_sessions[user_email] = client.chats.create(
            model=GEMINI_MODEL,
            config={"system_instruction": instruction},
        )
    return _user_sessions[user_email]


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")


@chatbot_bp.route("/message", methods=["POST"])
def send_message():
    payload = request.get_json(force=True)
    user_email = payload.get("user")
    message = payload.get("message", "")

    if not user_email or not message.strip():
        return jsonify({"detail": "user and message are required"}), 400

    if contains_crisis_language(message):
        return jsonify({"reply": CRISIS_RESPONSE, "flagged": True}), 200

    latest_emotion = get_latest_emotion(user_email)
    try:
        chat = get_or_create_session(user_email, latest_emotion)
        response = chat.send_message(message)
    except Exception as e:
        print(f"Gemini error: {e}")
        _user_sessions.pop(user_email, None)
        return jsonify({
            "reply": "Sorry, I'm having trouble connecting right now. Please try again in a moment.",
            "flagged": False,
        }), 200

    return jsonify({
        "reply": response.text,
        "context_emotion_used": latest_emotion,
        "flagged": False,
    }), 200


@chatbot_bp.route("/reset", methods=["POST"])
def reset_session():
    user_email = request.get_json(force=True).get("user")
    _user_sessions.pop(user_email, None)
    return jsonify({"status": "session reset"}), 200