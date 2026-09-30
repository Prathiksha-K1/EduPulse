import os
import sys
import json
import hashlib
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional

# Ensure UTF-8 output encoding for non-ASCII characters (Tamil, Hindi, Telugu) on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from google import genai
import pymupdf
import edge_tts

from database import engine, Base, get_db
from models import User, DocumentSummary, LessonProgress, ActivityLog
from knowledge_tracing import estimate_level

# Load environment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize database schema
Base.metadata.create_all(bind=engine)

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

gemini_client = None
if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[Warning] Failed to initialize Google GenAI client: {e}")

app = FastAPI(
    title="EduPulse API",
    description="Backend API for EduPulse - Real Auth, Live CBSE Curriculum, Real Gamification & On-Device Attention Tracking",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "voice": "en-IN-NeerjaNeural"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "voice": "ta-IN-ValluvarNeural"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "voice": "hi-IN-MadhurNeural"},
    "te": {"name": "Telugu", "native": "తెలుగు", "voice": "te-IN-MohanNeural"}
}

CBSE_SYLLABUS = [
    {
        "id": "math",
        "name": "Mathematics",
        "icon": "Calculator",
        "color": "emerald",
        "description": "CBSE Class 10/12 Algebra, Trigonometry, Coordinate Geometry & Calculus",
        "topics": [
            "Quadratic Equations & Roots",
            "Arithmetic Progressions (AP)",
            "Trigonometric Ratios & Identities",
            "Coordinate Geometry & Distance Formula",
            "Real Numbers & Fundamental Theorem of Arithmetic",
            "Probability & Statistics Basics"
        ]
    },
    {
        "id": "physics",
        "name": "Physics",
        "icon": "Zap",
        "color": "teal",
        "description": "Optics, Electricity, Magnetism, Motion, Gravitation & Energy",
        "topics": [
            "Light: Reflection, Refraction & Lens Formula",
            "Electricity: Ohm's Law, Resistance & Power",
            "Magnetic Effects of Electric Current",
            "Human Eye & The Colourful World",
            "Sources of Energy & Conservation of Momentum"
        ]
    },
    {
        "id": "chemistry",
        "name": "Chemistry",
        "icon": "FlaskConical",
        "color": "green",
        "description": "Chemical Reactions, Acids & Bases, Periodic Classification, Organic Chemistry",
        "topics": [
            "Chemical Reactions, Types & Balancing Equations",
            "Acids, Bases, and Salts & pH Scale",
            "Metals and Non-Metals: Properties & Reactivity",
            "Carbon and its Compounds: Covalent Bonding",
            "Periodic Classification of Elements"
        ]
    },
    {
        "id": "english",
        "name": "English",
        "icon": "BookMarked",
        "color": "emerald",
        "description": "Reading Comprehension, Grammar Mastery, Formal Writing & Literature",
        "topics": [
            "Reading Comprehension & Critical Analysis",
            "Tenses, Modals & Subject-Verb Agreement",
            "Formal Letter & Analytical Paragraph Writing",
            "Figures of Speech & Poetic Devices",
            "Reported Speech & Active-Passive Voice"
        ]
    }
]

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def call_gemini(prompt: str) -> str:
    if not gemini_client:
        raise HTTPException(
            status_code=500,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY in backend/.env"
        )
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Error]: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"AI service connection notice: {str(e)}"
        )

import re

def clean_json_response(raw_text: str):
    text_content = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_content)
    if match:
        text_content = match.group(1).strip()
    else:
        start_bracket = text_content.find('[')
        start_brace = text_content.find('{')
        if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
            end_bracket = text_content.rfind(']')
            if end_bracket != -1:
                text_content = text_content[start_bracket:end_bracket+1]
        elif start_brace != -1:
            end_brace = text_content.rfind('}')
            if end_brace != -1:
                text_content = text_content[start_brace:end_brace+1]
    return json.loads(text_content.strip())

# ==================== Request Schemas ====================
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"
    classroom: str = "CBSE Class 10 - Section A"
    preferred_lang: str = "en"

class LoginRequest(BaseModel):
    email: str
    password: str

class LessonRequest(BaseModel):
    subject: str
    topic: str
    language: str = "en"

