"""add otp codes and signup flow.

Revision ID: 0016_auth
Revises: 0015_settlement
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_auth"
down_revision: str | Sequence[str] | None = "0015_settlement"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "otp_codes",
        sa.Column("phone_e164", sa.String(length=16), primary_key=True),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "purpose in ('signup', 'login', 'reset')",
            name="otp_purpose",
        ),
    )
    op.create_index(
        "ix_otp_expires_at",
        "otp_codes",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_otp_expires_at",
        table_name="otp_codes",
    )
    op.drop_table("otp_codes")