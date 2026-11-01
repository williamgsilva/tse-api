import sys

import httpx

from ..modules.open_data.interfaces.cli import run
from ..shared.config import Settings
from ..shared.errors import AppError
from ..shared.observability import configure_logging
from .container import build_ingest_container


def main(argv: list[str] | None = None) -> int:
    settings = Settings()
    configure_logging(settings.log_level, "text")
    with httpx.Client(
        timeout=httpx.Timeout(60.0, read=600.0), follow_redirects=True, headers={"User-Agent": settings.user_agent}
    ) as http:
        container = build_ingest_container(settings, http)
        try:
            return run(argv, container.available, container.importer)
        except AppError as exc:
            print(f"erro: {exc.detail}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
