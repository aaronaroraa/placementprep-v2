"""All remaining routers: resume, coding, chat, mock_interview, analytics"""
import uuid, os, aiofiles
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import (User, Resume, Problem, CodeSubmission, ChatSession,
                        MockInterview, PerformanceMetric, ImprovementTrend)
from app.auth import get_current_user
from app.services.resume_parser import parse_resume
from app.services.code_executor import execute_code, STARTER_CODE, estimate_complexity
from app.services.ai_service import (interviewer_response, coach_response,
                                     flashcard_response, mock_interview_response,
                                     mock_interview_chat,
                                     generate_resume_interview_questions,
                                     extract_score_from_evaluation, extract_verdict_from_score,
                                     build_chat_system, stream_ai)
from app.services.cache import rate_limit, cache_get, cache_set
from app.config import settings
from fastapi.responses import StreamingResponse

# ── Resume ────────────────────────────────────────────────────────────────────
resume_router = APIRouter(prefix="/resume", tags=["resume"])

@resume_router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not (file.filename or "").endswith(".pdf"):
        raise HTTPException(400, "PDF only")
    content = await file.read()
    if len(content) > settings.MAX_RESUME_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"Max {settings.MAX_RESUME_SIZE_MB}MB")
    os.makedirs(settings.RESUME_UPLOAD_DIR, exist_ok=True)

    # Clean up this user's previous resume files from disk to avoid unbounded growth.
    old_r = await db.execute(select(Resume).where(Resume.user_id == user.id))
    for old in old_r.scalars().all():
        if old.file_path and os.path.exists(old.file_path):
            try: os.remove(old.file_path)
            except OSError: pass
    fid = uuid.uuid4()
    path = os.path.join(settings.RESUME_UPLOAD_DIR, f"{fid}_{file.filename}")
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)
    parsed = await parse_resume(content, file.filename or "resume.pdf", user.target_role)
    resume = Resume(id=uuid.uuid4(), user_id=user.id, file_path=path, file_name=file.filename or "resume.pdf",
                    raw_text=parsed["raw_text"], parsed_data=parsed["parsed_data"],
                    skills_extracted=parsed["skills_extracted"], projects_extracted=parsed["projects_extracted"],
                    experience_extracted=parsed["experience_extracted"], education_extracted=parsed["education_extracted"],
                    skill_gaps=parsed["skill_gaps"], strengths=parsed["strengths"],
                    interview_questions=parsed["interview_questions"], analyzed_at=datetime.now(timezone.utc))
    db.add(resume)
    await db.flush()
    return {"resume_id": str(resume.id), **{k: parsed[k] for k in ["skills_extracted","projects_extracted","skill_gaps","strengths","interview_questions","parsed_data"]}}

@resume_router.get("/latest")
async def get_latest(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc()).limit(1))
    resume = r.scalar_one_or_none()
    if not resume: raise HTTPException(404, "No resume found")
    return {"resume_id": str(resume.id), "file_name": resume.file_name,
            "skills_extracted": resume.skills_extracted, "projects_extracted": resume.projects_extracted,
            "skill_gaps": resume.skill_gaps, "strengths": resume.strengths,
            "interview_questions": resume.interview_questions, "education_extracted": resume.education_extracted}

@resume_router.post("/generate-questions")
async def gen_questions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc()).limit(1))
    resume = r.scalar_one_or_none()
    if not resume: raise HTTPException(404, "No resume found")
    questions = await generate_resume_interview_questions(
        resume.projects_extracted or [], resume.experience_extracted or [],
        user.target_role or "SDE-1", user.target_company or "your target company",
        skills=resume.skills_extracted or [], education=resume.education_extracted or [],
    )
    resume.interview_questions = questions
    db.add(resume)
    await db.flush()
    return {"questions": questions}


# ── Coding ────────────────────────────────────────────────────────────────────
coding_router = APIRouter(prefix="/coding", tags=["coding"])

