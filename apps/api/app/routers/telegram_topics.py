"""Telegram topics router — CRUD with soft-deactivate."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas.telegram_topic import TelegramTopicCreate, TelegramTopicRead, TelegramTopicUpdate
from app.services.telegram_topic_service import TelegramTopicService

router = APIRouter(prefix="/telegram/topics", tags=["telegram-topics"])


def _svc(s: AsyncSession = Depends(get_async_session)) -> TelegramTopicService:
    return TelegramTopicService(s)


_TOPIC_404 = "Telegram topic not found"


@router.post("", response_model=TelegramTopicRead, status_code=status.HTTP_201_CREATED)
async def create_topic(
    body: TelegramTopicCreate,
    svc: TelegramTopicService = Depends(_svc),
) -> TelegramTopicRead:
    return TelegramTopicRead.model_validate(await svc.create(body))


@router.get("", response_model=list[TelegramTopicRead])
async def list_topics(
    active_only: bool = Query(False),
    svc: TelegramTopicService = Depends(_svc),
) -> list[TelegramTopicRead]:
    results = await svc.list(active_only=active_only)
    return [TelegramTopicRead.model_validate(r) for r in results]


@router.get("/{topic_id}", response_model=TelegramTopicRead)
async def get_topic(
    topic_id: UUID,
    svc: TelegramTopicService = Depends(_svc),
) -> TelegramTopicRead:
    obj = await svc.get(topic_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_TOPIC_404)
    return TelegramTopicRead.model_validate(obj)


@router.patch("/{topic_id}", response_model=TelegramTopicRead)
async def update_topic(
    topic_id: UUID,
    body: TelegramTopicUpdate,
    svc: TelegramTopicService = Depends(_svc),
) -> TelegramTopicRead:
    obj = await svc.update(topic_id, body)
    if obj is None:
        raise HTTPException(status_code=404, detail=_TOPIC_404)
    return TelegramTopicRead.model_validate(obj)


@router.delete("/{topic_id}", response_model=TelegramTopicRead, status_code=status.HTTP_200_OK)
async def deactivate_topic(
    topic_id: UUID,
    svc: TelegramTopicService = Depends(_svc),
) -> TelegramTopicRead:
    obj = await svc.deactivate(topic_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_TOPIC_404)
    return TelegramTopicRead.model_validate(obj)
