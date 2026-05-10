"""Telegram WebApp auth endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.schemas.telegram_webapp import TelegramWebAppAuthRequest, TelegramWebAppAuthResponse
from app.services.telegram_webapp_auth import TelegramWebAppAuthError, validate_telegram_webapp_init_data

router = APIRouter(prefix="/telegram/webapp", tags=["telegram-webapp"])


@router.post("/auth", response_model=TelegramWebAppAuthResponse)
async def telegram_webapp_auth(body: TelegramWebAppAuthRequest) -> TelegramWebAppAuthResponse:
    """Validate Telegram WebApp initData signature and return verified user subset."""
    try:
        payload = validate_telegram_webapp_init_data(body.initData, settings.TELEGRAM_BOT_TOKEN)
    except TelegramWebAppAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return TelegramWebAppAuthResponse(**payload)
