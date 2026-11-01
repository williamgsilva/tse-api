"""Cursor opaco para paginação de listas grandes (ver docs/standards/api.md)."""

import base64
import binascii
from dataclasses import dataclass
from typing import Generic, TypeVar

from .errors import InvalidInputError

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    total: int
    next_cursor: str | None


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"o:{offset}".encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        prefix, offset = raw.split(":", 1)
        if prefix != "o" or int(offset) < 0:
            raise ValueError(raw)
        return int(offset)
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        raise InvalidInputError("cursor de paginação inválido") from exc


def paginate(items: list[T], limit: int, cursor: str | None) -> Page[T]:
    offset = decode_cursor(cursor)
    end = offset + limit
    return Page(items=items[offset:end], total=len(items), next_cursor=encode_cursor(end) if end < len(items) else None)
