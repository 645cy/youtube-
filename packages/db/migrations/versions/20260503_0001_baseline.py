"""baseline current schema"""

from __future__ import annotations

from alembic import op

from packages.db.schema import Base

revision = "20260503_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # CRG: Baseline migration captures the current SQLAlchemy metadata without a hand-copied giant DDL diff.
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    # CRG: Downgrade is reversible for fresh environments; production rollbacks should use backups first.
    Base.metadata.drop_all(bind=bind)
