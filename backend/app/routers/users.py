import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import User, PrepPlan, CodeSubmission, PerformanceMetric, DailyTask, Problem, Resume
from app.auth import get_current_user
from app.services.prep_engine import generate_plan, generate_plan_smart
from app.services.calendar_service import (
    create_prep_calendar, bulk_create_prep_schedule,
    create_interview_day_event, mark_event_complete, refresh_google_token,
)
from app.config import settings

router = APIRouter(prefix="/users", tags=["users"])


class OnboardingReq(BaseModel):
    college: str
    branch: str
    graduation_year: int
    target_role: str
    target_company: str
    interview_date: date
    daily_hours: float = 2.0
    skill_assessment: dict


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    branch: Optional[str] = None
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    interview_date: Optional[date] = None
    daily_hours: Optional[float] = None


class CompleteTaskReq(BaseModel):
    task_id: str


class ConnectCalendarReq(BaseModel):
    token_data: dict


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id), "email": user.email, "full_name": user.full_name,
        "avatar_url": user.avatar_url, "college": user.college, "branch": user.branch,
        "graduation_year": user.graduation_year, "target_role": user.target_role,
        "target_company": user.target_company, "interview_date": user.interview_date,
        "daily_hours": user.daily_hours, "skill_assessment": user.skill_assessment,
        "onboarding_completed": user.onboarding_completed, "onboarding_step": user.onboarding_step,
        "calendar_connected": user.calendar_connected,
        "created_at": user.created_at.isoformat(),
    }


@router.put("/me")
async def update_me(body: ProfileUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    await db.flush()
    return {"message": "Updated"}


async def _ensure_calendar_token(db: AsyncSession, user: User) -> Optional[dict]:
    """
    Refreshes the user's Google access token before calendar operations.
    Access tokens expire in ~1 hour, so we refresh up front and persist the new one.
    Returns the usable token dict, or None if refresh isn't possible.
    """
    token = user.google_calendar_token
    if not token or not token.get("refresh_token"):
        return token
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET):
        return token
    refreshed = await refresh_google_token(token, settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET)
    if refreshed and refreshed.get("access_token") != token.get("access_token"):
        user.google_calendar_token = refreshed
        db.add(user)
        await db.flush()
    return refreshed


async def _retrieve_candidate_problems(db: AsyncSession, company: Optional[str], limit: int = 60) -> list:
    """
    RAG retrieval step: pull the most relevant REAL problems from the DB, ranked by
    how often they're asked. Filters to the target company when we have matches,
    otherwise returns the globally most-asked problems.
    """
    r = await db.execute(select(Problem).order_by(Problem.times_asked.desc()).limit(150))
    problems = r.scalars().all()
    if company:
        cl = company.lower()
        company_matches = [p for p in problems if cl in [t.lower() for t in (p.company_tags or [])]]
        if company_matches:
            problems = company_matches
    return [{"id": str(p.id), "title": p.title, "difficulty": (p.difficulty.value if hasattr(p.difficulty, "value") else p.difficulty),
             "category": p.category, "times_asked": p.times_asked} for p in problems[:limit]]


async def _build_plan_for_user(db: AsyncSession, user: User, days_left: int, interview_date) -> dict:
    """
    Generates a comprehensive from-scratch curriculum. Does NOT filter topics by
    what the user claims to know — covers everything they need for the target company.
    """
    candidate_problems = await _retrieve_candidate_problems(db, user.target_company)
    plan_data = await generate_plan_smart(
        days_left, user.target_company, user.target_role, interview_date, user.daily_hours,
        candidate_problems=candidate_problems,
    )
    plan_data["_problem_index"] = {p["title"].lower(): p["id"] for p in candidate_problems}
    return plan_data


