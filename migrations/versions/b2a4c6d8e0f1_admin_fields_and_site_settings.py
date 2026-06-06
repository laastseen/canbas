"""admin fields and site settings

Revision ID: b2a4c6d8e0f1
Revises: 0a5c613a3a00
Create Date: 2026-06-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b2a4c6d8e0f1"
down_revision = "0a5c613a3a00"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"))

    op.create_table(
        "site_setting",
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade():
    op.drop_table("site_setting")
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("is_active")
        batch_op.drop_column("is_superadmin")
