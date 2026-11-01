"""Serve o build do frontend (``frontend/dist``) na raiz, com fallback para o roteamento da SPA."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)


def mount_frontend(app: FastAPI, dist: Path, reserved_prefixes: tuple[str, ...]) -> None:
    index = dist / "index.html"
    if not index.is_file():
        logger.info("frontend não encontrado; servindo só a API", extra={"dist": str(dist)})
        return
    root = dist.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str) -> FileResponse:
        if f"/{path}".startswith(reserved_prefixes):
            raise HTTPException(404, "rota não encontrada")
        candidate = (root / path).resolve()
        # Impede path traversal: só arquivos dentro do diretório do build.
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        return FileResponse(index)
