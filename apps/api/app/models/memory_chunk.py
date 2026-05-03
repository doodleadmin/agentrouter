"""Memory chunk model for vector retrieval."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MemoryChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Chunk-level embedding for semantic memory search."""

    __tablename__ = "memory_chunks"
    __table_args__ = (
        Index("idx_memory_chunks_project", "project_id"),
    )

    document_id: Mapped[str] = mapped_column(
        ForeignKey("memory_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    chunk_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )
