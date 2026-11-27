"""add unique constraint to refresh token hashes

Revision ID: a1b2c3d4e5f6
Revises: eb3d7de2b26c
"""

from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "eb3d7de2b26c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_refresh_tokens_token_hash", "refresh_tokens", type_="unique"
    )
