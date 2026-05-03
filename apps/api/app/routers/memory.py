"""Memory router — CRUD + indexing + retrieval endpoints for .ai_memory vault."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.schemas.memory import (
    MemoryAccessInfo,
    MemoryFileListResult,
    MemoryFileRead,
    MemoryFileWrite,
    MemoryFileWriteRequest,
    MemoryProvisionRequest,
    MemoryProvisionResult,
    MemoryReindexRequest,
    MemoryReindexResponse,
    MemorySearchRequest,
    MemorySearchResponse,
)
from app.services.memory_indexing_service import MemoryIndexingService
from app.services.memory_policy_service import (
    PathValidationError,
    SecretsDetectedError,
    WriteForbiddenError,
)
from app.services.memory_provisioning_service import MemoryProvisioningService
from app.services.memory_retrieval_service import (
    MemoryRetrievalService,
    SqlAlchemyRetrievalRepository,
)
from app.services.memory_service import MemoryFileNotFoundError, MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


def _svc() -> MemoryService:
    return MemoryService()


def _prov() -> MemoryProvisioningService:
    return MemoryProvisioningService()


def _db_session(s: AsyncSession = Depends(get_async_session)) -> AsyncSession:
    return s


@router.get("/files", response_model=MemoryFileListResult)
def list_files(
    prefix: str | None = Query(None, description="Path prefix filter"),
    project_slug: str | None = Query(None, description="Project slug filter"),
) -> MemoryFileListResult:
    """List markdown files in the vault, optionally filtered."""
    svc = _svc()
    return svc.list_files(prefix=prefix, project_slug=project_slug)


@router.get("/files/{path:path}", response_model=MemoryFileRead)
def read_file(path: str) -> MemoryFileRead:
    """Read a markdown file from the vault."""
    svc = _svc()
    try:
        return svc.read_file(path)
    except MemoryFileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except PathValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/files/{path:path}/append", response_model=MemoryFileWrite)
def append_file(
    path: str,
    body: MemoryFileWriteRequest,
    bypass_approval: bool = Query(False, description="System-level bypass"),
) -> MemoryFileWrite:
    """Append content to a memory file."""
    svc = _svc()
    try:
        return svc.append_file(path, body.content, bypass_approval=bypass_approval)
    except PathValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SecretsDetectedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except WriteForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/files/{path:path}", response_model=MemoryFileWrite)
def write_file(
    path: str,
    body: MemoryFileWriteRequest,
    bypass_approval: bool = Query(False, description="System-level bypass"),
) -> MemoryFileWrite:
    """Write (create or replace) a memory file."""
    svc = _svc()
    try:
        return svc.write_file(path, body.content, bypass_approval=bypass_approval)
    except PathValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SecretsDetectedError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except WriteForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/projects/{slug}/provision", response_model=MemoryProvisionResult)
def provision_project(slug: str, body: MemoryProvisionRequest) -> MemoryProvisionResult:
    """Provision memory vault for a project."""
    if slug != body.slug:
        raise HTTPException(
            status_code=400,
            detail=f"Slug mismatch: URL has '{slug}', body has '{body.slug}'",
        )
    prov = _prov()
    return prov.provision_project(slug, body.name)


@router.get("/access", response_model=MemoryAccessInfo)
def get_access_info(path: str = Query(..., description="Memory file path")) -> MemoryAccessInfo:
    """Get access tier info for a path."""
    svc = _svc()
    tier = svc.get_access_tier(path)
    return MemoryAccessInfo(path=path, access_tier=tier)


@router.post("/reindex", response_model=MemoryReindexResponse)
async def reindex_memory(
    body: MemoryReindexRequest,
    session: AsyncSession = Depends(_db_session),
) -> MemoryReindexResponse:
    """Run manual memory reindexing for selected scope."""
    svc = MemoryIndexingService(session)
    try:
        result = await svc.reindex(scope=body.scope, project_slug=body.project_slug)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return MemoryReindexResponse(
        scope=body.scope,
        project_slug=body.project_slug,
        scanned_files=result.scanned_files,
        indexed_documents=result.indexed_documents,
        skipped_documents=result.skipped_documents,
        total_chunks=result.total_chunks,
    )


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    body: MemorySearchRequest,
    session: AsyncSession = Depends(_db_session),
) -> MemorySearchResponse:
    """Search indexed memory chunks using deterministic embeddings."""
    repo = SqlAlchemyRetrievalRepository(session)
    svc = MemoryRetrievalService(repo)
    items = await svc.search(
        query=body.query,
        project_slug=body.project_slug,
        limit=body.limit,
        scope=body.scope,
    )
    return MemorySearchResponse(
        query=body.query,
        total=len(items),
        items=[
            {
                "path": i.path,
                "title": i.title,
                "scope": i.scope,
                "project_slug": i.project_slug,
                "heading": i.heading,
                "chunk_index": i.chunk_index,
                "content": i.content,
                "score": i.score,
            }
            for i in items
        ],
    )
