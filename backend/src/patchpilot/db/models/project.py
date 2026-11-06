from __future__ import annotations

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.db.base import Base, TimestampMixin, uuid_fk, uuid_pk


class ProjectModel(Base, TimestampMixin):
    """Registered repository. Exactly one of repo_url or local_path is set."""

    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "(repo_url IS NOT NULL AND local_path IS NULL) "
            "OR (repo_url IS NULL AND local_path IS NOT NULL)",
            name="source_xor",
        ),
    )

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    repo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(
        String(255), nullable=False, default="main", server_default="main"
    )
    created_by: Mapped[str] = uuid_fk("users.id")

    scans: Mapped[list[ScanModel]] = relationship(
        back_populates="project",
        lazy="raise",
    )


from patchpilot.db.models.scan import ScanModel