async def _persist_plan(db: AsyncSession, user: User, plan_data: dict, company, role) -> PrepPlan:
    """Deactivates old plans, writes the new plan + its tasks, linking real problem IDs."""
    from sqlalchemy import update
    await db.execute(update(PrepPlan).where(PrepPlan.user_id == user.id).values(is_active=False))

    plan = PrepPlan(
        id=uuid.uuid4(), user_id=user.id, plan_type=plan_data["plan_type"],
        start_date=plan_data["start_date"], end_date=plan_data["end_date"],
        total_days=max(1, plan_data["total_days"]),
        target_company=company, target_role=role,
        plan_structure=plan_data["plan_structure"], completion_pct=0.0, is_active=True,
    )
    db.add(plan)
    await db.flush()

    problem_index = plan_data.get("_problem_index", {})
    for t in plan_data["tasks"]:
        # Link dsa tasks to a real problem in the DB so they're clickable/solvable
        problem_id = None
        if t["task_type"] == "dsa_problem":
            pid = problem_index.get(t["title"].lower())
            if pid:
                try:
                    problem_id = uuid.UUID(pid)
                except (ValueError, TypeError):
                    problem_id = None
        task = DailyTask(
            id=uuid.uuid4(), plan_id=plan.id, day_number=t["day_number"],
            task_type=t["task_type"], title=t["title"], description=t.get("description", ""),
            task_metadata=t.get("metadata", {}), priority=t.get("priority", 2),
            estimated_minutes=t.get("estimated_minutes", 30), completed=False, problem_id=problem_id,
        )
        db.add(task)
    await db.flush()
    return plan


@router.post("/onboarding")
async def complete_onboarding(
    body: OnboardingReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Save profile
    user.college = body.college
    user.branch = body.branch
    user.graduation_year = body.graduation_year
    user.target_role = body.target_role
    user.target_company = body.target_company
    user.interview_date = body.interview_date
    user.daily_hours = body.daily_hours
    user.skill_assessment = body.skill_assessment
    user.onboarding_completed = True
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)

    # Generate plan (AI-grounded, with static fallback) and persist it
    days_left = max(1, (body.interview_date - date.today()).days)
    plan_data = await _build_plan_for_user(db, user, days_left, body.interview_date)
    plan = await _persist_plan(db, user, plan_data, body.target_company, body.target_role)

    # Google Calendar sync if connected
    calendar_event_ids = {}
    if user.calendar_connected and user.google_calendar_token:
        try:
            cal_token = await _ensure_calendar_token(db, user)
            cal_id = await create_prep_calendar(cal_token, f"PlacementPrep — {body.target_company}")
            if cal_id:
                # Group tasks by day
                tasks_by_day = {}
                for t in plan_data["tasks"]:
                    d = str(t["day_number"])
                    if d not in tasks_by_day:
                        tasks_by_day[d] = []
                    tasks_by_day[d].append(t["title"])

                event_ids = await bulk_create_prep_schedule(
                    cal_token, cal_id,
                    plan_data["start_date"], plan_data["end_date"],
                    body.target_company, body.target_role,
                    tasks_by_day, body.daily_hours,
                )
                # Interview day event
                interview_event_id = await create_interview_day_event(
                    cal_token, cal_id, body.interview_date,
                    body.target_company, body.target_role,
                )
                calendar_event_ids = {"prep_events": event_ids, "interview_event": interview_event_id, "calendar_id": cal_id}
                user.calendar_event_ids = calendar_event_ids
                db.add(user)
                await db.flush()
        except Exception:
            pass

    return {
        "message": "Onboarding complete",
        "plan_id": str(plan.id),
        "plan_type": plan.plan_type,
        "total_tasks": len(plan_data["tasks"]),
        "calendar_synced": bool(calendar_event_ids),
    }


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    days_left = None
    if user.interview_date:
        days_left = max(0, (user.interview_date - date.today()).days)

    plan_result = await db.execute(
        select(PrepPlan).where(PrepPlan.user_id == user.id, PrepPlan.is_active == True)
        .order_by(PrepPlan.start_date.desc()).limit(1)
    )
    plan = plan_result.scalar_one_or_none()

    solved_result = await db.execute(
        select(func.count(CodeSubmission.id))
        .where(CodeSubmission.user_id == user.id, CodeSubmission.status == "accepted")
    )
    problems_solved = solved_result.scalar() or 0

    metric_result = await db.execute(
        select(PerformanceMetric).where(PerformanceMetric.user_id == user.id)
        .order_by(PerformanceMetric.metric_date.desc()).limit(1)
    )
    metric = metric_result.scalar_one_or_none()

    # Today's tasks
    today_tasks = []
    if plan:
        day_num = max(1, (date.today() - plan.start_date).days + 1)
        tasks_result = await db.execute(
            select(DailyTask).where(DailyTask.plan_id == plan.id, DailyTask.day_number == day_num)
            .order_by(DailyTask.priority)
        )
        today_tasks = [
            {"id": str(t.id), "task_type": t.task_type, "title": t.title,
             "description": t.description, "priority": t.priority,
             "estimated_minutes": t.estimated_minutes, "completed": t.completed,
             "problem_id": str(t.problem_id) if t.problem_id else None}
            for t in tasks_result.scalars().all()
        ]

    return {
        "user": {"id": str(user.id), "full_name": user.full_name, "avatar_url": user.avatar_url,
                 "target_role": user.target_role, "target_company": user.target_company,
                 "interview_date": str(user.interview_date) if user.interview_date else None,
                 "onboarding_completed": user.onboarding_completed, "calendar_connected": user.calendar_connected},
        "days_left": days_left,
        "plan_type": plan.plan_type if plan else None,
        "plan_id": str(plan.id) if plan else None,
        "completion_pct": plan.completion_pct if plan else 0,
        "problems_solved": problems_solved,
        "readiness_score": metric.readiness_score if metric else 0,
        "streak_days": metric.streak_days if metric else 0,
        "today_tasks": today_tasks,
        "current_day": max(1, (date.today() - plan.start_date).days + 1) if plan else 1,
        "total_days": plan.total_days if plan else 0,
    }