class CompleteLessonRequest(BaseModel):
    user_id: int
    subject: str
    topic: str
    duration_seconds: int = 180

class QuizRequest(BaseModel):
    subject: str
    topic: str
    language: str = "en"
    context_text: Optional[str] = None

class QuizGradeRequest(BaseModel):
    user_id: int
    subject: str
    topic: str
    user_answers: List[int]
    correct_answers: List[int]
    time_taken_seconds: int = 60

class DoubtRequest(BaseModel):
    subject: str
    topic: str
    language: str = "en"
    doubt_text: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

class ResetUserRequest(BaseModel):
    user_id: int

class ResetClassroomRequest(BaseModel):
    classroom: Optional[str] = "CBSE Class 10 - Section A"

# ==================== Authentication Endpoints ====================

@app.post("/api/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new student or teacher with real zero-based stats."""
    existing = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="This email is already registered. Please sign in.")

    new_user = User(
        name=req.name.strip(),
        email=req.email.strip().lower(),
        password_hash=hash_password(req.password),
        role=req.role,
        classroom=req.classroom,
        preferred_lang=req.preferred_lang,
        xp=0, # REAL 0 XP!
        daily_xp=0,
        streak=1, # 1 day streak starting today
        completed_lessons=0,
        quizzes_taken=0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log registration activity
    log = ActivityLog(
        user_id=new_user.id,
        activity_type="joined",
        title="Joined EduPulse Classroom",
        xp_earned=0,
        details=f"Enrolled in {new_user.classroom}"
    )
    db.add(log)
    db.commit()

    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
        "classroom": new_user.classroom,
        "preferred_lang": new_user.preferred_lang,
        "xp": new_user.xp,
        "streak": new_user.streak
    }

@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user and updates real daily active streak."""
    user = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if not user or user.password_hash != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Real Streak tracking logic
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    if user.last_active_date == yesterday:
        user.streak += 1
        user.daily_xp = 0 # Fresh daily cap for new day
    elif user.last_active_date != today:
        # Missed more than 1 day
        user.streak = 1
        user.daily_xp = 0

    user.last_active_date = today
    db.commit()

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "classroom": user.classroom,
        "preferred_lang": user.preferred_lang,
        "xp": user.xp,
        "streak": user.streak,
        "daily_xp": user.daily_xp,
        "daily_cap": user.daily_cap,
        "completed_lessons": user.completed_lessons,
        "quizzes_taken": user.quizzes_taken
    }

@app.get("/api/auth/me")
def get_current_user(user_id: int, db: Session = Depends(get_db)):
    """Fetches real on-spot profile data for authenticated student."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "classroom": user.classroom,
        "preferred_lang": user.preferred_lang,
        "xp": user.xp,
        "streak": user.streak,
        "daily_xp": user.daily_xp,
        "daily_cap": user.daily_cap,
        "completed_lessons": user.completed_lessons,
        "quizzes_taken": user.quizzes_taken
    }

@app.get("/api/user/activities")
def get_user_activities(user_id: int, db: Session = Depends(get_db)):
    """Fetches real activity logs for student dashboard."""
    logs = db.query(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.created_at.desc()).limit(10).all()
    return [
        {
            "id": l.id,
            "type": l.activity_type,
            "title": l.title,
            "xp_earned": l.xp_earned,
            "details": l.details,
            "time": l.created_at.strftime("%b %d, %H:%M")
        } for l in logs
    ]

# ==================== CBSE Curriculum & Learning ====================

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    gemini_ready = bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 10)
    return {
        "status": "healthy",
        "service": "EduPulse API v2",
        "database": "connected (SQLite)",
        "gemini": {
            "configured": gemini_ready,
            "model": GEMINI_MODEL
        }
    }

@app.get("/api/subjects")
def get_subjects():
    return CBSE_SYLLABUS

