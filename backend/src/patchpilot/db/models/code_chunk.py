from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import CHAR, CheckConstraint, Computed, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column

from patchpilot.db.base import Base, TimestampMixin, uuid_fk, uuid_pk

# Must match Settings.embedding_dim and migration 0002.
EMBEDDING_DIM = 768


class _BodyTsvComputed(Computed):
    """Generated tsvector on PostgreSQL. SQLite stores a plain column so unit tests can create_all."""


@compiles(_BodyTsvComputed, "sqlite")
def _compile_body_tsv_sqlite(element: Computed, compiler: object, **kw: object) -> str:
    return ""


class CodeChunkModel(Base, TimestampMixin):
    """Indexed source or knowledge chunk. body_tsv is generated from body."""

    __tablename__ = "code_chunks"
    __table_args__ = (
        CheckConstraint("kind IN ('code', 'knowledge')", name="kind_values"),
        Index(
            "uq_code_chunks_project_commit_path_lines",
            "project_id",
            "commit_sha",
            "file_path",
            "start_line",
            "end_line",
            unique=True,
        ),
        Index(
            "ix_code_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_code_chunks_body_tsv", "body_tsv", postgresql_using="gin"),
    )

    id: Mapped[str] = uuid_pk()
    kind: Mapped[str] = mapped_column(Text, nullable=False, default="code", server_default="code")
    project_id: Mapped[str | None] = uuid_fk("projects.id", nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(CHAR(40), nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    symbol: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR().with_variant(Text(), "sqlite"),
        _BodyTsvComputed("to_tsvector('simple', body)", persisted=True),
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    cwe: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
