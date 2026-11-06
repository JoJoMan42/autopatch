"""Core relational tables.

Revision ID: 0001
Revises:
Create Date: 2026-11-07

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from patchpilot.constants import (
    FindingStatus,
    PatchState,
    ReviewDecision,
    Role,
    Severity,
    StageName,
    StageOutcome,
    Verdict,
)
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enum_check(column: str, enum_cls: type, name: str) -> sa.CheckConstraint:
    values = ", ".join(f"'{member.value}'" for member in enum_cls)
    return sa.CheckConstraint(f'"{column}" IN ({values})', name=name)


def _uuid(name: str, *, nullable: bool = False) -> sa.Column:
    return sa.Column(name, postgresql.UUID(as_uuid=False), nullable=nullable)


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
    """Create users, projects, scans, findings, patches, validation runs, and reviews."""
    op.create_table(
        "users",
        _pk(),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint("email = lower(email)", name="email_lowercase"),
        _enum_check("role", Role, "role_enum"),
    )
    op.create_table(
        "projects",
        _pk(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("repo_url", sa.Text(), nullable=True),
        sa.Column("local_path", sa.Text(), nullable=True),
        sa.Column(
            "default_branch",
            sa.String(length=255),
            nullable=False,
            server_default="main",
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", name="fk_projects_created_by_users", ondelete="RESTRICT"),
            nullable=False,
        ),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
        sa.UniqueConstraint("name", name="uq_projects_name"),
        sa.CheckConstraint(
            "(repo_url IS NOT NULL AND local_path IS NULL) "
            "OR (repo_url IS NULL AND local_path IS NOT NULL)",
            name="source_xor",
        ),
    )
    op.create_table(
        "scans",
        _pk(),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "projects.id", name="fk_scans_project_id_projects", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column("commit_sha", sa.CHAR(length=40), nullable=False),
        sa.Column("scanner", sa.Text(), nullable=False),
        sa.Column("scanner_ver", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        # jobs does not exist yet; migration 0002 adds fk_scans_job_id_jobs.
        _uuid("job_id", nullable=True),
        sa.Column("summary", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_scans"),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'done', 'failed')",
            name="status_values",
        ),
    )
    op.create_table(
        "findings",
        _pk(),
        sa.Column(
            "scan_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("scans.id", name="fk_findings_scan_id_scans", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "projects.id", name="fk_findings_project_id_projects", ondelete="RESTRICT"
            ),
            nullable=False,
        ),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column("rule_id", sa.Text(), nullable=False),
        sa.Column("scanner", sa.Text(), nullable=False),
        sa.Column("cwe", sa.Text(), nullable=True),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_sarif", postgresql.JSONB(), nullable=False),
        sa.Column("code_slice", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_findings"),
        sa.UniqueConstraint(
            "scan_id", "fingerprint", name="uq_findings_scan_id_fingerprint"
        ),
        _enum_check("severity", Severity, "severity_enum"),
        _enum_check("status", FindingStatus, "status_enum"),
    )
    op.create_index("ix_findings_scan_id_severity", "findings", ["scan_id", "severity"])
    op.create_index(
        "ix_findings_status_open",
        "findings",
        ["status"],
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_table(
        "patch_candidates",
        _pk(),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "findings.id",
                name="fk_patch_candidates_finding_id_findings",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        # jobs does not exist yet; migration 0002 adds fk_patch_candidates_job_id_jobs.
        _uuid("job_id", nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("params", postgresql.JSONB(), nullable=False),
        sa.Column("retrieved_chunk_ids", postgresql.JSONB(), nullable=False),
        sa.Column("unified_diff", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("analysis", sa.Text(), nullable=False),
        sa.Column("assumptions", postgresql.JSONB(), nullable=False),
        sa.Column("risks", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Numeric(4, 3), nullable=False, server_default="0"),
        sa.Column("judge", postgresql.JSONB(), nullable=True),
        sa.Column("generated_test", postgresql.JSONB(), nullable=True),
        sa.Column("base_commit", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="proposed"),
        sa.Column("verdict", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_patch_candidates"),
        sa.UniqueConstraint(
            "finding_id", "attempt", name="uq_patch_candidates_finding_id_attempt"
        ),
        _enum_check("state", PatchState, "state_enum"),
        _enum_check("verdict", Verdict, "verdict_enum"),
    )
    op.create_index("ix_patch_candidates_finding_id", "patch_candidates", ["finding_id"])
    op.create_table(
        "validation_runs",
        _pk(),
        sa.Column(
            "patch_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "patch_candidates.id",
                name="fk_validation_runs_patch_id_patch_candidates",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("log_uri", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_validation_runs"),
        _enum_check("stage", StageName, "stage_enum"),
        _enum_check("outcome", StageOutcome, "outcome_enum"),
    )
    op.create_index(
        "ix_validation_runs_patch_id_stage",
        "validation_runs",
        ["patch_id", "stage"],
    )
    op.create_table(
        "reviews",
        _pk(),
        sa.Column(
            "patch_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey(
                "patch_candidates.id",
                name="fk_reviews_patch_id_patch_candidates",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", name="fk_reviews_reviewer_id_users", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "include_generated_test",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reviews"),
        _enum_check("decision", ReviewDecision, "decision_enum"),
    )


def downgrade() -> None:
    """Drop the core tables in reverse dependency order."""
    op.drop_table("reviews")
    op.drop_index("ix_validation_runs_patch_id_stage", table_name="validation_runs")
    op.drop_table("validation_runs")
    op.drop_index("ix_patch_candidates_finding_id", table_name="patch_candidates")
    op.drop_table("patch_candidates")
    op.drop_index("ix_findings_status_open", table_name="findings")
    op.drop_index("ix_findings_scan_id_severity", table_name="findings")
    op.drop_table("findings")
    op.drop_table("scans")
    op.drop_table("projects")
    op.drop_table("users")
