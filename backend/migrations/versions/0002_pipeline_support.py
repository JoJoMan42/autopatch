"""Retrieval, LLM logging, and job tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-07

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from patchpilot.config import get_settings
from patchpilot.constants import JobStatus, JobType
from patchpilot.db.models.code_chunk import EMBEDDING_DIM
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enum_check(column: str, enum_cls: type, name: str) -> sa.CheckConstraint:
    values = ", ".join(f"'{member.value}'" for member in enum_cls)
    return sa.CheckConstraint(f'"{column}" IN ({values})', name=name)


def _pk() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=False),
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


def upgrade() -> None:
    """Create the vector extension and the pipeline support tables."""
    if EMBEDDING_DIM != get_settings().embedding_dim:
        raise RuntimeError("EMBEDDING_DIM must match Settings.embedding_dim")

    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.create_table(
        "code_chunks",
        _pk(),
        sa.Column("kind", sa.Text(), nullable=False, server_default="code"),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "projects.id",
                name="fk_code_chunks_project_id_projects",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
        sa.Column("commit_sha", sa.CHAR(length=40), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "body_tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple', body)", persisted=True),
            nullable=True,
        ),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("cwe", sa.String(length=32), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_code_chunks"),
        sa.CheckConstraint(
            "kind IN ('code', 'knowledge')",
            name="kind_values",
        ),
    )
    op.create_index(
        "uq_code_chunks_project_commit_path_lines",
        "code_chunks",
        ["project_id", "commit_sha", "file_path", "start_line", "end_line"],
        unique=True,
    )
    op.create_index(
        "ix_code_chunks_embedding_hnsw",
        "code_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_code_chunks_body_tsv",
        "code_chunks",
        ["body_tsv"],
        postgresql_using="gin",
    )
    op.create_table(
        "prompts",
        _pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("sha256", sa.CHAR(length=64), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_prompts"),
        sa.UniqueConstraint("name", "version", name="uq_prompts_name_version"),
    )
    op.create_table(
        "jobs",
        _pk(),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "projects.id", name="fk_jobs_project_id_projects", ondelete="RESTRICT"
            ),
            nullable=True,
        ),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "findings.id", name="fk_jobs_finding_id_findings", ondelete="RESTRICT"
            ),
            nullable=True,
        ),
        sa.Column(
            "patch_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "patch_candidates.id",
                name="fk_jobs_patch_id_patch_candidates",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
        # experiments does not exist yet; migration 0003 adds the foreign key.
        sa.Column("experiment_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", name="fk_jobs_created_by_users", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("correlation_id", sa.Text(), nullable=False),
        sa.Column("celery_task_id", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
        _enum_check("type", JobType, "type_enum"),
        _enum_check("status", JobStatus, "status_enum"),
    )
    op.create_foreign_key(
        "fk_scans_job_id_jobs",
        "scans",
        "jobs",
        ["job_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_patch_candidates_job_id_jobs",
        "patch_candidates",
        "jobs",
        ["job_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_table(
        "llm_calls",
        _pk(),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("jobs.id", name="fk_llm_calls_job_id_jobs", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "patch_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "patch_candidates.id",
                name="fk_llm_calls_patch_id_patch_candidates",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("params", postgresql.JSONB(), nullable=False),
        sa.Column("prompt_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("prompt_uri", sa.Text(), nullable=True),
        sa.Column("response_uri", sa.Text(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ok"),
        sa.Column("error", sa.Text(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_llm_calls"),
        sa.CheckConstraint("status IN ('ok', 'error')", name="status_values"),
    )
    op.create_table(
        "job_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("jobs.id", name="fk_job_events_job_id_jobs", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_job_events"),
        sa.UniqueConstraint("job_id", "seq", name="uq_job_events_job_id_seq"),
    )


def downgrade() -> None:
    """Drop pipeline tables and the foreign keys added onto the core tables."""
    op.drop_table("job_events")
    op.drop_table("llm_calls")
    op.drop_constraint("fk_patch_candidates_job_id_jobs", "patch_candidates", type_="foreignkey")
    op.drop_constraint("fk_scans_job_id_jobs", "scans", type_="foreignkey")
    op.drop_table("jobs")
    op.drop_table("prompts")
    op.drop_index("ix_code_chunks_body_tsv", table_name="code_chunks")
    op.drop_index("ix_code_chunks_embedding_hnsw", table_name="code_chunks")
    op.drop_index("uq_code_chunks_project_commit_path_lines", table_name="code_chunks")
    op.drop_table("code_chunks")
