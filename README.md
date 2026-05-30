# 🎯 PlacementPrep AI — v2

> **Your AI-powered FAANG placement coach.** A full-stack platform that builds personalized study plans, runs pure-voice mock interviews, evaluates code in real-time, and tracks your progress — all tailored to the companies you're targeting.

---

## ✨ Features

| Module | What it does |
|---|---|
| **Onboarding** | Collects your target companies, experience level, and resume to build a personalized prep roadmap |
| **Curriculum Engine** | Generates a day-by-day study plan covering DSA, system design, and behavioral topics |
| **Coding Simulator** | Monaco-based editor with Judge0 code execution — solve problems and get instant feedback |
| **Voice Mock Interviews** | Pure audio-first interview experience powered by Google Gemini / OpenAI to simulate real FAANG rounds |
| **Theory Lessons** | AI-generated theory content aligned to your current day in the curriculum |
| **Analytics Dashboard** | Track problems solved, interview scores, topic mastery, and daily streaks with interactive charts |
| **Google OAuth** | One-click sign-in via Google with JWT-based session management |
| **Resume Parser** | Upload your resume (PDF) and let AI extract key skills to inform your prep plan |
| **Google Calendar Sync** | Schedule study sessions and interviews directly into your Google Calendar |

---

## 🏗️ Tech Stack

### Frontend
- **React 18** + **Vite** — fast dev server and optimized builds
- **Tailwind CSS** — utility-first styling
- **Framer Motion** — smooth page transitions and micro-animations
- **Monaco Editor** — VS Code-grade code editor in the browser
- **Recharts** — interactive analytics charts
- **Zustand** — lightweight global state management
- **React Router v6** — client-side routing with animated transitions

### Backend
- **FastAPI** — async Python API framework
- **SQLAlchemy 2.0** (async) + **asyncpg** — PostgreSQL ORM with async support
- **Alembic** — database migrations
- **Redis** — caching and session management
- **Google Generative AI (Gemini)** — AI-powered interviews, theory, and feedback
- **OpenAI** — alternative LLM provider
- **Judge0 CE** — sandboxed code execution engine
- **pdfplumber** — resume PDF extraction

### Infrastructure
- **Docker Compose** — one-command local dev environment (PostgreSQL 16, Redis 7, backend)
- **JWT Auth** — access + refresh token flow with Google OAuth integration

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.11
- **Docker** & **Docker Compose** (recommended)
- API keys for **Google Gemini** or **OpenAI**
- (Optional) **Judge0** API key for code execution
- (Optional) **Google OAuth** credentials for sign-in

### 1. Clone the repo

```bash
git clone https://github.com/aaronaroraa/placementprep-v2.git
cd placementprep-v2
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys and secrets
```

### 3. Start the infrastructure (Database + Redis + Backend)

```bash
docker-compose up -d
```

This spins up:
- **PostgreSQL 16** on `localhost:5432`
- **Redis 7** on `localhost:6379`
- **FastAPI backend** on `localhost:8000` (with hot reload)

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be live at **http://localhost:5173**

---

## 📁 Project Structure

```
placementprep-v2/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Environment & app settings
│   │   ├── database.py          # Async SQLAlchemy engine setup
│   │   ├── auth.py              # JWT + OAuth utilities
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── routers/
│   │   │   ├── auth.py          # Auth endpoints (login, register, OAuth)
│   │   │   ├── users.py         # User profile & progress endpoints
│   │   │   └── main_routers.py  # Core API (curriculum, coding, interviews)
│   │   └── services/
│   │       ├── ai_service.py       # Gemini / OpenAI integration
│   │       ├── prep_engine.py      # Curriculum generation logic
│   │       ├── code_executor.py    # Judge0 code execution client
│   │       ├── resume_parser.py    # PDF resume extraction
│   │       └── calendar_service.py # Google Calendar API integration
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Root component with routing
│   │   ├── pages/
│   │   │   ├── Landing.jsx      # Marketing landing page
│   │   │   ├── Auth.jsx         # Login / Register / OAuth callback
│   │   │   ├── Onboarding.jsx   # Target company & skill setup
│   │   │   ├── Dashboard.jsx    # Main dashboard with daily tasks
│   │   │   ├── Plan.jsx         # Full curriculum roadmap view
│   │   │   ├── Coding.jsx       # Code editor + problem solving
│   │   │   ├── MockInterview.jsx # Voice-first mock interview UI
│   │   │   └── Analytics.jsx    # Progress charts & insights
│   │   ├── components/          # Shared UI components
│   │   ├── stores/              # Zustand state stores
│   │   └── api/                 # Axios API client
│   ├── package.json
│   └── vite.config.js
├── seed/                        # Seed data (companies, coding problems)
│   ├── companies.json
│   ├── coding_problems.json
│   └── company_profiles/
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## 🔌 API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Login with email/password |
| `GET` | `/api/auth/google` | Initiate Google OAuth flow |
| `GET` | `/api/auth/google/callback` | Handle OAuth callback |
| `GET` | `/api/users/me` | Get current user profile |
| `PUT` | `/api/users/me` | Update user profile |
| `POST` | `/api/curriculum/generate` | Generate a personalized study plan |
| `GET` | `/api/curriculum/today` | Get today's tasks |
| `POST` | `/api/coding/submit` | Submit code for execution |
| `POST` | `/api/interview/start` | Start a mock interview session |
| `POST` | `/api/resume/upload` | Upload and parse a resume |

---

## 🧑‍💻 Development

### Running backend locally (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> Make sure PostgreSQL and Redis are running and configured in `.env`

### Building for production

```bash
# Frontend
cd frontend
npm run build    # Output in dist/

# Backend — served via Docker or any ASGI server
```

---

## 📄 License

This project is for personal/educational use.

---

<p align="center">
  Built with ❤️ to crack FAANG interviews
</p>