@coding_router.get("/problems")
async def list_problems(difficulty: Optional[str] = None, category: Optional[str] = None,
                        company: Optional[str] = None, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    # Problems are global and change rarely → cache the rendered list for 10 minutes.
    cache_key = f"problems:{difficulty or ''}:{category or ''}:{company or ''}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    q = select(Problem)
    if difficulty: q = q.where(Problem.difficulty == difficulty)
    if category: q = q.where(Problem.category == category)
    q = q.order_by(Problem.times_asked.desc()).limit(100)
    result = await db.execute(q)
    problems = result.scalars().all()
    if company:
        cl = company.lower()
        problems = [p for p in problems if cl in [t.lower() for t in (p.company_tags or [])]]
    payload = [{"id": str(p.id), "title": p.title,
                "difficulty": p.difficulty.value if hasattr(p.difficulty, "value") else p.difficulty,
                "category": p.category, "tags": p.tags, "company_tags": p.company_tags,
                "times_asked": p.times_asked, "optimal_complexity": p.optimal_complexity} for p in problems]
    await cache_set(cache_key, payload, ttl_seconds=600)
    return payload

@coding_router.get("/problems/{pid}")
async def get_problem(pid: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    try: problem_id = uuid.UUID(pid)
    except: raise HTTPException(400, "Invalid ID")
    r = await db.execute(select(Problem).where(Problem.id == problem_id))
    p = r.scalar_one_or_none()
    if not p: raise HTTPException(404, "Not found")
    sub_r = await db.execute(select(CodeSubmission).where(CodeSubmission.user_id == user.id, CodeSubmission.problem_id == problem_id).order_by(CodeSubmission.score.desc()).limit(1))
    best = sub_r.scalar_one_or_none()
    return {"id": str(p.id), "title": p.title, "description": p.description, "difficulty": p.difficulty,
            "category": p.category, "tags": p.tags, "constraints": p.constraints, "hints": p.hints,
            "test_cases": (p.test_cases or [])[:3], "optimal_complexity": p.optimal_complexity,
            "company_tags": p.company_tags, "role_tags": p.role_tags, "starter_code": STARTER_CODE,
            "user_best_score": best.score if best else None, "user_best_status": best.status if best else None}

class SubmitReq(BaseModel):
    problem_id: str
    code: str
    language: str

@coding_router.post("/submit")
async def submit(body: SubmitReq, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if body.language not in {"python","cpp","java","javascript"}: raise HTTPException(400,"Invalid language")
    try: pid = uuid.UUID(body.problem_id)
    except: raise HTTPException(400,"Invalid problem ID")
    r = await db.execute(select(Problem).where(Problem.id == pid))
    p = r.scalar_one_or_none()
    if not p: raise HTTPException(404,"Problem not found")
    result = await execute_code(body.code, body.language, {"id": str(p.id), "test_cases": p.test_cases or [], "optimal_complexity": p.optimal_complexity})
    sub = CodeSubmission(id=uuid.uuid4(), user_id=user.id, problem_id=pid, code=body.code, language=body.language,
                         status=result["status"], execution_time_ms=result["execution_time_ms"],
                         memory_used_kb=result["memory_used_kb"], test_results=result["test_results"],
                         tests_passed=result["tests_passed"], tests_total=result["tests_total"],
                         complexity_estimate=result["complexity_estimate"], edge_cases_handled=result["edge_cases_handled"],
                         score=result["score"], feedback=result["feedback"])
    db.add(sub)
    await db.flush()
    return {**result, "submission_id": str(sub.id), "optimal_complexity": p.optimal_complexity}

@coding_router.get("/submissions")
async def submissions(limit: int = Query(20, le=100), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(CodeSubmission, Problem.title).join(Problem, CodeSubmission.problem_id == Problem.id)
                         .where(CodeSubmission.user_id == user.id).order_by(CodeSubmission.submitted_at.desc()).limit(limit))
    return [{"id": str(s.id), "problem_id": str(s.problem_id), "problem_title": t, "language": s.language,
             "status": s.status, "score": s.score, "tests_passed": s.tests_passed, "tests_total": s.tests_total,
             "complexity_estimate": s.complexity_estimate, "submitted_at": s.submitted_at.isoformat()} for s, t in r.all()]


# ── Chat ──────────────────────────────────────────────────────────────────────
chat_router = APIRouter(prefix="/chat", tags=["chat"])


async def _build_progress_context(db: AsyncSession, user) -> str:
    """
    Summarises the user's real standing for AI personalisation: readiness, weak
    areas, streak, total solved, and days until the interview. Returns "" if there's
    nothing meaningful yet (the AI then just coaches generally).
    """
    lines = []
    mr = await db.execute(
        select(PerformanceMetric).where(PerformanceMetric.user_id == user.id)
        .order_by(PerformanceMetric.metric_date.desc()).limit(1)
    )
    metric = mr.scalar_one_or_none()
    if metric:
        if metric.readiness_score:
            lines.append(f"Readiness score: {round(metric.readiness_score)}/100")
        if metric.total_problems_solved:
            lines.append(f"Problems solved so far: {metric.total_problems_solved}")
        if metric.weak_areas:
            lines.append(f"Weakest areas: {', '.join(metric.weak_areas)}")
        if metric.strong_areas:
            lines.append(f"Strong areas: {', '.join(metric.strong_areas)}")
        if metric.streak_days:
            lines.append(f"Current streak: {metric.streak_days} day(s)")
    if user.interview_date:
        from datetime import date as _date
        days_left = (user.interview_date - _date.today()).days
        if days_left >= 0:
            lines.append(f"Days until their interview: {days_left}")
    return "\n".join(f"- {l}" for l in lines)

class ChatMsg(BaseModel):
    message: str
    problem_id: Optional[str] = None
    current_code: Optional[str] = None
    context_type: str = "general"  # coding|general|flashcard|coach
    topic: Optional[str] = None

@chat_router.post("/message")
async def chat_message(body: ChatMsg, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Rate limit: 20 AI messages/minute per user — protects the LLM API key from abuse.
    if not await rate_limit(f"chat:{user.id}", limit=20, window_seconds=60):
        raise HTTPException(429, "You're sending messages too fast. Please wait a moment.")
    # Get/create session
    sr = await db.execute(select(ChatSession).where(ChatSession.user_id == user.id, ChatSession.ended_at.is_(None), ChatSession.context_type == body.context_type).order_by(ChatSession.started_at.desc()).limit(1))
    session = sr.scalar_one_or_none()
    if not session:
        session = ChatSession(id=uuid.uuid4(), user_id=user.id, context_type=body.context_type, messages=[], context_data={})
        db.add(session)
        await db.flush()

    # Get resume context
    rr = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc()).limit(1))
    resume = rr.scalar_one_or_none()
    projects = resume.projects_extracted or [] if resume else []

    # Build live progress context so the AI coaches against the user's real standing.
    progress = await _build_progress_context(db, user)

    history = session.messages or []
    problem_title = ""
    if body.problem_id:
        try:
            pr = await db.execute(select(Problem).where(Problem.id == uuid.UUID(body.problem_id)))
            prob = pr.scalar_one_or_none()
            if prob: problem_title = prob.title
        except: pass

    # Route to appropriate AI mode
    ct = body.context_type
    if ct == "coding":
        reply = await interviewer_response(body.message, history, user.full_name,
                                           user.target_company or "your target company",
                                           user.target_role or "SDE-1", problem_title,
                                           body.current_code or "", projects, progress=progress)
    elif ct == "flashcard":
        reply = await flashcard_response(body.message, history, body.topic or "computer science", user.full_name, progress=progress)
    elif ct == "coach":
        reply = await coach_response(body.message, history, user.full_name,
                                     user.target_role or "SDE-1", user.target_company or "top tech company", progress=progress)
    else:
        reply = await coach_response(body.message, history, user.full_name,
                                     user.target_role or "SDE-1", user.target_company or "top tech company", progress=progress)

    now = datetime.now(timezone.utc).isoformat()
    session.messages = (list(history) + [{"role":"user","content":body.message,"timestamp":now},
                                          {"role":"assistant","content":reply,"timestamp":now}])[-50:]
    db.add(session)
    await db.flush()
    return {"session_id": str(session.id), "reply": reply}

@chat_router.post("/stream")
async def chat_stream(body: ChatMsg, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Streams the AI reply token-by-token via Server-Sent Events (SSE).
    Each event is `data: {"delta": "..."}`; a final `data: {"done": true, ...}` closes it.
    The full reply is persisted to the chat session once streaming completes.
    """
    if not await rate_limit(f"chat:{user.id}", limit=20, window_seconds=60):
        raise HTTPException(429, "You're sending messages too fast. Please wait a moment.")

    # Session
    sr = await db.execute(select(ChatSession).where(ChatSession.user_id == user.id, ChatSession.ended_at.is_(None), ChatSession.context_type == body.context_type).order_by(ChatSession.started_at.desc()).limit(1))
    session = sr.scalar_one_or_none()
    if not session:
        session = ChatSession(id=uuid.uuid4(), user_id=user.id, context_type=body.context_type, messages=[], context_data={})
        db.add(session)
        await db.flush()

    rr = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc()).limit(1))
    resume = rr.scalar_one_or_none()
    projects = resume.projects_extracted or [] if resume else []
    progress = await _build_progress_context(db, user)
    history = list(session.messages or [])

    problem_title = ""
    if body.problem_id:
        try:
            pr = await db.execute(select(Problem).where(Problem.id == uuid.UUID(body.problem_id)))
            prob = pr.scalar_one_or_none()
            if prob: problem_title = prob.title
        except Exception:
            pass

    system = build_chat_system(
        body.context_type, user_name=user.full_name,
        company=user.target_company or "your target company", role=user.target_role or "SDE-1",
        problem_title=problem_title, code=body.current_code or "", projects=projects,
        topic=body.topic or "", progress=progress,
    )

    async def event_gen():
        import json
        full = ""
        async for piece in stream_ai(system, history, body.message):
            full += piece
            yield f"data: {json.dumps({'delta': piece})}\n\n"
        # Persist the completed exchange.
        now = datetime.now(timezone.utc).isoformat()
        session.messages = (history + [{"role": "user", "content": body.message, "timestamp": now},
                                       {"role": "assistant", "content": full, "timestamp": now}])[-50:]
        db.add(session)
        await db.flush()
        yield f"data: {json.dumps({'done': True, 'session_id': str(session.id)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


class EndSessionReq(BaseModel):
    session_id: Optional[str] = None


@chat_router.post("/end-session")
async def end_session(body: EndSessionReq, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    sid = body.session_id
    if sid:
        r = await db.execute(select(ChatSession).where(ChatSession.id == uuid.UUID(sid), ChatSession.user_id == user.id))
    else:
        r = await db.execute(select(ChatSession).where(ChatSession.user_id == user.id, ChatSession.ended_at.is_(None)).order_by(ChatSession.started_at.desc()).limit(1))
    session = r.scalar_one_or_none()
    if not session: raise HTTPException(404, "Session not found")
    session.ended_at = datetime.now(timezone.utc)
    db.add(session)
    await db.flush()
    return {"ended": True}


# ── Mock Interview ────────────────────────────────────────────────────────────
mock_router = APIRouter(prefix="/mock", tags=["mock"])


def _is_interview_allowed(user) -> bool:
    return user.subscription_status in ("free_trial", "active")


class StartMockReq(BaseModel):
    round_type: str = "full"  # technical | behavioral | full


class MockChatReq(BaseModel):
    mock_id: str
    message: str
    end_requested: bool = False       # candidate clicked "End interview"
    tab_switches: Optional[int] = None
    camera_active: Optional[bool] = None


def _resume_data_from(resume) -> dict:
    if not resume:
        return {}
    return {
        "projects": resume.projects_extracted or [],
        "experience": resume.experience_extracted or [],
        "skills": resume.skills_extracted or [],
        "education": resume.education_extracted or [],
    }


@mock_router.post("/start")
async def start_mock(body: StartMockReq, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not _is_interview_allowed(user):
        raise HTTPException(403, "Mock interviews require an active subscription")

    rr = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc()).limit(1))
    resume = rr.scalar_one_or_none()
    resume_data = _resume_data_from(resume)

    # AI generates the opening question — no pre-generated list
    opening = await mock_interview_chat(
        message="[START]",
        history=[],
        user_name=user.full_name or "Candidate",
        company=user.target_company or "top tech company",
        role=user.target_role or "SDE-1",
        resume_data=resume_data,
        round_type=body.round_type,
    )

    mock = MockInterview(
        id=uuid.uuid4(), user_id=user.id, interview_type=body.round_type,
        target_company=user.target_company, target_role=user.target_role,
        # Store conversation as a flat messages list: [{"role": "assistant"|"user", "content": "..."}]
        questions=[opening], answers=[], evaluations=[],
        completed=False, is_proctored=True, time_limit_minutes=30,
    )
    db.add(mock)
    await db.flush()
    return {"mock_id": str(mock.id), "opening": opening, "round_type": body.round_type}


@mock_router.post("/chat")
async def mock_chat(body: MockChatReq, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Conversational interview turn. Passes the full message history to the AI so it can
    follow up on specific words/concepts from the candidate's last answer instead of
    moving to a pre-set next question.
    """
    if not await rate_limit(f"mock:{user.id}", limit=30, window_seconds=60):
        raise HTTPException(429, "Too many submissions. Please slow down.")

    r = await db.execute(select(MockInterview).where(MockInterview.id == uuid.UUID(body.mock_id), MockInterview.user_id == user.id))
    mock = r.scalar_one_or_none()
    if not mock:
        raise HTTPException(404, "Mock not found")
    if mock.completed:
        raise HTTPException(400, "This interview is already complete")

    rr = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc()).limit(1))
    resume = rr.scalar_one_or_none()
    resume_data = _resume_data_from(resume)

    # Proctoring telemetry
    if body.tab_switches is not None:
        mock.tab_switches = body.tab_switches
    if body.camera_active is not None:
        mock.camera_active = body.camera_active

    # Rebuild full conversation history from stored turns
    # questions[] = AI turns, answers[] = candidate turns, interleaved
    ai_turns = list(mock.questions or [])   # AI messages (opening + follow-ups)
    candidate_turns = list(mock.answers or [])  # candidate messages

    history = []
    for i, ai_msg in enumerate(ai_turns):
        history.append({"role": "assistant", "content": ai_msg})
        if i < len(candidate_turns):
            history.append({"role": "user", "content": candidate_turns[i]})

    # Get the AI's next response (follow-up or new topic — AI decides)
    ai_response = await mock_interview_chat(
        message=body.message,
        history=history,
        user_name=user.full_name or "Candidate",
        company=mock.target_company or "top tech company",
        role=mock.target_role or "SDE-1",
        resume_data=resume_data,
        round_type=mock.interview_type or "full",
        end_requested=body.end_requested,
    )

    # When end_requested, the user message is replaced by the debrief prompt in mock_interview_chat,
    # so we don't persist a fake user turn for it — only persist real candidate answers.
    if not body.end_requested:
        mock.answers = candidate_turns + [body.message]
    mock.questions = ai_turns + [ai_response]

    # The interview ends ONLY when explicitly requested (timer or manual end button).
    # The AI never self-terminates during regular turns — it just keeps interviewing.
    is_complete = body.end_requested

    if is_complete:
        mock.completed = True
        mock.completed_at = datetime.now(timezone.utc)
        mock.duration_minutes = int((datetime.now(timezone.utc) - mock.started_at).total_seconds() / 60)
        mock.feedback_summary = ai_response
        mock.overall_score = extract_score_from_evaluation(ai_response)
        mock.verdict = extract_verdict_from_score(mock.overall_score)

    db.add(mock)
    await db.flush()

    return {
        "reply": ai_response,
        "is_complete": is_complete,
        "overall_score": mock.overall_score if is_complete else None,
        "verdict": mock.verdict if is_complete else None,
        "feedback_summary": mock.feedback_summary if is_complete else None,
        "exchange_count": len(mock.answers),
    }

@mock_router.get("/history")
async def mock_history(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(MockInterview).where(MockInterview.user_id == user.id).order_by(MockInterview.started_at.desc()).limit(10))
    mocks = r.scalars().all()
    return [{"id": str(m.id), "interview_type": m.interview_type, "target_company": m.target_company,
             "overall_score": m.overall_score, "verdict": m.verdict, "completed": m.completed,
             "duration_minutes": m.duration_minutes, "started_at": m.started_at.isoformat()} for m in mocks]


# ── Analytics ─────────────────────────────────────────────────────────────────
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])

