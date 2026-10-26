"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - AI module
recommend_routes.py - hybrid recommendation engine (content-based +
collaborative filtering), rewritten to use SQLAlchemy ORM and
email-based user keying, matching the rest of the app.

Uses the Resource / ResourceFeedback / MoodLog models already defined
in backend/database.py.
"""

import pandas as pd
from flask import Blueprint, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity

from database import SessionLocal, Resource, ResourceFeedback, MoodLog

CONTENT_WEIGHT = 0.6
COLLAB_WEIGHT = 0.4
MIN_RATINGS_FOR_COLLAB = 5
TOP_N = 5

recommend_bp = Blueprint("recommend", __name__, url_prefix="/api/recommendations")


def get_content_matches(db, emotion: str) -> pd.DataFrame:
    resources = db.query(Resource).all()
    rows = [{
        "id": r.id, "title": r.title, "description": r.description,
        "category": r.category, "target_emotions": r.target_emotions,
    } for r in resources]
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    def matches(tags):
        return emotion in [t.strip() for t in str(tags).split(",")]

    matched = df[df["target_emotions"].apply(matches)].copy()
    if matched.empty:
        matched = df.copy()
    matched["content_score"] = 1.0
    return matched


def get_collaborative_scores(db, user_email: str, candidate_ids: list) -> dict:
    feedback = db.query(ResourceFeedback).all()
    if len(feedback) < MIN_RATINGS_FOR_COLLAB:
        return {}

    fb_df = pd.DataFrame([{
        "user_email": f.user_email, "resource_id": f.resource_id, "rating": f.rating,
    } for f in feedback])

    matrix = fb_df.pivot_table(
        index="user_email", columns="resource_id", values="rating", fill_value=0
    )
    if user_email not in matrix.index:
        return {}

    item_sim = cosine_similarity(matrix.T)
    item_sim_df = pd.DataFrame(item_sim, index=matrix.columns, columns=matrix.columns)

    user_ratings = matrix.loc[user_email]
    rated_items = user_ratings[user_ratings > 0].index.tolist()
    if not rated_items:
        return {}

    scores = {}
    for candidate_id in candidate_ids:
        if candidate_id not in item_sim_df.columns:
            continue
        sims = item_sim_df.loc[candidate_id, rated_items]
        weights = user_ratings[rated_items]
        denom = sims.abs().sum()
        if denom == 0:
            continue
        scores[candidate_id] = float((sims * weights).sum() / denom)

    if scores:
        max_score = max(scores.values()) or 1
        scores = {k: v / max_score for k, v in scores.items()}
    return scores


@recommend_bp.route("", methods=["GET"])
def recommend():
    user_email = request.args.get("user")
    if not user_email or user_email == "undefined":
        return jsonify({"detail": "user is required"}), 400

    db = SessionLocal()
    try:
        latest = db.query(MoodLog).filter(MoodLog.user_email == user_email)\
                    .order_by(MoodLog.created_at.desc()).first()
        if not latest:
            return jsonify({
                "error": "No mood entries logged yet. Log a mood entry first "
                         "to get personalized recommendations."
            }), 200

        emotion = latest.emotion
        content_df = get_content_matches(db, emotion)
        if content_df.empty:
            return jsonify({"error": "No resources configured yet."}), 200

        candidate_ids = content_df["id"].tolist()
        collab_scores = get_collaborative_scores(db, user_email, candidate_ids)

        content_df["collab_score"] = content_df["id"].map(collab_scores).fillna(0)
        if not collab_scores:
            content_df["hybrid_score"] = content_df["content_score"]
        else:
            content_df["hybrid_score"] = (
                CONTENT_WEIGHT * content_df["content_score"]
                + COLLAB_WEIGHT * content_df["collab_score"]
            )

        ranked = content_df.sort_values("hybrid_score", ascending=False).head(TOP_N)
        recs = ranked[["id", "title", "description", "category", "hybrid_score"]]\
            .to_dict(orient="records")

        return jsonify({"based_on_emotion": emotion, "recommendations": recs}), 200
    finally:
        db.close()


@recommend_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    payload = request.get_json(force=True)
    user_email = payload.get("user")
    resource_id = payload.get("resource_id")
    rating = payload.get("rating")

    if not all([user_email, resource_id, rating]):
        return jsonify({"detail": "user, resource_id, and rating are required"}), 400
    if not (1 <= int(rating) <= 5):
        return jsonify({"detail": "rating must be between 1 and 5"}), 400

    db = SessionLocal()
    try:
        db.add(ResourceFeedback(user_email=user_email, resource_id=resource_id, rating=rating))
        db.commit()
        return jsonify({"status": "feedback recorded"}), 201
    finally:
        db.close()


# In backend/app.py:  from recommend_routes import recommend_bp
