"""Alembic environment configuration for offline/online migrations."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.db.base import Base
import app.models  # noqa: F401  # required for model registration


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def _validate_migration_safety() -> None:
    """Fail-fast if migration targets production/staging database."""
    url = config.get_main_option("sqlalchemy.url")
    if url:
        url_lower = url.lower()
        blocked_hosts = ["prod", "staging", "rds.amazonaws.com"]
        for blocked in blocked_hosts:
            if blocked in url_lower:
                raise RuntimeError(
                    f"Refusing to run migrations against non-dev database"
                )
    # NOTE: We do NOT inspect Base.metadata.tables here because
    # metadata != DB state -- that check would be misleading.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    _validate_migration_safety()

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    """Sync callback for run_sync — executes within async engine connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    _validate_migration_safety()

    url = config.get_main_option("sqlalchemy.url")
    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(_do_run_migrations)

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
