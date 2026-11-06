from __future__ import annotations

from logging.config import fileConfig

import patchpilot.db.models  # noqa: F401  # register every model on Base.metadata
from alembic import context
from patchpilot.config import get_settings
from patchpilot.db.base import Base
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# pgvector may reflect operator-class indexes that are not part of our metadata.
_PGVECTOR_INDEX_MARKERS = ("hnsw", "ivfflat", "vector_cosine", "vector_l2", "vector_ip")


def include_object(
    obj: object,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: object | None,
) -> bool:
    """Skip reflected pgvector internal indexes that the models do not declare."""
    if type_ == "index" and reflected and compare_to is None:
        lowered = (name or "").lower()
        if any(marker in lowered for marker in _PGVECTOR_INDEX_MARKERS):
            return False
        table = getattr(obj, "table", None)
        columns = getattr(obj, "columns", None)
        if table is not None and getattr(table, "name", None) == "code_chunks" and columns:
            for column in columns:
                if getattr(column, "name", None) == "embedding":
                    return False
    return True


def _database_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations without a DBAPI connection."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live connection, one transaction per revision."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
            transaction_per_migration=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
