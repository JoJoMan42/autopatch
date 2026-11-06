"""Audit trail, experiments, and append-only enforcement.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-07

The application database role should have INSERT and SELECT only on
audit_events, validation_runs, and job_events. The trigger below is a
second barrier: UPDATE and DELETE still fail if those grants are widened.

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_APPEND_ONLY_TABLES = ("audit_events", "validation_runs", "job_events")

_FORBID_UPDATE_DELETE = """
CREATE OR REPLACE FUNCTION pp_forbid_update_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Table % is append-only: UPDATE and DELETE are prohibited', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql
"""


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
    """Create audit and experiment tables, then attach append-only triggers."""
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("prev_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("hash", sa.CHAR(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
        sa.UniqueConstraint("hash", name="uq_audit_events_hash"),
    )
    op.create_table(
        "benchmark_cases",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("cwe", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("project_ref", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("line", sa.Integer(), nullable=False),
        sa.Column("split", sa.Text(), nullable=False),
        sa.Column("ground_truth", postgresql.JSONB(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_benchmark_cases"),
        sa.CheckConstraint(
            "source IN ('injected', 'curated')",
            name="source_values",
        ),
        sa.CheckConstraint(
            "split IN ('dev', 'test')",
            name="split_values",
        ),
    )
    op.create_table(
        "experiments",
        _pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("git_sha", sa.CHAR(length=40), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("jobs.id", name="fk_experiments_job_id_jobs", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "users.id", name="fk_experiments_created_by_users", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_experiments"),
    )
    op.create_foreign_key(
        "fk_jobs_experiment_id_experiments",
        "jobs",
        "experiments",
        ["experiment_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_table(
        "experiment_runs",
        _pk(),
        sa.Column(
            "experiment_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "experiments.id",
                name="fk_experiment_runs_experiment_id_experiments",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            sa.Text(),
            sa.ForeignKey(
                "benchmark_cases.id",
                name="fk_experiment_runs_case_id_benchmark_cases",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("variant", sa.Text(), nullable=False),
        sa.Column("sample_idx", sa.Integer(), nullable=False),
        sa.Column(
            "patch_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "patch_candidates.id",
                name="fk_experiment_runs_patch_id_patch_candidates",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "findings.id",
                name="fk_experiment_runs_finding_id_findings",
                ondelete="RESTRICT",
            ),
            nullable=True,
        ),
        sa.Column("outcome", postgresql.JSONB(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_experiment_runs"),
        sa.UniqueConstraint(
            "experiment_id",
            "case_id",
            "variant",
            "sample_idx",
            name="uq_experiment_runs_case_variant_sample",
        ),
    )
    op.execute(_FORBID_UPDATE_DELETE)
    for table_name in _APPEND_ONLY_TABLES:
        op.execute(
            sa.text(
                f"CREATE TRIGGER trg_{table_name}_append_only "
                f"BEFORE UPDATE OR DELETE ON {table_name} "
                "FOR EACH ROW EXECUTE FUNCTION pp_forbid_update_delete()"
            )
        )


def downgrade() -> None:
    """Drop append-only triggers and the function, then the tables."""
    for table_name in reversed(_APPEND_ONLY_TABLES):
        op.execute(
            sa.text(f"DROP TRIGGER IF EXISTS trg_{table_name}_append_only ON {table_name}")
        )
    op.execute(sa.text("DROP FUNCTION IF EXISTS pp_forbid_update_delete()"))
    op.drop_table("experiment_runs")
    op.drop_constraint(
        "fk_jobs_experiment_id_experiments", "jobs", type_="foreignkey"
    )
    op.drop_table("experiments")
    op.drop_table("benchmark_cases")
    op.drop_table("audit_events")
