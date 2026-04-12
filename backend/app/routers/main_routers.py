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
                                     generate_resume_interview_questions)
from app.config import settings

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
        user.target_role or "SDE-1", user.target_company or "your target company"
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
    q = select(Problem)
    if difficulty: q = q.where(Problem.difficulty == difficulty)
    if category: q = q.where(Problem.category == category)
    q = q.order_by(Problem.times_asked.desc()).limit(100)
    result = await db.execute(q)
    problems = result.scalars().all()
    if company:
        cl = company.lower()
        problems = [p for p in problems if cl in [t.lower() for t in (p.company_tags or [])]]
    return [{"id": str(p.id), "title": p.title, "difficulty": p.difficulty, "category": p.category,
             "tags": p.tags, "company_tags": p.company_tags, "times_asked": p.times_asked,
             "optimal_complexity": p.optimal_complexity} for p in problems]

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

class ChatMsg(BaseModel):
    message: str
    problem_id: Optional[str] = None
    current_code: Optional[str] = None
    context_type: str = "general"  # coding|general|flashcard|coach
    topic: Optional[str] = None

@chat_router.post("/message")
async def chat_message(body: ChatMsg, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
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
                                           body.current_code or "", projects)
    elif ct == "flashcard":
        reply = await flashcard_response(body.message, history, body.topic or "computer science", user.full_name)
    elif ct == "coach":
        reply = await coach_response(body.message, history, user.full_name,
                                     user.target_role or "SDE-1", user.target_company or "top tech company")
    else:
        reply = await coach_response(body.message, history, user.full_name,
                                     user.target_role or "SDE-1", user.target_company or "top tech company")

    now = datetime.now(timezone.utc).isoformat()
    session.messages = (list(history) + [{"role":"user","content":body.message,"timestamp":now},
                                          {"role":"assistant","content":reply,"timestamp":now}])[-50:]
    db.add(session)
    await db.flush()
    return {"session_id": str(session.id), "reply": reply}

@chat_router.post("/end-session")
async def end_session(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    sid = body.get("session_id")
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

class MockAnswer(BaseModel):
    mock_id: str
    question_index: int
    answer: str

@mock_router.post("/start")
async def start_mock(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    interview_type = body.get("interview_type", "technical")
    rr = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc()).limit(1))
    resume = rr.scalar_one_or_none()
    projects = resume.projects_extracted or [] if resume else []
    questions = await generate_resume_interview_questions(
        projects, resume.experience_extracted or [] if resume else [],
        user.target_role or "SDE-1", user.target_company or "top tech company"
    )
    mock = MockInterview(id=uuid.uuid4(), user_id=user.id, interview_type=interview_type,
                         target_company=user.target_company, target_role=user.target_role,
                         questions=questions, answers=[], evaluations=[], completed=False)
    db.add(mock)
    await db.flush()
    return {"mock_id": str(mock.id), "first_question": questions[0] if questions else "Tell me about yourself.", "total_questions": len(questions), "interview_type": interview_type}

@mock_router.post("/answer")
async def submit_answer(body: MockAnswer, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(MockInterview).where(MockInterview.id == uuid.UUID(body.mock_id), MockInterview.user_id == user.id))
    mock = r.scalar_one_or_none()
    if not mock: raise HTTPException(404, "Mock not found")

    rr = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.uploaded_at.desc()).limit(1))
    resume = rr.scalar_one_or_none()
    projects = resume.projects_extracted or [] if resume else []

    answers = list(mock.answers or [])
    answers.append({"question_index": body.question_index, "answer": body.answer})
    mock.answers = answers

    questions = mock.questions or []
    current_q = questions[body.question_index] if body.question_index < len(questions) else ""

    history = []
    for i, ans in enumerate(answers[:-1]):
        if i < len(questions):
            history.append({"role": "assistant", "content": questions[i]})
            history.append({"role": "user", "content": ans["answer"]})

    ai_response = await mock_interview_response(
        body.answer, history, user.full_name,
        mock.target_company or "your target company",
        mock.target_role or "SDE-1", projects,
        mock.interview_type,
    )

    evaluations = list(mock.evaluations or [])
    evaluations.append({"question_index": body.question_index, "evaluation": ai_response})
    mock.evaluations = evaluations

    # Check if done
    next_q_index = body.question_index + 1
    is_complete = next_q_index >= len(questions)
    next_question = None
    if not is_complete:
        next_question = questions[next_q_index]

    if is_complete:
        mock.completed = True
        mock.completed_at = datetime.now(timezone.utc)
        mock.duration_minutes = int((datetime.now(timezone.utc) - mock.started_at).total_seconds() / 60)
        # Final score from last AI response (contains debrief)
        mock.feedback_summary = ai_response
        mock.overall_score = min(100, max(0, len([a for a in answers if len(a.get("answer","")) > 50]) * (100 / len(questions))))

    db.add(mock)
    await db.flush()
    return {"interviewer_response": ai_response, "next_question": next_question,
            "next_question_index": next_q_index, "is_complete": is_complete,
            "overall_score": mock.overall_score if is_complete else None,
            "feedback_summary": mock.feedback_summary if is_complete else None}

@mock_router.get("/history")
async def mock_history(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(MockInterview).where(MockInterview.user_id == user.id).order_by(MockInterview.started_at.desc()).limit(10))
    mocks = r.scalars().all()
    return [{"id": str(m.id), "interview_type": m.interview_type, "target_company": m.target_company,
             "overall_score": m.overall_score, "completed": m.completed, "duration_minutes": m.duration_minutes,
             "started_at": m.started_at.isoformat()} for m in mocks]


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
