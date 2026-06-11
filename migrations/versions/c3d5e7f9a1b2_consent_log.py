"""consent log

Revision ID: c3d5e7f9a1b2
Revises: b2a4c6d8e0f1
Create Date: 2026-06-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c3d5e7f9a1b2"
down_revision = "b2a4c6d8e0f1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "consent_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("consent_type", sa.String(length=50), nullable=False),
        sa.Column("policy_version", sa.String(length=20), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("consent_log")
