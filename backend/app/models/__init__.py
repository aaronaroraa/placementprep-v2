import uuid, enum
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Boolean, Integer, Float, Text, Date, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PlanType(str, enum.Enum):
    crash_24h = "crash_24h"
    fast_track_1w = "fast_track_1w"
    structured_3w = "structured_3w"
    roadmap_1m_plus = "roadmap_1m_plus"

class Difficulty(str, enum.Enum):
    easy = "easy"; medium = "medium"; hard = "hard"

class Language(str, enum.Enum):
    python = "python"; cpp = "cpp"; java = "java"; javascript = "javascript"

class SubmissionStatus(str, enum.Enum):
    accepted = "accepted"; wrong_answer = "wrong_answer"; tle = "tle"; runtime_error = "runtime_error"

class TaskType(str, enum.Enum):
    dsa_problem = "dsa_problem"; theory = "theory"; behavioral = "behavioral"
    project_review = "project_review"; mock_test = "mock_test"

class ContextType(str, enum.Enum):
    coding = "coding"; resume = "resume"; general = "general"; mock_interview = "mock_interview"

class ImprovementTrend(str, enum.Enum):
    improving = "improving"; stable = "stable"; declining = "declining"

class AuthProvider(str, enum.Enum):
    email = "email"; google = "google"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    auth_provider: Mapped[AuthProvider] = mapped_column(SAEnum(AuthProvider), default=AuthProvider.email)
    google_id: Mapped[Optional[str]] = mapped_column(String(200), unique=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Google Calendar
    google_calendar_token: Mapped[Optional[dict]] = mapped_column(JSONB)
    calendar_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    calendar_event_ids: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Profile
    college: Mapped[Optional[str]] = mapped_column(String(200))
    branch: Mapped[Optional[str]] = mapped_column(String(100))
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer)
    target_role: Mapped[Optional[str]] = mapped_column(String(100))
    target_company: Mapped[Optional[str]] = mapped_column(String(100))
    interview_date: Mapped[Optional[date]] = mapped_column(Date)
    daily_hours: Mapped[float] = mapped_column(Float, default=2.0)
    skill_assessment: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    resumes: Mapped[List["Resume"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    prep_plans: Mapped[List["PrepPlan"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    code_submissions: Mapped[List["CodeSubmission"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    performance_metrics: Mapped[List["PerformanceMetric"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    mock_interviews: Mapped[List["MockInterview"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    file_path: Mapped[str] = mapped_column(String(500))
    file_name: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    skills_extracted: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    projects_extracted: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    experience_extracted: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    education_extracted: Mapped[Optional[dict]] = mapped_column(JSONB)
    skill_gaps: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    strengths: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    interview_questions: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    user: Mapped["User"] = relationship(back_populates="resumes")


class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[Difficulty] = mapped_column(SAEnum(Difficulty))
    category: Mapped[str] = mapped_column(String(50))
    tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    test_cases: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    hidden_test_cases: Mapped[Optional[dict]] = mapped_column(JSONB)
    constraints: Mapped[Optional[str]] = mapped_column(Text)
    hints: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    solution_approach: Mapped[Optional[str]] = mapped_column(Text)
    optimal_complexity: Mapped[Optional[str]] = mapped_column(String(50))
    company_tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    role_tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    times_asked: Mapped[int] = mapped_column(Integer, default=1)
    last_asked_year: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    submissions: Mapped[List["CodeSubmission"]] = relationship(back_populates="problem")


class CodeSubmission(Base):
    __tablename__ = "code_submissions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    problem_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(Text)
    language: Mapped[Language] = mapped_column(SAEnum(Language))
    status: Mapped[SubmissionStatus] = mapped_column(SAEnum(SubmissionStatus), default=SubmissionStatus.wrong_answer)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float)
    memory_used_kb: Mapped[Optional[float]] = mapped_column(Float)
    test_results: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_total: Mapped[int] = mapped_column(Integer, default=0)
    complexity_estimate: Mapped[Optional[str]] = mapped_column(String(50))
    edge_cases_handled: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    interviewer_notes: Mapped[Optional[str]] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped["User"] = relationship(back_populates="code_submissions")
    problem: Mapped["Problem"] = relationship(back_populates="submissions")


class PrepPlan(Base):
    __tablename__ = "prep_plans"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    plan_type: Mapped[PlanType] = mapped_column(SAEnum(PlanType))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    total_days: Mapped[int] = mapped_column(Integer)
    target_company: Mapped[Optional[str]] = mapped_column(String(100))
    target_role: Mapped[Optional[str]] = mapped_column(String(100))
    plan_structure: Mapped[Optional[dict]] = mapped_column(JSONB)
    completion_pct: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user: Mapped["User"] = relationship(back_populates="prep_plans")
    tasks: Mapped[List["DailyTask"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class DailyTask(Base):
    __tablename__ = "daily_tasks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prep_plans.id", ondelete="CASCADE"))
    day_number: Mapped[int] = mapped_column(Integer)
    task_type: Mapped[TaskType] = mapped_column(SAEnum(TaskType))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    problem_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("problems.id"), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=2)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    calendar_event_id: Mapped[Optional[str]] = mapped_column(String(200))
    plan: Mapped["PrepPlan"] = relationship(back_populates="tasks")


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    metric_date: Mapped[date] = mapped_column(Date)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    topic_scores: Mapped[Optional[dict]] = mapped_column(JSONB)
    problems_attempted: Mapped[int] = mapped_column(Integer, default=0)
    problems_solved: Mapped[int] = mapped_column(Integer, default=0)
    avg_time_per_problem_min: Mapped[float] = mapped_column(Float, default=0.0)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=0.0)
    total_problems_solved: Mapped[int] = mapped_column(Integer, default=0)
    total_study_time_min: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    weak_areas: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    strong_areas: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    improvement_trend: Mapped[ImprovementTrend] = mapped_column(SAEnum(ImprovementTrend), default=ImprovementTrend.stable)
    user: Mapped["User"] = relationship(back_populates="performance_metrics")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    context_type: Mapped[ContextType] = mapped_column(SAEnum(ContextType), default=ContextType.general)
    context_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    messages: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    user: Mapped["User"] = relationship(back_populates="chat_sessions")


class MockInterview(Base):
    __tablename__ = "mock_interviews"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    interview_type: Mapped[str] = mapped_column(String(50), default="full")
    target_company: Mapped[Optional[str]] = mapped_column(String(100))
    target_role: Mapped[Optional[str]] = mapped_column(String(100))
    questions: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    answers: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    evaluations: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    overall_score: Mapped[Optional[float]] = mapped_column(Float)
    feedback_summary: Mapped[Optional[str]] = mapped_column(Text)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    user: Mapped["User"] = relationship(back_populates="mock_interviews")
