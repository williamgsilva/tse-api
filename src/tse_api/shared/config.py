import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_env: str = field(default_factory=lambda: _env("APP_ENV", "development"))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "info"))
    log_format: str = field(default_factory=lambda: _env("LOG_FORMAT", "json"))
    tse_results_base_url: str = field(
        default_factory=lambda: _env("TSE_RESULTADOS_BASE", "https://resultados.tse.jus.br/oficial")
    )
    tse_open_data_base_url: str = field(
        default_factory=lambda: _env("TSE_DADOS_ABERTOS_BASE", "https://dadosabertos.tse.jus.br")
    )
    ibge_meshes_base_url: str = field(
        default_factory=lambda: _env("IBGE_MALHAS_BASE", "https://servicodados.ibge.gov.br/api/v3/malhas")
    )
    # Os JSONs do portal quase não mudam após a totalização, mas o catálogo pode ganhar
    # eleições suplementares; por isso o cache em memória expira.
    json_cache_ttl_seconds: int = field(default_factory=lambda: int(_env("TSE_JSON_TTL", "900")))
    max_upstream_concurrency: int = field(default_factory=lambda: int(_env("TSE_MAX_CONCURRENCY", "16")))
    user_agent: str = field(default_factory=lambda: _env("TSE_USER_AGENT", "tse-api/0.1 (consulta de dados publicos)"))
    data_dir: Path = field(default_factory=lambda: Path(_env("TSE_DATA_DIR", "data")))
    database_path_override: str = field(default_factory=lambda: _env("TSE_DB_PATH", ""))
    frontend_dist: Path = field(default_factory=lambda: Path(_env("FRONTEND_DIST", "frontend/dist")))
    cors_origins: tuple[str, ...] = field(default_factory=lambda: _csv(_env("CORS_ORIGINS", "")))

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def database_path(self) -> Path:
        return Path(self.database_path_override) if self.database_path_override else self.data_dir / "bweb.duckdb"
