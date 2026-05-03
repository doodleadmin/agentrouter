"""Agents router — CRUD with soft-disable."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])


def _svc(s: AsyncSession = Depends(get_async_session)) -> AgentService:
    return AgentService(s)


_AGENT_404 = "Agent not found"


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: AgentCreate,
    svc: AgentService = Depends(_svc),
) -> AgentRead:
    return AgentRead.model_validate(await svc.create(body))


@router.get("", response_model=list[AgentRead])
async def list_agents(
    active_only: bool = Query(False),
    svc: AgentService = Depends(_svc),
) -> list[AgentRead]:
    results = await svc.list(active_only=active_only)
    return [AgentRead.model_validate(r) for r in results]


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: UUID,
    svc: AgentService = Depends(_svc),
) -> AgentRead:
    obj = await svc.get(agent_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_AGENT_404)
    return AgentRead.model_validate(obj)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: UUID,
    body: AgentUpdate,
    svc: AgentService = Depends(_svc),
) -> AgentRead:
    obj = await svc.update(agent_id, body)
    if obj is None:
        raise HTTPException(status_code=404, detail=_AGENT_404)
    return AgentRead.model_validate(obj)


@router.delete("/{agent_id}", response_model=AgentRead, status_code=status.HTTP_200_OK)
async def disable_agent(
    agent_id: UUID,
    svc: AgentService = Depends(_svc),
) -> AgentRead:
    obj = await svc.disable(agent_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=_AGENT_404)
    return AgentRead.model_validate(obj)
