# PlacementPrep AI — v2

> An AI-powered interview prep platform that generates personalized study plans, runs proctored mock interviews, evaluates code in real-time, and tracks your progress — all tailored to your target company and role.

---

## Features

| Module | What it does |
|---|---|
| **Onboarding** | Collects your target company, role, interview date, daily hours, and resume to build a personalized prep profile |
| **AI Study Plan** | Generates a from-scratch day-by-day curriculum covering DSA phases, system design, and behavioral prep — not based on judging your current skill level, but building you up comprehensively |
| **Mock Interview** | Proctored, chat-based, 30-minute interview with camera on. AI reads your resume in full and asks deep questions about everything on it, plus injects company-specific historical question patterns. Fully conversational — follows up on specific words and claims in your answers |
| **Coding Simulator** | Monaco-based code editor with Judge0 execution — solve problems and get instant AI feedback |
| **Analytics Dashboard** | Track interview scores, problems solved, topic mastery, and daily streaks with interactive charts |
| **Resume Parser** | Upload your PDF resume — projects, experience, skills, and education are all extracted and used to drive the mock interview |
| **Google Calendar Sync** | Add your interview date directly to Google Calendar |
| **Google OAuth** | One-click sign-in via Google with JWT session management |

---

## How the Mock Interview Works

The mock interview is a single unified round — no separate technical, behavioral, or full round options. It covers everything in one natural conversation the way real interviews work.

**Flow:**
1. Click "Start a mock interview" → confirm rules (30 min, camera on, no copy-paste, no tab switching)
2. Camera is verified live (never recorded or uploaded — local preview only)
3. AI opens with a background question and then follows the thread from your answers
4. AI listens for keywords: if you mention a technology, a metric, a design decision, or a vague claim — it follows up on it immediately before moving on
5. 2–3 follow-up questions per topic, then pivot. If you're stuck, AI acknowledges it and moves on
6. Timer hits zero → debrief is generated automatically from the full 30-minute conversation

**Debrief includes:**
- Overall score (0–100) and verdict (Strong Hire / Hire / Borderline / No Hire)
- Topic-by-topic breakdown with specific references to what you said
- Recruiter-ready summary — honest about strengths and gaps
- Top 2 actionable areas to work on, tied to what actually came up

The evaluation bar is high because the competition is real — 75+ means genuinely interview-ready. Below 60 means significant preparation is still needed. Scores are calibrated, not inflated.

---

## How the Study Plan Works

When you set your interview date, the AI generates a comprehensive from-scratch curriculum for your exact timeframe — not a judgment of your current skill level. It covers:

- All DSA phases: arrays → linked lists → trees → graphs → dynamic programming → system design
- Company-specific overlays (Google weights graphs/DP, Amazon weights behavioral/leadership principles, etc.)
- Behavioral prep and mock test checkpoints built into the schedule
- Daily task count adjusts to your available hours per day

Falls back to a static curriculum engine if AI generation fails, ensuring you always get a plan.

---

## Tech Stack

### Frontend
- **React 18** + **Vite**
- **Framer Motion** — page transitions and micro-animations
- **Monaco Editor** — VS Code-grade code editor
- **Recharts** — analytics charts
- **Zustand** — global state management
- **React Router v6** — client-side routing
- **ReactMarkdown** — renders AI debrief output

### Backend
- **FastAPI** — async Python API
- **SQLAlchemy 2.0** (async) + **asyncpg** — PostgreSQL ORM
- **Alembic** — database migrations
- **Redis** — rate limiting and caching
- **Google Generative AI (Gemini)** / **OpenAI** — mock interviews, study plans, feedback
- **Judge0 CE** — sandboxed code execution
- **pdfplumber** — resume PDF extraction

### Infrastructure
- **Docker Compose** — one-command local dev (PostgreSQL 16 + Redis 7 + backend)
- **JWT Auth** — access + refresh token flow with Google OAuth
- **Vercel** — frontend deployment (auto-deploys on push to `main`)

---

## Getting Started

### Prerequisites