@analytics_router.get("/dashboard")
async def analytics_dashboard(days: int = Query(14, ge=1, le=90), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    since = date.today() - timedelta(days=days)
    # Upsert today's metric
    today = date.today()
    mr = await db.execute(select(PerformanceMetric).where(PerformanceMetric.user_id == user.id, PerformanceMetric.metric_date == today))
    metric = mr.scalar_one_or_none()
    today_subs_r = await db.execute(select(CodeSubmission).where(CodeSubmission.user_id == user.id, func.date(CodeSubmission.submitted_at) == today))
    today_subs = today_subs_r.scalars().all()
    attempted = len(today_subs)
    solved = sum(1 for s in today_subs if s.status == "accepted")
    total_r = await db.execute(select(func.count(CodeSubmission.id)).where(CodeSubmission.user_id == user.id, CodeSubmission.status == "accepted"))
    total_solved = total_r.scalar() or 0
    sa = user.skill_assessment or {}
    topic_scores = {k: min(100, sa.get(k, 2) / 5 * 100) for k in ["dsa","os","dbms","cn","oop","system_design","behavioral"]}
    readiness = min(100, round(sum(topic_scores.values()) / 7 * 0.8 + min(20, total_solved * 0.5), 1))

    # Streak
    prev_r = await db.execute(select(PerformanceMetric).where(PerformanceMetric.user_id == user.id, PerformanceMetric.metric_date < today).order_by(PerformanceMetric.metric_date.desc()).limit(1))
    prev = prev_r.scalar_one_or_none()
    streak = 0
    if prev:
        if prev.metric_date == today - timedelta(days=1): streak = (prev.streak_days or 0) + (1 if attempted > 0 else 0)
        else: streak = 1 if attempted > 0 else 0
    else: streak = 1 if attempted > 0 else 0

    trend = ImprovementTrend.stable
    if prev:
        if readiness > prev.readiness_score + 2: trend = ImprovementTrend.improving
        elif readiness < prev.readiness_score - 2: trend = ImprovementTrend.declining

    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1])
    weak = [t for t, s in sorted_topics[:3] if s < 60]
    strong = [t for t, s in sorted_topics[-3:] if s >= 70]

    if not metric:
        metric = PerformanceMetric(id=uuid.uuid4(), user_id=user.id, metric_date=today)
    metric.readiness_score = readiness; metric.topic_scores = topic_scores
    metric.problems_attempted = attempted; metric.problems_solved = solved
    metric.accuracy_rate = (solved/attempted*100) if attempted else 0
    metric.total_problems_solved = total_solved; metric.weak_areas = weak
    metric.strong_areas = strong; metric.improvement_trend = trend; metric.streak_days = streak
    db.add(metric)
    await db.flush()

    hist_r = await db.execute(select(PerformanceMetric).where(PerformanceMetric.user_id == user.id, PerformanceMetric.metric_date >= since).order_by(PerformanceMetric.metric_date.asc()))
    history = hist_r.scalars().all()

    mock_r = await db.execute(select(MockInterview).where(MockInterview.user_id == user.id, MockInterview.completed == True).order_by(MockInterview.completed_at.desc()).limit(5))
    mocks = mock_r.scalars().all()

    return {
        "current": {"readiness_score": readiness, "topic_scores": topic_scores, "total_problems_solved": total_solved,
                    "streak_days": streak, "weak_areas": weak, "strong_areas": strong, "improvement_trend": trend,
                    "accuracy_rate": metric.accuracy_rate},
        "history": [{"date": m.metric_date.isoformat(), "readiness_score": m.readiness_score,
                     "problems_solved": m.problems_solved, "accuracy_rate": m.accuracy_rate, "streak_days": m.streak_days} for m in history],
        "mock_scores": [{"date": m.completed_at.isoformat() if m.completed_at else "", "score": m.overall_score, "company": m.target_company} for m in mocks],
    }
