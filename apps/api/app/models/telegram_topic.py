"""Telegram topic-to-domain mapping model."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.enums import TopicKind


class TelegramTopic(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Binding between Telegram forum topics and project/agent contexts."""

    __tablename__ = "telegram_topics"
    __table_args__ = (
        UniqueConstraint("chat_id", "message_thread_id", name="uq_telegram_topics_chat_thread"),
    )

    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    message_thread_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default=TopicKind.GENERAL.value, index=True)
    agent_id: Mapped[str | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
