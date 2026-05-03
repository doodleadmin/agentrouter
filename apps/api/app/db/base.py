"""Declarative base and shared SQLAlchemy model mixins."""

from datetime import datetime
from uuid import UUID as _UUID
from uuid import uuid4

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarative model with common metadata naming conventions."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """Common created/updated timestamp fields for domain entities."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class UUIDPrimaryKeyMixin:
    """Common UUID primary key field."""

    @declared_attr.directive
    def id(self) -> Mapped[_UUID]:  # noqa: N805
        return mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
