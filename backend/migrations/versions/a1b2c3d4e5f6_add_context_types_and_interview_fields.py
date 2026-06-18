"""Add flashcard/coach context types, subscription status, proctored interview fields

Revision ID: a1b2c3d4e5f6
Revises: f86f1033afd7
Create Date: 2026-06-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = 'f86f1033afd7'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. Extend the contexttype enum with flashcard and coach ──────────────
    # PostgreSQL requires ALTER TYPE ... ADD VALUE outside a transaction block.
    op.execute("ALTER TYPE contexttype ADD VALUE IF NOT EXISTS 'flashcard'")
    op.execute("ALTER TYPE contexttype ADD VALUE IF NOT EXISTS 'coach'")

    # ── 2. Add subscription_status to users ──────────────────────────────────
    # Values: free_trial | active | expired | none
    # We use a plain VARCHAR so we don't need another ENUM type —
    # easier to extend later when we add new tiers.
    op.add_column('users', sa.Column(
        'subscription_status',
        sa.String(length=20),
        nullable=False,
        server_default='free_trial',
    ))
    op.add_column('users', sa.Column(
        'trial_ends_at',
        sa.DateTime(timezone=True),
        nullable=True,
    ))
    op.add_column('users', sa.Column(
        'subscription_started_at',
        sa.DateTime(timezone=True),
        nullable=True,
    ))

    # ── 3. Extend mock_interviews for proctored sessions ─────────────────────
    op.add_column('mock_interviews', sa.Column(
        'is_proctored', sa.Boolean(), nullable=False, server_default='false'
    ))
    op.add_column('mock_interviews', sa.Column(
        'time_limit_minutes', sa.Integer(), nullable=False, server_default='30'
    ))
    op.add_column('mock_interviews', sa.Column(
        'tab_switches', sa.Integer(), nullable=False, server_default='0'
    ))
    op.add_column('mock_interviews', sa.Column(
        'camera_active', sa.Boolean(), nullable=False, server_default='false'
    ))
    # Stores per-question breakdown: [{question, answer, score, feedback, ideal_answer}]
    op.add_column('mock_interviews', sa.Column(
        'question_breakdown',
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    ))
    op.add_column('mock_interviews', sa.Column(
        'verdict', sa.String(length=20), nullable=True
    ))  # "pass" | "borderline" | "fail"


def downgrade():
    op.drop_column('mock_interviews', 'verdict')
    op.drop_column('mock_interviews', 'question_breakdown')
    op.drop_column('mock_interviews', 'camera_active')
    op.drop_column('mock_interviews', 'tab_switches')
    op.drop_column('mock_interviews', 'time_limit_minutes')
    op.drop_column('mock_interviews', 'is_proctored')

    op.drop_column('users', 'subscription_started_at')
    op.drop_column('users', 'trial_ends_at')
    op.drop_column('users', 'subscription_status')

    # Note: PostgreSQL does not support removing values from an ENUM type.
    # To fully revert the contexttype change, you would need to recreate the type.
