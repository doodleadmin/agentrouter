"""Shared pytest fixtures for async HTTP + DB integration tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.base import Base
from app.db.session import get_async_session


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh DB session bound to one connection; tables created/dropped per test."""
    engine = create_async_engine(
        settings.DATABASE_URL, echo=False, future=True, poolclass=NullPool,
    )
    async with engine.connect() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

        await conn.begin()
        maker = async_sessionmaker(
            bind=conn, class_=AsyncSession, expire_on_commit=False,
        )
        session = maker()
        yield session
        await session.close()
        await conn.rollback()

        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()
    await engine.dispose()


@pytest.fixture
async def async_client(
    test_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with DB dependency overridden to test session."""
    from app.main import create_app

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app = create_app()
    app.dependency_overrides[get_async_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
