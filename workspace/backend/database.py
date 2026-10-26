"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - Flask + MySQL migration
database.py - SQLAlchemy models (same schema as the original FastAPI/SQLite
version in mental-backend/database.py, just pointed at MySQL instead).

Setup:
    pip install sqlalchemy pymysql

    Create the MySQL database first:
        CREATE DATABASE mindmate CHARACTER SET utf8mb4;

    Set your connection details via environment variables (recommended)
    or edit DATABASE_URL directly below.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "AI-Empowered_Mental_Health_Awareness_Website_with_AI_Chatbot")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------
# Existing tables (ported as-is from the FastAPI/SQLite version)
# ---------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150))
    country = Column(String(100))
    message = Column(Text)
    rating = Column(Integer)


class Exercise(Base):
    __tablename__ = "exercise"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150))
    description = Column(Text)


class Diet(Base):
    __tablename__ = "diet"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150))
    description = Column(Text)


class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150))
    link = Column(String(255))


class StressResult(Base):
    __tablename__ = "stress_results"
    id = Column(Integer, primary_key=True, index=True)
    user = Column(String(255), index=True)
    sleep = Column(Float)
    bp = Column(String(20))
    resp = Column(Float)
    heart = Column(Float)
    stress_level = Column(String(20))
    advice = Column(String(2000))
    timestamp = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True)
    password = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)


# ---------------------------------------------------------------------
# NEW tables for the mood tracker (Steps 5-7 from our earlier work)
# ---------------------------------------------------------------------
class MoodLog(Base):
    __tablename__ = "mood_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), index=True)   # matches User.email (this
                                                     # project keys users by
                                                     # email, not numeric id)
    entry_text = Column(Text)
    emotion = Column(String(30))
    confidence = Column(Float)
    mood_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150))
    description = Column(Text)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, index=True)
    question_text = Column(String(255))
    question_order = Column(Integer)


class QuizOption(Base):
    __tablename__ = "quiz_options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, index=True)
    option_text = Column(String(150))
    score_value = Column(Integer)


class QuizResult(Base):
    __tablename__ = "quiz_results"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), index=True)
    quiz_id = Column(Integer)
    total_score = Column(Integer)
    result_band = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150))
    description = Column(Text)
    category = Column(String(50))
    target_emotions = Column(String(150))  # comma-separated


class ResourceFeedback(Base):
    __tablename__ = "resource_feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), index=True)
    resource_id = Column(Integer)
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