@app.post("/api/lesson/generate")
def generate_lesson(req: LessonRequest):
    """Generates a CBSE lesson in real time using Gemini in the requested language."""
    lang_name = SUPPORTED_LANGUAGES.get(req.language, {}).get("name", "English")

    prompt = f"""
You are a master CBSE teacher. Create a structured, engaging, and clear student lesson for the CBSE syllabus topic:
Subject: {req.subject}
Topic: {req.topic}
Target Language: {lang_name} ({req.language})

Explain everything directly in {lang_name}. Make it inspiring, crystal-clear, and easy to understand for Class 10/12 students.
Return ONLY valid JSON matching this schema with no markdown formatting:
{{
  "title": "Topic title in {lang_name}",
  "estimated_minutes": 5,
  "summary": "2-3 paragraphs explaining the core concept in friendly, simple language in {lang_name}",
  "key_concepts": [
    "Key takeaway point 1 in {lang_name}",
    "Key takeaway point 2 in {lang_name}",
    "Key takeaway point 3 in {lang_name}"
  ],
  "real_world_example": "A real-world relatable example illustrating this concept in {lang_name}",
  "quick_tip": "A smart memory rule, formula, or exam tip in {lang_name}"
}}
"""
    raw = call_gemini(prompt)
    try:
        return clean_json_response(raw)
    except Exception:
        return {
            "title": f"{req.topic} ({req.subject})",
            "estimated_minutes": 5,
            "summary": raw,
            "key_concepts": ["Review core definitions", "Apply formula carefully", "Practice past paper problems"],
            "real_world_example": "Everyday science and mathematics in action.",
            "quick_tip": "Remember to write units and check steps in exams."
        }

@app.post("/api/lesson/complete")
def complete_lesson(req: CompleteLessonRequest, db: Session = Depends(get_db)):
    """Awards real XP when student finishes studying a lesson."""
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    xp_awarded = 15
    if user.daily_xp + xp_awarded > user.daily_cap:
        xp_awarded = max(0, user.daily_cap - user.daily_xp)

    user.xp += xp_awarded
    user.daily_xp += xp_awarded
    user.completed_lessons += 1

    # Record lesson progress in database
    progress = LessonProgress(
        user_id=user.id,
        subject=req.subject,
        topic=req.topic,
        completed=True,
        duration_seconds=req.duration_seconds
    )
    db.add(progress)

    # Record activity log
    log = ActivityLog(
        user_id=user.id,
        activity_type="lesson",
        title=f"Studied {req.subject}: {req.topic}",
        xp_earned=xp_awarded,
        details=f"Completed study session in {max(1, req.duration_seconds // 60)}m"
    )
    db.add(log)
    db.commit()

    return {
        "xp_earned": xp_awarded,
        "total_xp": user.xp,
        "completed_lessons": user.completed_lessons
    }

@app.post("/api/quiz/generate")
def generate_quiz(req: QuizRequest):
    """Generates a 5-question multiple choice quiz in the requested language."""
    lang_name = SUPPORTED_LANGUAGES.get(req.language, {}).get("name", "English")
    context_part = f"\nAdditional Context / Reference Notes:\n{req.context_text[:2000]}" if req.context_text else ""

    prompt = f"""
You are an expert CBSE examiner. Create a 5-question multiple choice quiz for:
Subject: {req.subject}
Topic: {req.topic}
Language: {lang_name}{context_part}

Requirements:
- Exactly 5 multiple-choice questions.
- Write questions, options, and explanations in {lang_name}.
- Each question must have exactly 4 distinct options.
- 'correct_index' must be 0, 1, 2, or 3 (0-indexed).
- Provide a helpful, clear explanation in {lang_name} for why the answer is correct.

Return ONLY valid JSON with this exact array structure:
[
  {{
    "id": 1,
    "question": "Question text in {lang_name}?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Explanation in {lang_name}"
  }}
]
"""
    raw = call_gemini(prompt)
    try:
        parsed = clean_json_response(raw)
        if isinstance(parsed, dict) and "questions" in parsed:
            questions = parsed["questions"]
        elif isinstance(parsed, list):
            questions = parsed
        else:
            questions = [parsed]
        return {"questions": questions}
    except Exception as e:
        print(f"Quiz JSON parse error: {e}")
        fallback = [
            {
                "id": 1,
                "question": f"What is the fundamental law involved in {req.topic}?",
                "options": ["Conservation of Energy", "Direct Proportionality", "Equilibrium State", "Linear Variance"],
                "correct_index": 0,
                "explanation": "Conservation principles form the foundation of this topic."
            }
        ]
        return {"questions": fallback}

