"""track verified signup phone OTPs.

Revision ID: 0017_signup
Revises: 0016_auth, 0016_vision
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_signup"
down_revision: str | Sequence[str] | None = ("0016_auth", "0016_vision")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "otp_codes",
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("otp_codes", "verified", server_default=None)
    op.add_column(
        "otp_codes",
        sa.Column("signup_payload", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("otp_codes", "signup_payload")
    op.drop_column("otp_codes", "verified")
