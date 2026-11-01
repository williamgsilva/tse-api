"""Base dos schemas HTTP: atributos em inglês no código, campos em português no JSON (ADR 0003)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


def pt(alias: str, default: Any = ..., **kwargs: Any) -> Any:
    """Campo cujo nome no JSON é ``alias`` (português) e no código é o nome do atributo (inglês)."""
    return Field(default, serialization_alias=alias, **kwargs)