@app.post("/api/quiz/grade")
def grade_quiz(req: QuizGradeRequest, db: Session = Depends(get_db)):
    """Grades quiz, awards real on-spot XP, and records activity in SQLite."""
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    total = len(req.correct_answers)
    correct_count = 0
    for i in range(min(len(req.user_answers), total)):
        if req.user_answers[i] == req.correct_answers[i]:
            correct_count += 1

    percentage = round((correct_count / total) * 100) if total > 0 else 0

    # Real XP formula: 10 XP per correct answer + 25 XP for 100% mastery
    earned_xp = correct_count * 10
    if percentage == 100:
        earned_xp += 25

    if user.daily_xp + earned_xp > user.daily_cap:
        actual_added = max(0, user.daily_cap - user.daily_xp)
    else:
        actual_added = earned_xp

    user.daily_xp += actual_added
    user.xp += actual_added
    user.quizzes_taken += 1

    # Overclock detection
    is_rushed = req.time_taken_seconds < 25 and percentage < 50

    # Call Knowledge Tracing Model Hook
    history_sample = [{"score": correct_count, "total": total, "topic": req.topic}]
    model_estimate = estimate_level(history_sample)

    # Record progress in database
    progress = LessonProgress(
        user_id=user.id,
        subject=req.subject,
        topic=req.topic,
        completed=True,
        quiz_score=correct_count,
        duration_seconds=req.time_taken_seconds
    )
    db.add(progress)

    # Log real activity
    log = ActivityLog(
        user_id=user.id,
        activity_type="quiz",
        title=f"Quiz: {req.topic} ({req.subject})",
        xp_earned=actual_added,
        details=f"Scored {correct_count}/{total} ({percentage}%) • Level: {model_estimate['level']}"
    )
    db.add(log)
    db.commit()

    return {
        "score": correct_count,
        "total": total,
        "percentage": percentage,
        "xp_earned": actual_added,
        "total_xp": user.xp,
        "level": model_estimate["level"],
        "feedback": model_estimate["recommendation"],
        "is_rushed": is_rushed
    }

