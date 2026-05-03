"""
Agent Mission Control — Orchestrator API

FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    # TODO: initialize DB connection pool, Redis, etc.
    yield
    # Shutdown
    # TODO: close connections gracefully


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Agent Mission Control API",
        description="Orchestration platform for AI agent management",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from app.routers import (
        agents_router,
        approvals_router,
        health_router,
        memory_router,
        projects_router,
        runtime_router,
        task_events_router,
        tasks_router,
        telegram_topics_router,
    )

    app.include_router(health_router)
    app.include_router(projects_router)
    app.include_router(agents_router)
    app.include_router(telegram_topics_router)
    app.include_router(tasks_router)
    app.include_router(approvals_router)
    app.include_router(task_events_router)
    app.include_router(runtime_router)
    app.include_router(memory_router)

    return app


app = create_app()
