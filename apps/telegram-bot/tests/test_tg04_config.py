"""Tests for TG-04 config additions: TELEGRAM_ADMIN_USER_IDS + .env.local support."""

from app.config import Settings


class TestTelegramAdminUserIds:
    """Safe config parsing and fail-closed behaviour for admin allowlist."""

    def test_default_is_empty_list(self, monkeypatch) -> None:
        """Empty env = empty list = admin actions fail-closed (no one is admin)."""
        monkeypatch.delenv("TELEGRAM_ADMIN_USER_IDS", raising=False)
        s = Settings(_env_file=None)
        assert s.admin_user_ids() == []

    def test_comma_separated_ids_parsed(self, monkeypatch) -> None:
        """Config parses '123,456' -> [123, 456]."""
        monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "123,456")
        s = Settings(_env_file=None)
        assert s.admin_user_ids() == [123, 456]

    def test_single_id_parsed(self, monkeypatch) -> None:
        monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "777888999")
        s = Settings(_env_file=None)
        assert s.admin_user_ids() == [777888999]

    def test_env_file_supports_local_override(self) -> None:
        """model_config uses (".env", ".env.local") tuple."""
        assert Settings.model_config.get("env_file") == (".env", ".env.local")

    def test_admin_user_ids_invalid_causes_fail_closed(self, monkeypatch) -> None:
        """Non-integer values cause entire list to fail-closed (return [])."""
        monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "123,abc,456")
        s = Settings(_env_file=None)
        # Fail-closed: any invalid token results in empty list (safety).
        assert s.admin_user_ids() == []


def test_webapp_url_config_supported(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_WEBAPP_URL", "https://example.com/app")
    s = Settings(_env_file=None)
    assert s.TELEGRAM_WEBAPP_URL == "https://example.com/app"