@router.post("/tasks/complete")
async def complete_task(
    body: CompleteTaskReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        tid = uuid.UUID(body.task_id)
    except Exception:
        raise HTTPException(400, "Invalid task ID")

    result = await db.execute(
        select(DailyTask).join(PrepPlan)
        .where(DailyTask.id == tid, PrepPlan.user_id == user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")

    task.completed = True
    task.completed_at = datetime.now(timezone.utc)
    db.add(task)
    await db.flush()

    # Update plan completion %
    plan_result = await db.execute(select(PrepPlan).where(PrepPlan.id == task.plan_id))
    plan = plan_result.scalar_one()
    all_tasks = await db.execute(select(DailyTask).where(DailyTask.plan_id == plan.id))
    all_t = all_tasks.scalars().all()
    plan.completion_pct = round(sum(1 for t in all_t if t.completed) / len(all_t) * 100, 1) if all_t else 0
    db.add(plan)
    await db.flush()

    # Sync to Google Calendar
    if user.calendar_connected and user.google_calendar_token and user.calendar_event_ids:
        try:
            cal_events = user.calendar_event_ids
            cal_id = cal_events.get("calendar_id")
            plan_events = cal_events.get("prep_events", {})
            day_key = str(task.day_number)
            if cal_id and day_key in plan_events:
                cal_token = await _ensure_calendar_token(db, user)
                await mark_event_complete(
                    cal_token, cal_id,
                    plan_events[day_key], f"PlacementPrep — Day {task.day_number}"
                )
        except Exception:
            pass

    return {"task_id": task_id, "completed": True, "completion_pct": plan.completion_pct}


@router.post("/plan/regenerate")
async def regenerate_plan(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Rebuilds the study plan from the user's CURRENT situation — days left until the
    interview, latest resume gaps, and skill self-assessment. Use after the timeline
    changes or a new resume is uploaded.
    """
    if not user.interview_date:
        raise HTTPException(400, "Set an interview date first")
    days_left = max(1, (user.interview_date - date.today()).days)
    plan_data = await _build_plan_for_user(db, user, days_left, user.interview_date)
    plan = await _persist_plan(db, user, plan_data, user.target_company, user.target_role)
    return {
        "message": "Plan regenerated",
        "plan_id": str(plan.id),
        "plan_type": plan.plan_type,
        "total_tasks": len(plan_data["tasks"]),
        "generated_by": plan_data["plan_structure"].get("generated_by", "static"),
    }


@router.get("/curriculum")
async def get_curriculum(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    plan_result = await db.execute(
        select(PrepPlan).where(PrepPlan.user_id == user.id, PrepPlan.is_active == True)
        .order_by(PrepPlan.start_date.desc()).limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "No active plan found")

    tasks_result = await db.execute(
        select(DailyTask).where(DailyTask.plan_id == plan.id).order_by(DailyTask.day_number, DailyTask.priority)
    )
    all_tasks = tasks_result.scalars().all()

    # Group tasks by day
    days: dict = {}
    for t in all_tasks:
        d = str(t.day_number)
        if d not in days:
            days[d] = []
        days[d].append({
            "id": str(t.id), "task_type": t.task_type, "title": t.title,
            "description": t.description, "priority": t.priority,
            "estimated_minutes": t.estimated_minutes, "completed": t.completed,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        })

    current_day = max(1, (date.today() - plan.start_date).days + 1)
    completed_task_ids = [str(t.id) for t in all_tasks if t.completed]

    return {
        "plan_id": str(plan.id),
        "plan_type": plan.plan_type,
        "current_day": current_day,
        "total_days": plan.total_days,
        "completion_pct": plan.completion_pct,
        "generated_by": (plan.plan_structure or {}).get("generated_by", "static"),
        "completed_task_ids": completed_task_ids,
        "days": [{"day": int(k), "tasks": v} for k, v in sorted(days.items(), key=lambda x: int(x[0]))],
    }


@router.post("/tasks/advance-day")
async def advance_day(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Marks all tasks for the current day as complete and moves to the next day.
    Used when a user wants to skip ahead or manually advance their plan.
    """
    plan_result = await db.execute(
        select(PrepPlan).where(PrepPlan.user_id == user.id, PrepPlan.is_active == True)
        .order_by(PrepPlan.start_date.desc()).limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "No active plan found")

    current_day = max(1, (date.today() - plan.start_date).days + 1)
    if current_day >= plan.total_days:
        return {"message": "Already on the final day", "new_day": current_day}

    # Mark today's incomplete tasks as complete
    tasks_result = await db.execute(
        select(DailyTask).where(
            DailyTask.plan_id == plan.id,
            DailyTask.day_number == current_day,
            DailyTask.completed == False,
        )
    )
    for task in tasks_result.scalars().all():
        task.completed = True
        task.completed_at = datetime.now(timezone.utc)
        db.add(task)

    # Recalculate completion %
    all_tasks_result = await db.execute(select(DailyTask).where(DailyTask.plan_id == plan.id))
    all_tasks = all_tasks_result.scalars().all()
    plan.completion_pct = round(sum(1 for t in all_tasks if t.completed) / len(all_tasks) * 100, 1) if all_tasks else 0
    db.add(plan)
    await db.flush()

    new_day = current_day + 1
    return {"success": True, "new_day": new_day, "completion_pct": plan.completion_pct}


@router.post("/calendar/connect")
async def connect_calendar(
    body: ConnectCalendarReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Called after Google OAuth when user wants to connect calendar post-onboarding."""
    token_data = body.token_data
    if not token_data:
        raise HTTPException(400, "token_data required")
    user.google_calendar_token = token_data
    user.calendar_connected = True
    db.add(user)
    await db.flush()
    return {"connected": True}
