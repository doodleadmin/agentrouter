"""SEC-03B: Config defaults — SQL_ECHO must be False, decoupled from DEBUG."""
import pathlib

import pytest


class TestSqlEchoDecoupling:
    """SQL_ECHO must be independent of DEBUG to prevent SQLAlchemy bind param logging."""

    def test_sql_echo_default_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SQL_ECHO is False by default (no env var)."""
        monkeypatch.delenv("SQL_ECHO", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        from app.config import Settings
        s = Settings()
        assert s.SQL_ECHO is False

    def test_sql_echo_explicit_enable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SQL_ECHO=true via env — explicit opt-in works."""
        monkeypatch.setenv("SQL_ECHO", "true")
        monkeypatch.delenv("DEBUG", raising=False)
        from app.config import Settings
        s = Settings()
        assert s.SQL_ECHO is True

    def test_debug_true_does_not_imply_sql_echo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """DEBUG=true must NOT enable SQL_ECHO. They are decoupled."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.delenv("SQL_ECHO", raising=False)
        from app.config import Settings
        s = Settings()
        assert s.DEBUG is True
        assert s.SQL_ECHO is False


def test_session_py_uses_sql_echo_not_debug() -> None:
    """session.py must use settings.SQL_ECHO, not settings.DEBUG."""
    session_path = pathlib.Path(__file__).resolve().parent.parent / "app" / "db" / "session.py"
    content = session_path.read_text()
    # Must have echo=settings.SQL_ECHO
    assert "echo=settings.SQL_ECHO" in content, "session.py must use SQL_ECHO, not DEBUG"
    # Must NOT have echo=settings.DEBUG
    assert "echo=settings.DEBUG" not in content, "session.py must NOT use DEBUG for echo"
