"""Tests for TG-04 SecretRedactionFilter — token/secret safety in logs."""
import logging

from app.logging import SecretRedactionFilter, install_redaction_filter


class TestSecretRedactionFilter:
    """Verify the logging filter masks sensitive patterns."""

    def test_redacts_bot_token(self) -> None:
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "Token: 1234567890:ABCDEFghijklmnopQRSTUVWXYZabcdefghij", (), None
        )
        SecretRedactionFilter().filter(record)
        assert "***BOT_TOKEN***" in record.msg
        assert "ABCDEFghijklmnop" not in record.msg

    def test_redacts_openai_key(self) -> None:
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "key=sk-proj-1234567890abcdef1234567890abcdef1234567890abcd", (), None
        )
        SecretRedactionFilter().filter(record)
        assert "***OPENAI_KEY***" in record.msg

    def test_redacts_bearer_token(self) -> None:
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc", (), None
        )
        SecretRedactionFilter().filter(record)
        assert "Bearer ***REDACTED***" in record.msg

    def test_redacts_db_password_in_url(self) -> None:
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "postgresql://user:secret123@host:5432/db", (), None
        )
        SecretRedactionFilter().filter(record)
        assert "secret123" not in record.msg
        assert "REDACTED" in record.msg

    def test_redacts_redis_password_in_url(self) -> None:
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "redis://:mypassword@localhost:6379/0", (), None
        )
        SecretRedactionFilter().filter(record)
        assert "mypassword" not in record.msg
        assert "REDACTED" in record.msg

    def test_benign_message_passes_through(self) -> None:
        msg = "[INFO] Bot polling started on localhost"
        record = logging.LogRecord("test", logging.INFO, "", 0, msg, (), None)
        SecretRedactionFilter().filter(record)
        assert record.msg == msg

    def test_install_does_not_double_attach(self) -> None:
        logger = logging.getLogger("tg04_test_dedup")
        install_redaction_filter("tg04_test_dedup")
        install_redaction_filter("tg04_test_dedup")
        count = sum(1 for f in logger.filters if isinstance(f, SecretRedactionFilter))
        assert count == 1
