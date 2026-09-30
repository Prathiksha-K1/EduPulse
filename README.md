# EduPulse - AI Self-Learning Platform for CBSE Students

**EduPulse** is a full-featured, AI-powered study companion designed for CBSE students (Class 10/12) in **Mathematics, Physics, Chemistry, and English**. It is built like a "Duolingo for studies" with gamified learning, streaks, XP rewards, a classroom leaderboard, an on-device webcam attention tracker, a side document summarizer, and full multilingual support in **English, Tamil (தமிழ்), Hindi (हिन्दी), and Telugu (తెలుగు)**.

---

## 🌟 Key Features Across All 7 Phases

1. **CBSE Subjects & Curriculum** (Phase 1 & 3):
   - Comprehensive modules for **Mathematics**, **Physics**, **Chemistry**, and **English**.
   - Real-time lessons powered by Google Gemini (`gemini-3.5-flash-lite`).
   - High-yield key concepts, real-world examples, and exam tips.

2. **Text-To-Speech Audio Lectures** (Phase 3):
   - In-browser Web Speech API audio with background fallback to `edge-tts`.
   - Native accent voices for English (`en-IN`), Tamil (`ta-IN`), Hindi (`hi-IN`), and Telugu (`te-IN`).

3. **Duolingo-Style Gamification** (Phase 4):
   - **Daily Streaks** (🔥 tracking consecutive days of study).
   - **XP Point System** (+10 XP per quiz question, +25 XP bonus for 100% score).
   - **Anti-Gaming Daily XP Cap** (prevents spamming).
   - **Classroom Leaderboard** with student ranks and gold/silver/bronze badges.

4. **Interactive 5-Question Checkpoint Quizzes & Grading** (Phase 2):
   - Auto-generated 5-question multiple choice quizzes based on any topic or uploaded notes.
   - Real-time grading with detailed answer explanations.
   - Knowledge tracing level estimation (**Beginner**, **Intermediate**, **Advanced**).

5. **Private On-Device Webcam Attention Tracking** (Phase 5):
   - Camera viewport on the left side of the screen with active focus meter (0-100%).
   - Blinking and momentary glances are smoothed out.
   - If the student is distracted or looking away continuously for **> 10 seconds**:
     - Automatically pauses the audio lecture.
     - Pops up a gentle notification: *"Do you have a doubt, or didn't you understand?"*
     - Quick actions to resume, get a simpler 2-paragraph concept breakdown, or take a 2-minute break.
   - **100% Privacy Guarantee**: Video frames never leave the browser.

6. **Adaptive Study Rules & Anti-Rushing** (Phase 6):
   - Detects if a student rushes through a quiz (< 25s) with a low score (< 50%) and prompts them to review.
   - Clean pluggable model hook in `backend/knowledge_tracing.py` (`estimate_level(history)`) with an Elo-based IRT algorithm.
   - Kaggle-ready deep learning training notebook located at `training/knowledge_tracing.ipynb`.

7. **Side Column PDF Summarizer** (Phase 1):
   - Dedicated right column to upload any chapter PDF or paste notes.
   - PyMuPDF text extraction with Gemini summarization into any chosen language.
   - Extracts 4 key glossary terms and generates a custom 5-question quiz directly from the PDF.

8. **Complete 4-Language Translation** (Phase 7):
   - Full UI and generated lessons/quizzes/summaries switch instantly between **English**, **Tamil**, **Hindi**, and **Telugu**.

---

## 📁 Project Architecture

```text
EduPulse/
├── backend/
│   ├── .env                    # GEMINI_API_KEY, PORT=8001, DATABASE_URL
│   ├── .env.example            # Environment template
│   ├── database.py             # SQLite connection & SQLAlchemy Base
│   ├── edupulse.db             # SQLite database (stores user XP, documents, quizzes)
│   ├── knowledge_tracing.py    # Pluggable model hook & Elo level estimator
│   ├── main.py                 # FastAPI backend, CBSE endpoints, Gemini prompts, TTS
│   ├── models.py               # SQLAlchemy User, DocumentSummary, LessonProgress models
│   ├── requirements.txt        # Backend dependencies
│   └── venv/                   # Python virtual environment
│
├── frontend/
│   ├── package.json            # React 19, Lucide, Tailwind CSS
│   ├── vite.config.js          # Vite configuration with proxy to port 8001
│   └── src/
│       ├── App.jsx             # 3-column EduPulse study interface
│       ├── index.css           # Styling and font configuration
│       └── main.jsx            # React root mount
│
├── training/
│   └── knowledge_tracing.ipynb # Kaggle-ready PyTorch Deep Knowledge Tracing notebook
│
├── .gitignore                  # Ignores .env, venv/, node_modules/, *.db
└── README.md                   # Complete documentation
```

---

## 🚀 Running on Windows

### 1. Backend Server (FastAPI on Port 8001)

Open a PowerShell terminal in the project root:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --app-dir . --reload
```
*API documentation is available at [http://localhost:8001/docs](http://localhost:8001/docs).*

### 2. Frontend Development Server (Vite on Port 5173)

Open a second PowerShell terminal in the project root:
```powershell
cd frontend
npm run dev
```
*Frontend application is available at [http://localhost:5173](http://localhost:5173).*

---

## 🧪 How to Test Every Feature in the UI

1. **Select a CBSE Subject & Topic**:
   - In the left column, click **Mathematics**, **Physics**, **Chemistry**, or **English**.
   - Click any subtopic (e.g. *Light: Reflection, Refraction & Lens Formula*).
   - Notice the lesson updates with summary, key concepts, real-world examples, and exam tips.

2. **Listen to Lecture (Text-to-Speech)**:
   - Click **"Listen to Lecture"** to hear the audio read aloud in the selected language.

3. **Take Checkpoint Quiz & Earn XP**:
   - Click **"Take Checkpoint Quiz"**.
   - Answer the 5 multiple choice questions.
   - Click **"Submit Answers & Earn XP"**.
   - Notice your XP updates in the top bar, your rank updates on the leaderboard, and your estimated level is displayed.

4. **Test the Webcam Attention Tracker**:
   - In the left column, click **"Enable Focus Camera"** and allow browser camera permissions.
   - Look straight ahead to observe the green *Attentive & Focused* status and attention score.
   - If inattention continues for > 10 seconds, the gentle doubt pop-up appears asking if you have a doubt or need a simpler explanation!

5. **Test Side Document Upload**:
   - In the right column, choose any PDF file (or paste textbook notes into the text area).
   - Click **"Summarize & Create Quiz"**.
   - Review the summary and glossary terms, then click **"Take Quiz on this Document"**.

6. **Switch Languages**:
   - In the top navigation bar, change the language to **தமிழ்**, **हिन्दी**, or **తెలుగు**.
   - All navigation items, buttons, subjects, quizzes, and lessons will display in that language.

---

## ☁️ Deployment Guide (Free Hosting: Vercel + Render)

### Deploying the Backend (Render Free Web Service)
1. Push your repository to GitHub (ensure `.env` is NOT committed).
2. Go to [Render.com](https://render.com/) and create a **New Web Service**.
3. Connect your GitHub repository:
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
   - `GEMINI_API_KEY`: *(Your Google AI Studio API key)*
   - `GEMINI_MODEL`: `gemini-3.5-flash-lite`

### Deploying the Frontend (Vercel)
1. Go to [Vercel.com](https://vercel.com/) and click **Add New Project**.
2. Connect your GitHub repository:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. In `frontend/vite.config.js`, update the production proxy to your Render backend URL (e.g. `https://eduplus-backend.onrender.com`).
4. Click **Deploy**.
