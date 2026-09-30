import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

def hash_pw(p):
    return hashlib.sha256(p.encode('utf-8')).hexdigest()

def seed():
    db_path = Path(__file__).resolve().parent / "edupulse.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Create tables if not present
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'student',
            classroom VARCHAR(100) DEFAULT 'CBSE Class 10 - Section A',
            preferred_lang VARCHAR(10) DEFAULT 'en',
            xp INTEGER DEFAULT 0,
            daily_xp INTEGER DEFAULT 0,
            daily_cap INTEGER DEFAULT 250,
            streak INTEGER DEFAULT 1,
            completed_lessons INTEGER DEFAULT 0,
            quizzes_taken INTEGER DEFAULT 0,
            last_active_date VARCHAR(20) DEFAULT '',
            created_at DATETIME
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            xp_earned INTEGER DEFAULT 0,
            details VARCHAR(255) DEFAULT '',
            created_at DATETIME
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject VARCHAR(50) NOT NULL,
            topic VARCHAR(150) NOT NULL,
            completed BOOLEAN DEFAULT 0,
            quiz_score INTEGER DEFAULT 0,
            duration_seconds INTEGER DEFAULT 0,
            created_at DATETIME
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS document_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename VARCHAR(255) NOT NULL,
            detected_language VARCHAR(50) DEFAULT 'en',
            target_language VARCHAR(10) DEFAULT 'en',
            summary TEXT NOT NULL,
            key_terms TEXT DEFAULT '[]',
            quiz_json TEXT DEFAULT '[]',
            created_at DATETIME
        )
    """)

    cur.execute("SELECT email FROM users")
    existing_emails = set(r[0] for r in cur.fetchall())

    # Fresh starting stats: 0 XP, 0 daily XP, 1 active day streak, 0 completed lessons, 0 quizzes
    users_to_add = [
        ('Aarav Sharma', 'aarav@cbse.edu', 'password123', 'student', 'CBSE Class 10 - Section A', 'en', 0, 0, 250, 1, 0, 0),
        ('Priya Patel', 'priya@cbse.edu', 'password123', 'student', 'CBSE Class 10 - Section A', 'en', 0, 0, 250, 1, 0, 0),
        ('Rohan Verma', 'rohan@cbse.edu', 'password123', 'student', 'CBSE Class 10 - Section A', 'en', 0, 0, 250, 1, 0, 0),
        ('Ananya Iyer', 'ananya@cbse.edu', 'password123', 'student', 'CBSE Class 10 - Section A', 'en', 0, 0, 250, 1, 0, 0),
        ('Vikram Singh', 'vikram@cbse.edu', 'password123', 'student', 'CBSE Class 10 - Section A', 'en', 0, 0, 250, 1, 0, 0),
        ('Mrs. Sunita Rao', 'teacher@cbse.edu', 'password123', 'teacher', 'CBSE Class 10 - Section A', 'en', 0, 0, 250, 1, 0, 0),
    ]

    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    for name, email, pw, role, classroom, lang, xp, daily_xp, cap, streak, comp_less, quiz_cnt in users_to_add:
        if email in existing_emails:
            cur.execute("""UPDATE users SET name=?, password_hash=?, role=?, classroom=?, preferred_lang=?, xp=?, daily_xp=?, daily_cap=?, streak=?, completed_lessons=?, quizzes_taken=?, last_active_date=? WHERE email=?""",
                        (name, hash_pw(pw), role, classroom, lang, xp, daily_xp, cap, streak, comp_less, quiz_cnt, today_str, email))
        else:
            cur.execute("""INSERT INTO users (name, email, password_hash, role, classroom, preferred_lang, xp, daily_xp, daily_cap, streak, completed_lessons, quizzes_taken, last_active_date, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (name, email, hash_pw(pw), role, classroom, lang, xp, daily_xp, cap, streak, comp_less, quiz_cnt, today_str, now_str))

    conn.commit()

    # Clear old activity logs, lesson progress, and summaries for a completely fresh start
    cur.execute("DELETE FROM activity_logs")
    cur.execute("DELETE FROM lesson_progress")
    cur.execute("DELETE FROM document_summaries")

    cur.execute("SELECT id, name FROM users WHERE role = 'student'")
    student_rows = cur.fetchall()

    # Add fresh enrollment activity
    for s_id, s_name in student_rows:
        cur.execute("""INSERT INTO activity_logs (user_id, activity_type, title, xp_earned, details, created_at) VALUES (?, ?, ?, ?, ?, ?)""",
                    (s_id, 'joined', 'Enrolled in EduPulse Classroom', 0, 'Classroom: CBSE Class 10 - Section A', now_str))

    conn.commit()
    conn.close()
    print("EduPulse clean reset and seed completed successfully!")

if __name__ == '__main__':
    seed()