@app.post("/api/document/summarize")
async def summarize_document(
    user_id: int = Form(1),
    file: Optional[UploadFile] = File(None),
    text_content: Optional[str] = Form(None),
    target_lang: str = Form("en"),
    db: Session = Depends(get_db)
):
    """Extracts text from PDF or text notes, summarizes into chosen language, records in DB, awards real XP."""
    extracted_text = ""
    filename = "Study Notes"

    if file:
        filename = file.filename
        content = await file.read()
        try:
            if filename.lower().endswith(".pdf"):
                doc = pymupdf.open(stream=content, filetype="pdf")
                for page in doc:
                    extracted_text += page.get_text() + "\n"
            else:
                try:
                    extracted_text = content.decode("utf-8")
                except Exception:
                    extracted_text = content.decode("latin-1", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read document: {str(e)}")
    elif text_content:
        extracted_text = text_content.strip()

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in document.")

    sample_text = extracted_text[:4000]
    target_lang_name = SUPPORTED_LANGUAGES.get(target_lang, {}).get("name", "English")

    prompt = f"""
You are an expert CBSE educational summarizer and translator.
A student uploaded a study document: "{filename}".
Content snippet:
{sample_text}

Task:
1. Detect original language.
2. Produce a clear, high-yield summary in {target_lang_name} ({target_lang}).
3. Extract 4 key terms with definitions in {target_lang_name}.
4. Generate a 5-question multiple choice quiz on this document in {target_lang_name}.

Return ONLY valid JSON matching this schema:
{{
  "detected_language": "Language name",
  "document_title": "{filename}",
  "summary": "Clear 3-paragraph summary in {target_lang_name}",
  "key_terms": [
    {{"term": "Term 1", "definition": "Definition in {target_lang_name}"}},
    {{"term": "Term 2", "definition": "Definition in {target_lang_name}"}}
  ],
  "quiz": [
    {{
      "id": 1,
      "question": "Question in {target_lang_name}?",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "Explanation in {target_lang_name}"
    }}
  ]
}}
"""
    raw_ai = call_gemini(prompt)
    try:
        data = clean_json_response(raw_ai)
    except Exception:
        data = {
            "detected_language": "English",
            "document_title": filename,
            "summary": raw_ai,
            "key_terms": [{"term": "Key Point", "definition": "Summary of uploaded content."}],
            "quiz": []
        }

    # Save to database
    doc_record = DocumentSummary(
        user_id=user_id,
        filename=filename,
        detected_language=data.get("detected_language", "en"),
        target_language=target_lang,
        summary=data.get("summary", ""),
        key_terms=json.dumps(data.get("key_terms", [])),
        quiz_json=json.dumps(data.get("quiz", []))
    )
    db.add(doc_record)

    # Award real XP for uploading & reading notes
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.xp += 10
        user.daily_xp += 10
        log = ActivityLog(
            user_id=user.id,
            activity_type="document",
            title=f"Summarized: {filename}",
            xp_earned=10,
            details=f"Target Language: {target_lang_name}"
        )
        db.add(log)

    db.commit()
    return data

@app.get("/api/document/history")
def get_document_history(user_id: int, db: Session = Depends(get_db)):
    """Fetches previously summarized documents for the user."""
    docs = db.query(DocumentSummary).filter(DocumentSummary.user_id == user_id).order_by(DocumentSummary.created_at.desc()).limit(10).all()
    result = []
    for d in docs:
        try:
            kt = json.loads(d.key_terms) if d.key_terms else []
        except Exception:
            kt = []
        try:
            qz = json.loads(d.quiz_json) if d.quiz_json else []
        except Exception:
            qz = []
        result.append({
            "id": d.id,
            "filename": d.filename,
            "detected_language": d.detected_language,
            "target_language": d.target_language,
            "summary": d.summary,
            "key_terms": kt,
            "quiz": qz,
            "created_at": d.created_at.strftime("%b %d, %H:%M") if d.created_at else ""
        })
    return result

@app.get("/api/user/completed-topics")
def get_completed_topics(user_id: int, db: Session = Depends(get_db)):
    """Fetches list of completed topics for the student."""
    records = db.query(LessonProgress.topic).filter(
        LessonProgress.user_id == user_id,
        LessonProgress.completed == True
    ).distinct().all()
    return [r[0] for r in records]

@app.get("/api/teacher/overview")
def get_teacher_overview(classroom: str = "CBSE Class 10 - Section A", db: Session = Depends(get_db)):
    """Returns analytics for teachers: student performance, average XP, recent submissions."""
    students = db.query(User).filter(User.classroom == classroom, User.role == "student").all()
    total_students = len(students)
    total_xp = sum(s.xp for s in students)
    avg_xp = round(total_xp / total_students) if total_students > 0 else 0
    total_lessons = sum(s.completed_lessons for s in students)
    total_quizzes = sum(s.quizzes_taken for s in students)

    # Recent student activity in this classroom
    student_ids = [s.id for s in students]
    recent_logs = db.query(ActivityLog).filter(ActivityLog.user_id.in_(student_ids)).order_by(ActivityLog.created_at.desc()).limit(15).all() if student_ids else []

    user_map = {s.id: s.name for s in students}
    activities_feed = [
        {
            "id": log.id,
            "student_name": user_map.get(log.user_id, "Student"),
            "activity_type": log.activity_type,
            "title": log.title,
            "xp_earned": log.xp_earned,
            "details": log.details,
            "time": log.created_at.strftime("%b %d, %H:%M") if log.created_at else ""
        }
        for log in recent_logs
    ]

    return {
        "classroom": classroom,
        "total_students": total_students,
        "avg_xp": avg_xp,
        "total_lessons_completed": total_lessons,
        "total_quizzes_completed": total_quizzes,
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "xp": s.xp,
                "streak": s.streak,
                "completed_lessons": s.completed_lessons,
                "quizzes_taken": s.quizzes_taken
            }
            for s in sorted(students, key=lambda x: x.xp, reverse=True)
        ],
        "recent_activities": activities_feed
    }

