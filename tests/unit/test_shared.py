import pytest

from tse_api.shared.errors import InvalidInputError
from tse_api.shared.pagination import decode_cursor, encode_cursor, paginate
from tse_api.shared.uf import parse_uf


def test_paginate_walks_all_items_with_opaque_cursor():
    items = list(range(5))
    first = paginate(items, 2, None)
    second = paginate(items, 2, first.next_cursor)
    last = paginate(items, 2, second.next_cursor)
    assert (first.items, second.items, last.items) == ([0, 1], [2, 3], [4])
    assert last.next_cursor is None
    assert first.total == 5


@pytest.mark.parametrize("cursor", ["@@@", "bm9wZQ", encode_cursor(0).replace("b", "x")])
def test_invalid_cursor_is_rejected(cursor):
    with pytest.raises(InvalidInputError):
        decode_cursor(cursor)


def test_parse_uf():
    assert parse_uf(" SP ") == "sp"
    assert parse_uf("ZZ") == "zz"
    assert parse_uf("br", allow_national=True) == "br"
    with pytest.raises(InvalidInputError):
        parse_uf("br")
    with pytest.raises(InvalidInputError):
        parse_uf("xx")
