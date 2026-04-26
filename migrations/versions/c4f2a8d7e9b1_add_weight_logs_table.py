"""add weight_logs table

Revision ID: c4f2a8d7e9b1
Revises: a29fa99b4275
Create Date: 2026-04-24 15:32:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c4f2a8d7e9b1"
down_revision = "a29fa99b4275"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "weight_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index(op.f("ix_weight_logs_user_id"), "weight_logs", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_weight_logs_recorded_at"),
        "weight_logs",
        ["recorded_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_weight_logs_recorded_at"), table_name="weight_logs")
    op.drop_index(op.f("ix_weight_logs_user_id"), table_name="weight_logs")
    op.drop_table("weight_logs")
