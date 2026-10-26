"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - Flask + MySQL migration
app.py
"""

import os
import sys
import re
import secrets
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from database import (
    engine, SessionLocal, Base,
    User, Feedback, Exercise, Diet, Video, StressResult, Admin,
)

AI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai")
sys.path.append(AI_DIR)

Base.metadata.create_all(bind=engine)

app = Flask(__name__)

# =====================================================================
# CORS FIX: handle OPTIONS preflight for ALL routes including blueprints
# =====================================================================
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, token, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.status_code = 200
        return response

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, token, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response

CORS(app)
# =====================================================================

# --- AI blueprints ---
try:
    from mood_routes import mood_bp
    app.register_blueprint(mood_bp)
except Exception as e:
    print(f"[warning] mood_routes not loaded: {e}")

try:
    from chatbot_routes import chatbot_bp
    app.register_blueprint(chatbot_bp)
except Exception as e:
    print(f"[warning] chatbot_routes not loaded: {e}")

try:
    from recommend_routes import recommend_bp
    app.register_blueprint(recommend_bp)
except Exception as e:
    print(f"[warning] recommend_routes not loaded: {e}")

try:
    from quiz_routes import quiz_bp
    app.register_blueprint(quiz_bp)
except Exception as e:
    print(f"[warning] quiz_routes not loaded: {e}")

user_tokens = {}
admin_tokens = {}


def get_db():
    return SessionLocal()


@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "AI-Empowered_Mental_Health_Awareness_Website_with_AI_Chatbot backend is running (Flask + MySQL)!"})


@app.route("/tables", methods=["GET"])
def show_tables():
    from sqlalchemy import inspect
    inspector = inspect(engine)
    return jsonify({"tables": inspector.get_table_names()})


def require_user():
    token = request.headers.get("token")
    if not token or token not in user_tokens:
        return None
    return user_tokens[token]


def require_admin(db):
    token = request.headers.get("token")
    if not token or token not in admin_tokens:
        return None
    admin_id = admin_tokens[token]
    admin = db.query(Admin).filter(Admin.id == admin_id, Admin.is_active == 1).first()
    return admin


def parse_blood_pressure(bp_str):
    try:
        systolic, diastolic = map(int, bp_str.split('/'))
        return systolic, diastolic
    except Exception:
        try:
            return int(bp_str), 0
        except Exception:
            return 120, 80


def get_hypertension_stage(systolic, diastolic):
    if systolic >= 180 or diastolic >= 120:
        return "Hypertensive Crisis", "DANGER"
    elif systolic >= 160 or diastolic >= 100:
        return "Stage 2 Hypertension", "HIGH"
    elif systolic >= 140 or diastolic >= 90:
        return "Stage 1 Hypertension", "MEDIUM"
    elif systolic >= 130 or diastolic >= 80:
        return "Elevated", "LOW"
    else:
        return "Normal", "NORMAL"


def get_medical_advice(systolic, diastolic, sleep, resp, heart):
    bp_stage, bp_risk = get_hypertension_stage(systolic, diastolic)
    advice_parts, warnings = [], []

    if bp_risk == "DANGER":
        warnings.append("HYPERTENSIVE CRISIS: Seek immediate medical attention!")
        advice_parts.append("Go to emergency room immediately.")
    elif bp_risk == "HIGH":
        warnings.append("Stage 2 Hypertension detected")
        advice_parts.append("Consult doctor within 1 week.")
    elif bp_risk == "MEDIUM":
        warnings.append("Stage 1 Hypertension detected")
        advice_parts.append("Schedule doctor appointment within 1 month.")
    elif bp_risk == "LOW":
        advice_parts.append("BP slightly elevated. Monitor regularly.")
    else:
        advice_parts.append("Blood pressure is normal.")

    if sleep < 5:
        advice_parts.append(f"CRITICAL: Only {sleep} hours of sleep. Aim for 7-9 hours nightly.")
    elif sleep < 7:
        advice_parts.append(f"Sleep duration is low ({sleep} hours). Try to get 7-9 hours.")
    else:
        advice_parts.append(f"Good sleep duration ({sleep} hours).")

    if heart > 100:
        advice_parts.append(f"Heart rate is elevated ({heart} bpm).")
    elif heart < 60:
        advice_parts.append(f"Heart rate is low ({heart} bpm).")
    else:
        advice_parts.append(f"Heart rate is normal ({heart} bpm).")

    if resp > 20:
        advice_parts.append(f"Respiration rate is high ({resp} breaths/min).")
    elif resp < 12:
        advice_parts.append(f"Respiration rate is low ({resp} breaths/min).")
    else:
        advice_parts.append(f"Respiration rate is normal ({resp} breaths/min).")

    return {"warnings": warnings, "analysis": advice_parts, "bp_stage": bp_stage, "bp_risk": bp_risk}


@app.route("/stress", methods=["POST"])
def stress_detect():
    db = get_db()
    try:
        payload = request.get_json(force=True)
        user_email = payload.get("user") or "guest@example.com"
        if user_email == "undefined":
            user_email = "guest@example.com"

        sleep, resp, heart = float(payload["sleep"]), float(payload["resp"]), float(payload["heart"])
        bp = payload["bp"]

        if not (0 < sleep <= 24) or not (0 < resp <= 60) or not (0 < heart <= 300):
            raise ValueError("Invalid numeric input")

        systolic, diastolic = parse_blood_pressure(bp)
        if not (50 <= systolic <= 300) or not (30 <= diastolic <= 200):
            raise ValueError("Invalid blood pressure range")

        medical_data = get_medical_advice(systolic, diastolic, sleep, resp, heart)

        score = 0
        if sleep < 5: score += 4
        elif sleep < 7: score += 2
        if heart > 100: score += 3
        elif heart < 60: score += 2
        if resp > 20: score += 2
        elif resp < 12: score += 2

        if score >= 8:
            stress_level, stress_advice = "HIGH", "HIGH STRESS: Multiple health concerns detected."
        elif score >= 5:
            stress_level, stress_advice = "MEDIUM", "MODERATE STRESS: Several vital signs need attention."
        elif score >= 2:
            stress_level, stress_advice = "LOW", "MILD STRESS: Some vital signs could be improved."
        else:
            stress_level, stress_advice = "OPTIMAL", "EXCELLENT: All vital signs are healthy."

        full_advice = f"{stress_advice}\n\nBlood Pressure Stage: {medical_data['bp_stage']}\n"
        if medical_data["warnings"]:
            full_advice += "WARNINGS:\n" + "\n".join(medical_data["warnings"]) + "\n"
        full_advice += "ANALYSIS:\n" + "\n".join(medical_data["analysis"]) + "\n"

        result = StressResult(user=user_email, sleep=sleep, bp=f"{systolic}/{diastolic}",
                               resp=resp, heart=heart, stress_level=stress_level, advice=full_advice)
        db.add(result)
        db.commit()
        db.refresh(result)

        return jsonify({
            "id": result.id, "stress_level": stress_level, "advice": full_advice,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            "bp_stage": medical_data["bp_stage"], "systolic": systolic, "diastolic": diastolic,
        })
    except Exception as e:
        return jsonify({"stress_level": "MEDIUM", "advice": f"Error: {str(e)}", "timestamp": None})
    finally:
        db.close()


@app.route("/stress/history", methods=["GET"])
def stress_history():
    user = request.args.get("user")
    if not user or user == "undefined":
        return jsonify([])
    db = get_db()
    try:
        results = db.query(StressResult).filter(StressResult.user == user)\
                    .order_by(StressResult.timestamp.desc()).all()
        return jsonify([{
            "id": r.id, "sleep": r.sleep, "bp": r.bp, "resp": r.resp, "heart": r.heart,
            "stress_level": r.stress_level, "advice": r.advice,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        } for r in results])
    finally:
        db.close()


@app.route("/stress/history/delete/<int:id>", methods=["DELETE"])
def delete_stress_history(id):
    db = get_db()
    try:
        record = db.query(StressResult).filter(StressResult.id == id).first()
        if not record:
            return jsonify({"detail": "Stress history record not found"}), 404
        db.delete(record)
        db.commit()
        return jsonify({"message": "Stress history record deleted successfully"})
    finally:
        db.close()


@app.route("/feedback", methods=["POST"])
def add_feedback():
    db = get_db()
    try:
        name = request.form.get("name")
        country = request.form.get("country")
        message = request.form.get("message")
        rating = int(request.form.get("rating"))

        if not (1 <= rating <= 5):
            return jsonify({"detail": "Rating must be 1-5"}), 400

        fb = Feedback(name=name, country=country, message=message, rating=rating)
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return jsonify({"message": "Feedback submitted successfully", "id": fb.id}), 200
    finally:
        db.close()


@app.route("/feedback", methods=["GET"])
def get_feedback():
    db = get_db()
    try:
        feedbacks = db.query(Feedback).order_by(Feedback.id.desc()).all()
        return jsonify([{
            "id": f.id, "name": f.name, "country": f.country,
            "message": f.message, "rating": f.rating,
        } for f in feedbacks])
    finally:
        db.close()


@app.route("/register", methods=["POST"])
def register():
    db = get_db()
    try:
        email = request.form.get("email")
        password = request.form.get("password")

        if not re.match(r"^[\w\.-]+@gmail\.com$", email or ""):
            return jsonify({"detail": "Email must be @gmail.com"}), 400
        if not password or len(password) < 6:
            return jsonify({"detail": "Password too short"}), 400
        if db.query(User).filter(User.email == email).first():
            return jsonify({"detail": "User exists"}), 400

        hashed_password = generate_password_hash(password)
        db.add(User(email=email, password=hashed_password))
        db.commit()
        token = secrets.token_hex(16)
        user_tokens[token] = email
        return jsonify({"message": f"User {email} registered", "token": token})
    finally:
        db.close()


@app.route("/login", methods=["POST"])
def login():
    db = get_db()
    try:
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.query(User).filter(User.email == email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"detail": "Invalid credentials"}), 400
        token = secrets.token_hex(16)
        user_tokens[token] = email
        return jsonify({"message": f"User {email} logged in", "token": token})
    finally:
        db.close()


@app.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("token")
    user_tokens.pop(token, None)
    return jsonify({"message": "User logged out"})


@app.route("/admin/login", methods=["POST"])
def admin_login():
    db = get_db()
    try:
        username = request.form.get("username")
        password = request.form.get("password")
        admin = db.query(Admin).filter(
            ((Admin.email == username) | (Admin.username == username)),
            Admin.is_active == 1,
        ).first()
        if not admin or not check_password_hash(admin.password, password):
            return jsonify({"detail": "Invalid admin credentials"}), 400
        token = secrets.token_hex(16)
        admin_tokens[token] = admin.id
        return jsonify({
            "message": f"Admin {admin.email} logged in", "token": token,
            "admin_id": admin.id, "username": admin.email,
        })
    finally:
        db.close()


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    token = request.headers.get("token")
    admin_tokens.pop(token, None)
    return jsonify({"message": "Admin logged out"})


@app.route("/admin/users", methods=["GET"])
def admin_get_users():
    db = get_db()
    try:
        admin = require_admin(db)
        if not admin:
            return jsonify({"detail": "Unauthorized admin"}), 401
        users = db.query(User).all()
        return jsonify([{"id": u.id, "email": u.email} for u in users])
    finally:
        db.close()


@app.route("/admin/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    db = get_db()
    try:
        admin = require_admin(db)
        if not admin:
            return jsonify({"detail": "Unauthorized admin"}), 401
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"detail": "User not found"}), 404
        db.delete(user)
        db.commit()
        return jsonify({"message": "User deleted"})
    finally:
        db.close()


@app.route("/admin/feedbacks", methods=["GET"])
def admin_get_feedbacks():
    db = get_db()
    try:
        admin = require_admin(db)
        if not admin:
            return jsonify({"detail": "Unauthorized admin"}), 401
        feedbacks = db.query(Feedback).all()
        return jsonify([{
            "id": f.id, "name": f.name, "country": f.country,
            "message": f.message, "rating": f.rating,
        } for f in feedbacks])
    finally:
        db.close()


@app.route("/admin/feedbacks/<int:fid>", methods=["DELETE"])
def admin_delete_feedback(fid):
    db = get_db()
    try:
        admin = require_admin(db)
        if not admin:
            return jsonify({"detail": "Unauthorized admin"}), 401
        fb = db.query(Feedback).filter(Feedback.id == fid).first()
        if not fb:
            return jsonify({"detail": "Feedback not found"}), 404
        db.delete(fb)
        db.commit()
        return jsonify({"message": "Feedback deleted"})
    finally:
        db.close()


@app.route("/admin/analytics/users", methods=["GET"])
def admin_user_stats():
    db = get_db()
    try:
        admin = require_admin(db)
        if not admin:
            return jsonify({"detail": "Unauthorized admin"}), 401
        return jsonify({
            "users": db.query(User).count(),
            "feedbacks": db.query(Feedback).count(),
            "stress_entries": db.query(StressResult).count(),
        })
    finally:
        db.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)