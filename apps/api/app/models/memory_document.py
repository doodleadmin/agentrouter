"""Memory document model for indexed markdown files."""

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MemoryDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Indexed logical memory document and its latest content hash."""

    __tablename__ = "memory_documents"
    __table_args__ = (
        # NOTE: unique(scope, project_id, path) with nullable project_id may require
        # a partial unique index strategy; deferred for follow-up.
        Index("idx_memory_docs_scope", "scope"),
        Index("idx_memory_docs_scope_project_path", "scope", "project_id", "path"),
    )

    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
