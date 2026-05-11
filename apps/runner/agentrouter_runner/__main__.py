"""Module entrypoint for `python -m agentrouter_runner`."""

from .cli import run


if __name__ == "__main__":
    raise SystemExit(run())
