import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.database import get_db
from app.models import User, PrepPlan, CodeSubmission, PerformanceMetric, DailyTask
from app.auth import get_current_user
from app.services.prep_engine import generate_plan
from app.services.calendar_service import (
    create_prep_calendar, bulk_create_prep_schedule,
    create_interview_day_event, mark_event_complete,
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

    # Generate plan
    days_left = max(1, (body.interview_date - date.today()).days)
    plan_data = generate_plan(days_left, body.target_company, body.target_role, body.interview_date, body.daily_hours)

    # Deactivate old plans
    from sqlalchemy import update
    await db.execute(update(PrepPlan).where(PrepPlan.user_id == user.id).values(is_active=False))

    plan = PrepPlan(
        id=uuid.uuid4(), user_id=user.id, plan_type=plan_data["plan_type"],
        start_date=plan_data["start_date"], end_date=plan_data["end_date"],
        total_days=max(1, plan_data["total_days"]),
        target_company=body.target_company, target_role=body.target_role,
        plan_structure=plan_data["plan_structure"], completion_pct=0.0, is_active=True,
    )
    db.add(plan)
    await db.flush()

    # Create tasks
    for t in plan_data["tasks"]:
        task = DailyTask(
            id=uuid.uuid4(), plan_id=plan.id, day_number=t["day_number"],
            task_type=t["task_type"], title=t["title"], description=t.get("description",""),
            metadata=t.get("metadata",{}), priority=t.get("priority",2),
            estimated_minutes=t.get("estimated_minutes",30), completed=False,
        )
        db.add(task)
    await db.flush()

    # Google Calendar sync if connected
    calendar_event_ids = {}
    if user.calendar_connected and user.google_calendar_token:
        try:
            cal_id = await create_prep_calendar(user.google_calendar_token, f"PlacementPrep — {body.target_company}")
            if cal_id:
                # Group tasks by day
                tasks_by_day = {}
                for t in plan_data["tasks"]:
                    d = str(t["day_number"])
                    if d not in tasks_by_day:
                        tasks_by_day[d] = []
                    tasks_by_day[d].append(t["title"])

                event_ids = await bulk_create_prep_schedule(
                    user.google_calendar_token, cal_id,
                    plan_data["start_date"], plan_data["end_date"],
                    body.target_company, body.target_role,
                    tasks_by_day, body.daily_hours,
                )
                # Interview day event
                interview_event_id = await create_interview_day_event(
                    user.google_calendar_token, cal_id, body.interview_date,
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
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    task_id = body.get("task_id")
    try:
        tid = uuid.UUID(task_id)
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
                await mark_event_complete(
                    user.google_calendar_token, cal_id,
                    plan_events[day_key], f"PlacementPrep — Day {task.day_number}"
                )
        except Exception:
            pass

    return {"task_id": task_id, "completed": True, "completion_pct": plan.completion_pct}


@router.post("/calendar/connect")
async def connect_calendar(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Called after Google OAuth when user wants to connect calendar post-onboarding."""
    token_data = body.get("token_data")
    if not token_data:
        raise HTTPException(400, "token_data required")
    user.google_calendar_token = token_data
    user.calendar_connected = True
    db.add(user)
    await db.flush()
    return {"connected": True}
