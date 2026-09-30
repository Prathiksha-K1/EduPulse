from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from database import Base

class User(Base):
    """
    Student or Teacher user profile.
    Real tracking: XP starts at 0, streaks start at 0 until first completed activity.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="student") # student or teacher
    classroom = Column(String(100), default="Grade 10 - Section A")
    preferred_lang = Column(String(10), default="en")
    xp = Column(Integer, default=0) # Real XP, starts at 0
    daily_xp = Column(Integer, default=0)
    daily_cap = Column(Integer, default=250)
    streak = Column(Integer, default=0) # Starts at 0 until first completed study activity
    completed_lessons = Column(Integer, default=0)
    quizzes_taken = Column(Integer, default=0)
    last_active_date = Column(String(20), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DocumentSummary(Base):
    """
    Records uploaded PDF summaries, language detection, and generated quizzes.
    """
    __tablename__ = "document_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    filename = Column(String(255), nullable=False)
    detected_language = Column(String(50), default="en")
    target_language = Column(String(10), default="en")
    summary = Column(Text, nullable=False)
    key_terms = Column(Text, default="[]")
    quiz_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LessonProgress(Base):
    """
    Records student completion of daily lessons and quizzes.
    """
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    subject = Column(String(50), nullable=False) # Math, Physics, Chemistry, English
    topic = Column(String(150), nullable=False)
    completed = Column(Boolean, default=False)
    quiz_score = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ActivityLog(Base):
    """
    Real-time activity log displayed on the professional student dashboard.
    """
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    activity_type = Column(String(50), nullable=False) # quiz, lesson, document
    title = Column(String(200), nullable=False)
    xp_earned = Column(Integer, default=0)
    details = Column(String(255), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