- Node.js ≥ 18
- Python ≥ 3.11
- Docker + Docker Compose
- API key for Google Gemini or OpenAI
- (Optional) Judge0 API key for code execution
- (Optional) Google OAuth credentials

### 1. Clone

```bash
git clone https://github.com/aaronaroraa/placementprep-v2.git
cd placementprep-v2
```

### 2. Environment variables

```bash
cp .env.example .env
# Fill in your API keys and secrets
```

Key variables:
```
LLM_PROVIDER=gemini           # or openai
GEMINI_API_KEY=...
OPENAI_API_KEY=...
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
JWT_SECRET=...
```

### 3. Start infrastructure

```bash
docker-compose up -d
```

Spins up PostgreSQL 16 on `localhost:5432`, Redis 7 on `localhost:6379`, and the FastAPI backend on `localhost:8000` with hot reload.

### 4. Run database migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

App is live at **http://localhost:5173**

---

## Project Structure

```
placementprep-v2/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Environment & settings
│   │   ├── auth.py                  # JWT + OAuth utilities
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── routers/
│   │   │   ├── auth.py              # Auth endpoints
│   │   │   ├── users.py             # Profile & progress
│   │   │   └── main_routers.py      # Curriculum, coding, mock interview
│   │   └── services/
│   │       ├── ai_service.py        # LLM integration (interview, plan, feedback)
│   │       ├── prep_engine.py       # Study plan generation
│   │       ├── cache.py             # Redis caching layer
│   │       ├── code_executor.py     # Judge0 client
│   │       ├── resume_parser.py     # PDF extraction
│   │       └── calendar_service.py  # Google Calendar API
│   ├── migrations/                  # Alembic migration files
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Landing.jsx          # Marketing page
│   │   │   ├── Dashboard.jsx        # Daily tasks + plan overview
│   │   │   ├── Plan.jsx             # Full study roadmap
│   │   │   ├── Coding.jsx           # Code editor + problems
│   │   │   ├── Interviews.jsx       # Interview history + scores
│   │   │   ├── InterviewRoom.jsx    # Live proctored interview flow
│   │   │   └── Analytics.jsx        # Charts + progress tracking
│   │   ├── components/
│   │   ├── stores/
│   │   └── api/
│   ├── vercel.json
│   └── vite.config.js
├── seed/
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register with email/password |
| `POST` | `/api/auth/login` | Login |
| `GET` | `/api/auth/google` | Google OAuth |
| `GET` | `/api/users/me` | Current user profile |
| `PUT` | `/api/users/me` | Update profile |
| `POST` | `/api/plan/generate` | Generate AI study plan |
| `GET` | `/api/plan/today` | Today's tasks |
| `POST` | `/api/coding/submit` | Submit code for execution |
| `POST` | `/api/mock/start` | Start a mock interview session |
| `POST` | `/api/mock/chat` | Send a message / get next question |
| `GET` | `/api/mock/history` | Past interview attempts |
| `POST` | `/api/resume/upload` | Upload and parse resume |

---

## Company Support

The mock interview and study plan have specific tuning for:

| Company | Interview Focus | Question Bank |
|---------|----------------|---------------|
| Google | Graphs, DP, system design at scale | Autocomplete, PageRank, distributed KV store |
| Amazon | Leadership Principles (every behavioral answer maps to an LP) | Order fulfillment, rate limiter, recommendation engine |
| Microsoft | OOP, collaboration, clarity | Teams real-time collab, Git from scratch, OneDrive |
| Meta | Move fast, scale thinking | News Feed ranking, Instagram Stories, hate speech detection |
| Flipkart | Flash sales, inventory, payments | 100k orders/min, real-time inventory, fraud detection |
| Others | General system design + behavioral | URL shortener, chat app, CDN, notification service |

---

## Local Development (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Make sure PostgreSQL and Redis are running locally and configured in `.env`.

---

## Deployment

The frontend is deployed on **Vercel** and auto-deploys on every push to `main`. The `frontend/vercel.json` handles SPA routing (all paths → `index.html`).

The backend requires a Python runtime with PostgreSQL and Redis — deploy to Railway, Render, or any server running Docker.

---

## License

Personal / educational use.
