"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - Mood tracker integration (matches your real app.py)
mood_routes.py - classifier + forecaster endpoints, using SQLAlchemy ORM
and email-based user keying (same convention as StressResult.user).

Requirements (in addition to app.py's requirements):
    pip install tensorflow numpy

Needs these files in the same folder (from Steps 1-4):
    tokenizer.pkl, label_encoder.pkl, emotion_bilstm_best.h5, mood_forecast_lstm.h5
"""

import pickle
import numpy as np
from flask import Blueprint, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

from database import SessionLocal, MoodLog

MAX_LEN = 40
WINDOW_SIZE = 7

EMOTION_TO_VALENCE = {
    "sadness": -0.7, "joy": 0.7, "love": 0.6,
    "anger": -0.6, "fear": -0.5, "surprise": 0.1,
}

import os
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

with open(os.path.join(MODELS_DIR, "tokenizer.pkl"), "rb") as f:
    tokenizer = pickle.load(f)
with open(os.path.join(MODELS_DIR, "label_encoder.pkl"), "rb") as f:
    label_encoder = pickle.load(f)

EMOTION_NAMES = list(label_encoder.classes_)
classifier_model = load_model(os.path.join(MODELS_DIR, "emotion_bilstm_best.keras"))
forecast_model = load_model(os.path.join(MODELS_DIR, "mood_forecast_lstm.keras"))


def clean_text(text: str) -> str:
    import re
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#", "", text)
    text = re.sub(r"[^a-z\s']", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def score_to_emotion_bucket(score: float) -> str:
    if score > 0.5: return "joy"
    elif score > 0.15: return "love"
    elif score > -0.15: return "surprise / neutral"
    elif score > -0.5: return "fear"
    else: return "sadness"


mood_bp = Blueprint("mood", __name__, url_prefix="/api/mood")


@mood_bp.route("/entry", methods=["POST"])
def add_mood_entry():
    payload = request.get_json(force=True)
    user_email = payload.get("user")
    text = payload.get("text", "")

    if not user_email or not text.strip():
        return jsonify({"detail": "user and text are required"}), 400

    cleaned = clean_text(text)
    seq = tokenizer.texts_to_sequences([cleaned])
    padded = pad_sequences(seq, maxlen=MAX_LEN, padding="post", truncating="post")

    pred_probs = classifier_model.predict(padded, verbose=0)[0]
    pred_idx = int(np.argmax(pred_probs))
    emotion = EMOTION_NAMES[pred_idx]
    confidence = float(pred_probs[pred_idx])
    mood_score = EMOTION_TO_VALENCE[emotion]

    db = SessionLocal()
    try:
        entry = MoodLog(
            user_email=user_email, entry_text=text,
            emotion=emotion, confidence=confidence, mood_score=mood_score,
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()

    return jsonify({
        "emotion": emotion,
        "confidence": round(confidence, 3),
        "mood_score": mood_score,
    }), 201


@mood_bp.route("/history", methods=["GET"])
def get_mood_history():
    user_email = request.args.get("user")
    if not user_email or user_email == "undefined":
        return jsonify([])

    db = SessionLocal()
    try:
        rows = db.query(MoodLog).filter(MoodLog.user_email == user_email)\
                  .order_by(MoodLog.created_at.asc()).all()
        return jsonify([{
            "emotion": r.emotion, "confidence": r.confidence,
            "mood_score": r.mood_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "entry_text": r.entry_text,
        } for r in rows])
    finally:
        db.close()


@mood_bp.route("/forecast", methods=["GET"])
def get_mood_forecast():
    user_email = request.args.get("user")
    if not user_email or user_email == "undefined":
        return jsonify({"detail": "user is required"}), 400

    db = SessionLocal()
    try:
        rows = db.query(MoodLog).filter(MoodLog.user_email == user_email)\
                  .order_by(MoodLog.created_at.desc()).limit(WINDOW_SIZE).all()
    finally:
        db.close()

    if len(rows) < WINDOW_SIZE:
        return jsonify({
            "error": f"Not enough history yet. Need {WINDOW_SIZE} entries, have {len(rows)}."
        }), 200

    scores = [r.mood_score for r in reversed(rows)]
    X = np.array(scores).reshape(1, WINDOW_SIZE, 1)
    predicted_score = float(forecast_model.predict(X, verbose=0)[0][0])

    return jsonify({
        "predicted_mood_score": round(predicted_score, 3),
        "predicted_trend": score_to_emotion_bucket(predicted_score),
        "based_on_last_n_entries": WINDOW_SIZE,
    }), 200


# In your app.py, add:
#
#   from mood_routes import mood_bp
#   app.register_blueprint(mood_bp)
