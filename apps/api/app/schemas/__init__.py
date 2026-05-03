"""Pydantic v2 schemas for API request/response contracts."""

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Validation or business logic error payload."""

    loc: list[str] = Field(default_factory=list)
    msg: str
    type: str = "value_error"


class ErrorResponse(BaseModel):
    """Standardised error envelope."""

    detail: str
    code: str = "internal_error"
    errors: list[ErrorDetail] = Field(default_factory=list)


class StatusUpdateIn(BaseModel):
    """Generic status-change request body."""

    status: str

    model_config = ConfigDict(extra="forbid")
