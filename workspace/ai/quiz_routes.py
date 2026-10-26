"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - AI module
quiz_routes.py - self-assessment quiz, rewritten to use SQLAlchemy ORM
and email-based user keying. Also logs each quiz result into MoodLog so
it feeds the same trend graphs and forecaster as journal entries.

NOTE ON CONTENT: this is an original self-reflection quiz, not a
reproduction of a validated clinical instrument (PHQ-9/GAD-7 etc) - see
quiz_seed_data.sql for the reasoning.
"""

from flask import Blueprint, request, jsonify
from database import SessionLocal, Quiz, QuizQuestion, QuizOption, QuizResult, MoodLog

DISCLAIMER = (
    "This check-in is a self-reflection tool, not a clinical diagnosis. "
    "If you're struggling, please consider speaking with a counselor or doctor."
)

quiz_bp = Blueprint("quiz", __name__, url_prefix="/api/quiz")


def score_to_band(total_score: int, max_possible: int) -> str:
    pct = total_score / max_possible
    if pct < 0.25:
        return "Doing well"
    elif pct < 0.5:
        return "Mild strain"
    elif pct < 0.75:
        return "Moderate strain"
    else:
        return "High strain - consider reaching out for support"


@quiz_bp.route("/<int:quiz_id>", methods=["GET"])
def get_quiz(quiz_id):
    db = SessionLocal()
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return jsonify({"detail": "Quiz not found"}), 404

        questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id)\
                       .order_by(QuizQuestion.question_order.asc()).all()

        result = []
        for q in questions:
            options = db.query(QuizOption).filter(QuizOption.question_id == q.id).all()
            result.append({
                "id": q.id, "question_text": q.question_text,
                "options": [{"id": o.id, "option_text": o.option_text,
                             "score_value": o.score_value} for o in options],
            })

        return jsonify({
            "quiz": {"id": quiz.id, "title": quiz.title, "description": quiz.description},
            "questions": result,
            "disclaimer": DISCLAIMER,
        }), 200
    finally:
        db.close()


@quiz_bp.route("/submit", methods=["POST"])
def submit_quiz():
    """Expects: { "user": "email", "quiz_id": 1, "selected_option_ids": [3,7,...] }"""
    payload = request.get_json(force=True)
    user_email = payload.get("user")
    quiz_id = payload.get("quiz_id")
    selected_option_ids = payload.get("selected_option_ids", [])

    if not user_email or not quiz_id or not selected_option_ids:
        return jsonify({"detail": "user, quiz_id, and selected_option_ids are required"}), 400

    db = SessionLocal()
    try:
        options = db.query(QuizOption).filter(QuizOption.id.in_(selected_option_ids)).all()
        total_score = sum(o.score_value for o in options)

        q_count = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).count()
        max_possible = q_count * 3
        band = score_to_band(total_score, max_possible)

        db.add(QuizResult(user_email=user_email, quiz_id=quiz_id,
                           total_score=total_score, result_band=band))

        # Also feed into mood_logs so quiz check-ins show up in the same
        # trend dashboard / forecaster pipeline as journal entries.
        mood_score = round(1 - 2 * (total_score / max_possible), 2)
        db.add(MoodLog(user_email=user_email, entry_text=f"[Quiz check-in] {band}",
                        emotion="quiz_result", confidence=1.0, mood_score=mood_score))

        db.commit()

        return jsonify({
            "total_score": total_score, "max_possible": max_possible,
            "result_band": band, "disclaimer": DISCLAIMER,
        }), 201
    finally:
        db.close()


# In backend/app.py:  from quiz_routes import quiz_bp
