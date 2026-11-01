from .errors import InvalidInputError

# fmt: off
STATES = frozenset({
    "ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa",
    "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to",
})
# fmt: on
ABROAD = "zz"

# Código IBGE de cada UF (usado pelas malhas do IBGE) e regiões geográficas.
IBGE_STATE_CODES = {
    "ro": 11, "ac": 12, "am": 13, "rr": 14, "pa": 15, "ap": 16, "to": 17,
    "ma": 21, "pi": 22, "ce": 23, "rn": 24, "pb": 25, "pe": 26, "al": 27, "se": 28, "ba": 29,
    "mg": 31, "es": 32, "rj": 33, "sp": 35,
    "pr": 41, "sc": 42, "rs": 43,
    "ms": 50, "mt": 51, "go": 52, "df": 53,
}  # fmt: skip
REGIONS = {1: "norte", 2: "nordeste", 3: "sudeste", 4: "sul", 5: "centro-oeste"}


def region_of(uf: str) -> str | None:
    code = IBGE_STATE_CODES.get(uf)
    return REGIONS[code // 10] if code else None


NATIONAL = "br"


def parse_uf(value: str, allow_national: bool = False) -> str:
    """Normaliza a sigla da UF. ``zz`` = eleitores no exterior; ``br`` = abrangência nacional."""
    uf = value.strip().lower()
    if uf in STATES or uf == ABROAD or (allow_national and uf == NATIONAL):
        return uf
    raise InvalidInputError(f"UF inválida: {value}")
