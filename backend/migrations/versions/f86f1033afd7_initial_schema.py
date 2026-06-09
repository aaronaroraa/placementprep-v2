"""Initial schema

Revision ID: f86f1033afd7
Revises: 
Create Date: 2026-06-09 14:31:58.908939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f86f1033afd7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE authprovider AS ENUM ('email', 'google')")
    op.execute("CREATE TYPE plantype AS ENUM ('crash_24h', 'fast_track_1w', 'structured_3w', 'roadmap_1m_plus')")
    op.execute("CREATE TYPE difficulty AS ENUM ('easy', 'medium', 'hard')")
    op.execute("CREATE TYPE language AS ENUM ('python', 'cpp', 'java', 'javascript')")
    op.execute("CREATE TYPE submissionstatus AS ENUM ('accepted', 'wrong_answer', 'tle', 'runtime_error')")
    op.execute("CREATE TYPE tasktype AS ENUM ('dsa_problem', 'theory', 'behavioral', 'project_review', 'mock_test')")
    op.execute("CREATE TYPE contexttype AS ENUM ('coding', 'resume', 'general', 'mock_interview')")
    op.execute("CREATE TYPE improvementtrend AS ENUM ('improving', 'stable', 'declining')")

    # Create tables
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('auth_provider', postgresql.ENUM('email', 'google', name='authprovider', create_type=False), nullable=False),
        sa.Column('google_id', sa.String(length=200), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('google_calendar_token', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('calendar_connected', sa.Boolean(), nullable=False),
        sa.Column('calendar_event_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('college', sa.String(length=200), nullable=True),
        sa.Column('branch', sa.String(length=100), nullable=True),
        sa.Column('graduation_year', sa.Integer(), nullable=True),
        sa.Column('target_role', sa.String(length=100), nullable=True),
        sa.Column('target_company', sa.String(length=100), nullable=True),
        sa.Column('interview_date', sa.Date(), nullable=True),
        sa.Column('daily_hours', sa.Float(), nullable=False),
        sa.Column('skill_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False),
        sa.Column('onboarding_step', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)

    op.create_table(
        'problems',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('difficulty', postgresql.ENUM('easy', 'medium', 'hard', name='difficulty', create_type=False), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('test_cases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('hidden_test_cases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('constraints', sa.Text(), nullable=True),
        sa.Column('hints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('solution_approach', sa.Text(), nullable=True),
        sa.Column('optimal_complexity', sa.String(length=50), nullable=True),
        sa.Column('company_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('role_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('times_asked', sa.Integer(), nullable=False),
        sa.Column('last_asked_year', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('skills_extracted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('projects_extracted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('experience_extracted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('education_extracted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('skill_gaps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('interview_questions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'prep_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_type', postgresql.ENUM('crash_24h', 'fast_track_1w', 'structured_3w', 'roadmap_1m_plus', name='plantype', create_type=False), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('total_days', sa.Integer(), nullable=False),
        sa.Column('target_company', sa.String(length=100), nullable=True),
        sa.Column('target_role', sa.String(length=100), nullable=True),
        sa.Column('plan_structure', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('completion_pct', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'daily_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('task_type', postgresql.ENUM('dsa_problem', 'theory', 'behavioral', 'project_review', 'mock_test', name='tasktype', create_type=False), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calendar_event_id', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['prep_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'code_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('problem_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('language', postgresql.ENUM('python', 'cpp', 'java', 'javascript', name='language', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('accepted', 'wrong_answer', 'tle', 'runtime_error', name='submissionstatus', create_type=False), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('memory_used_kb', sa.Float(), nullable=True),
        sa.Column('test_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tests_passed', sa.Integer(), nullable=False),
        sa.Column('tests_total', sa.Integer(), nullable=False),
        sa.Column('complexity_estimate', sa.String(length=50), nullable=True),
        sa.Column('edge_cases_handled', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('interviewer_notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('readiness_score', sa.Float(), nullable=False),
        sa.Column('topic_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('problems_attempted', sa.Integer(), nullable=False),
        sa.Column('problems_solved', sa.Integer(), nullable=False),
        sa.Column('avg_time_per_problem_min', sa.Float(), nullable=False),
        sa.Column('accuracy_rate', sa.Float(), nullable=False),
        sa.Column('total_problems_solved', sa.Integer(), nullable=False),
        sa.Column('total_study_time_min', sa.Integer(), nullable=False),
        sa.Column('streak_days', sa.Integer(), nullable=False),
        sa.Column('weak_areas', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('strong_areas', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('improvement_trend', postgresql.ENUM('improving', 'stable', 'declining', name='improvementtrend', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('context_type', postgresql.ENUM('coding', 'resume', 'general', 'mock_interview', name='contexttype', create_type=False), nullable=False),
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('messages', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'mock_interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interview_type', sa.String(length=50), nullable=False),
        sa.Column('target_company', sa.String(length=100), nullable=True),
        sa.Column('target_role', sa.String(length=100), nullable=True),
        sa.Column('questions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('answers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('feedback_summary', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('mock_interviews')
    op.drop_table('chat_sessions')
    op.drop_table('performance_metrics')
    op.drop_table('code_submissions')
    op.drop_table('daily_tasks')
    op.drop_table('prep_plans')
    op.drop_table('resumes')
    op.drop_table('problems')
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop custom PostgreSQL ENUMs
    op.execute("DROP TYPE IF EXISTS improvementtrend")
    op.execute("DROP TYPE IF EXISTS contexttype")
    op.execute("DROP TYPE IF EXISTS tasktype")
    op.execute("DROP TYPE IF EXISTS submissionstatus")
    op.execute("DROP TYPE IF EXISTS language")
    op.execute("DROP TYPE IF EXISTS difficulty")
    op.execute("DROP TYPE IF EXISTS plantype")
    op.execute("DROP TYPE IF EXISTS authprovider")

