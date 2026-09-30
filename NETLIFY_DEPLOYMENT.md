# 🚀 Hosting EduPulse on Netlify

EduPulse is now fully configured and optimized to be deployed to **Netlify**!

---

## ⚡ Option 1: Instant Drag-and-Drop (Zero Setup, 1 Minute)

1. Open a terminal and run the production build (already pre-built for you):
   ```bash
   cd frontend
   npm run build
   ```
2. Go to your [Netlify Dashboard](https://app.netlify.com/drop).
3. Drag and drop the `frontend/dist` folder into the Netlify Drop area.
4. Your site is instantly live with a public `*.netlify.app` URL!

---

## ⚡ Option 2: Deploy from GitHub on Netlify

1. Push your repository to GitHub.
2. In Netlify, click **"Add new site"** &rarr; **"Import an existing project"** &rarr; **GitHub**.
3. Choose the repository and use these build settings (pre-configured in [netlify.toml](file:///c:/Users/Lenovo/Downloads/Error404/netlify.toml)):
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `dist`
4. *(Optional Backend Connection)*:
   - If you host the FastAPI backend on **Render**, **Railway**, or **Fly.io**, add the environment variable in Netlify:
     - `VITE_API_URL`: `https://your-backend-service.onrender.com`
   - If no backend is connected, EduPulse runs in **Autonomous Showcase Mode** with full offline CBSE curriculum, checkpoint quizzes, scoring, leaderboard, and eye tracking enabled!

---

## 🔑 Demo Login Credentials
- **Student Account**: `aarav@cbse.edu` | Password: `password123`
- **Teacher Account**: `teacher@cbse.edu` | Password: `password123`
- **Instant Guest**: Click the **"Explore as Guest (Instant 1-Click Entry)"** button on the login screen to enter immediately without typing anything!