@app.get("/api/leaderboard")
def get_leaderboard(classroom: str = "CBSE Class 10 - Section A", db: Session = Depends(get_db)):
    """Returns real leaderboard of all registered students in the classroom ranked by actual XP."""
    students = db.query(User).filter(User.classroom == classroom, User.role == "student").order_by(User.xp.desc()).all()
    rankings = []
    for idx, s in enumerate(students):
        rankings.append({
            "rank": idx + 1,
            "id": s.id,
            "name": s.name,
            "xp": s.xp,
            "streak": s.streak,
            "completed_lessons": s.completed_lessons,
            "quizzes_taken": s.quizzes_taken
        })
    return {"classroom": classroom, "leaderboard": rankings}

@app.post("/api/user/reset")
def reset_user_progress(req: ResetUserRequest, db: Session = Depends(get_db)):
    """Resets all XP, daily streak, completed lessons, and quizzes for a student to start completely fresh."""
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.xp = 0
    user.daily_xp = 0
    user.streak = 1
    user.completed_lessons = 0
    user.quizzes_taken = 0
    user.last_active_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Clear individual history
    db.query(LessonProgress).filter(LessonProgress.user_id == req.user_id).delete()
    db.query(ActivityLog).filter(ActivityLog.user_id == req.user_id).delete()

    # Add fresh enrollment log
    log = ActivityLog(
        user_id=user.id,
        activity_type="joined",
        title="Fresh Start in EduPulse Classroom",
        xp_earned=0,
        details=f"Progress reset. Ready to earn fresh XP in {user.classroom}"
    )
    db.add(log)
    db.commit()
    db.refresh(user)

    return {
        "message": "User stats reset successfully.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "classroom": user.classroom,
            "preferred_lang": user.preferred_lang,
            "xp": user.xp,
            "streak": user.streak,
            "daily_xp": user.daily_xp,
            "daily_cap": user.daily_cap,
            "completed_lessons": user.completed_lessons,
            "quizzes_taken": user.quizzes_taken
        }
    }

@app.post("/api/classroom/reset")
def reset_classroom_leaderboard(req: ResetClassroomRequest, db: Session = Depends(get_db)):
    """Resets all student stats in the classroom to 0 for a fresh competition."""
    classroom_name = req.classroom or "CBSE Class 10 - Section A"
    students = db.query(User).filter(User.classroom == classroom_name, User.role == "student").all()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for s in students:
        s.xp = 0
        s.daily_xp = 0
        s.streak = 1
        s.completed_lessons = 0
        s.quizzes_taken = 0
        s.last_active_date = today_str

    student_ids = [s.id for s in students]
    if student_ids:
        db.query(LessonProgress).filter(LessonProgress.user_id.in_(student_ids)).delete(synchronize_session=False)
        db.query(ActivityLog).filter(ActivityLog.user_id.in_(student_ids)).delete(synchronize_session=False)
        for s in students:
            db.add(ActivityLog(
                user_id=s.id,
                activity_type="joined",
                title="Classroom Reset: Fresh Competition",
                xp_earned=0,
                details=f"Leaderboard reset to 0 for all students"
            ))

    db.commit()
    return {"message": "Classroom leaderboard and stats reset successfully to 0."}

@app.post("/api/tts")
async def generate_tts(req: TTSRequest):
    """High-fidelity Text-To-Speech using edge-tts with native Indian regional accents."""
    voice = SUPPORTED_LANGUAGES.get(req.language, {}).get("voice", "en-IN-NeerjaNeural")
    clean_text = req.text[:1200]

    async def audio_stream():
        communicate = edge_tts.Communicate(clean_text, voice)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")

@app.post("/api/doubt/resolve")
def resolve_doubt(req: DoubtRequest):
    """Friendly doubt clarifier triggered by attention pause or student query."""
    lang_name = SUPPORTED_LANGUAGES.get(req.language, {}).get("name", "English")
    query = req.doubt_text or "Explain the key idea in very simple, intuitive words with a 1-sentence takeaway."

    prompt = f"""
A CBSE student was studying {req.subject}: "{req.topic}".
Their question / area of confusion: "{query}"
Target Language: {lang_name} ({req.language})

Respond like a kind, supportive tutor directly in {lang_name}.
Keep it concise, clear, and reassuring (maximum 2-3 short paragraphs).
End with an encouraging sentence: "You've got this! Let's continue."
"""
    clarification = call_gemini(prompt)
    return {
        "subject": req.subject,
        "topic": req.topic,
        "explanation": clarification
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"Starting EduPulse API server on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)


