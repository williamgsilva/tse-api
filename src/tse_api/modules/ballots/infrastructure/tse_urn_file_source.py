from typing import Any

from ....shared.tse_http import TseFileNotFound, TseHttpClient
from ..domain.models import (
    SectionKey,
    SectionNotFound,
    SectionStatus,
    SectionSummary,
    UrnFile,
    UrnFileNotFound,
    UrnFileSet,
)
from ..domain.ports import UrnFileSource, VotingEventRef


def br_date_to_iso(date: str | None, time: str | None) -> str | None:
    if not date:
        return None
    day, month, year = date.split("/")
    return f"{year}-{month}-{day}T{time}" if time else f"{year}-{month}-{day}"


def sections_path(event: VotingEventRef, uf: str) -> str:
    return f"{event.cycle}/arquivo-urna/{event.code}/config/{uf}/{uf}-p{event.code:06d}-cs.json"


def section_dir(event: VotingEventRef, key: SectionKey) -> str:
    return (
        f"{event.cycle}/arquivo-urna/{event.code}/dados/{key.uf}/"
        f"{key.municipality:05d}/{key.zone:04d}/{key.section:04d}"
    )


def section_index_path(event: VotingEventRef, key: SectionKey) -> str:
    name = f"p{event.code:06d}-{key.uf}-m{key.municipality:05d}-z{key.zone:04d}-s{key.section:04d}-aux.json"
    return f"{section_dir(event, key)}/{name}"


class TseUrnFileSource(UrnFileSource):
    """Arquivos de urna publicados no portal de resultados do TSE (``arquivo-urna``)."""

    def __init__(self, client: TseHttpClient):
        self._client = client

    async def list_sections(self, event: VotingEventRef, uf: str) -> list[SectionSummary]:
        try:
            raw = await self._client.get_json(sections_path(event, uf))
        except TseFileNotFound as exc:
            raise SectionNotFound(f"lista de seções não publicada: {exc.path}") from exc
        return [
            SectionSummary(
                key=SectionKey(scope["cd"], int(m["cd"]), int(z["cd"]), int(s["ns"])),
                municipality_name=m.get("nm"),
                updated_at=br_date_to_iso(s.get("da"), s.get("ha")),
            )
            for scope in raw.get("abr", [])
            for m in scope.get("mu", [])
            for z in m.get("zon", [])
            for s in z.get("sec", [])
        ]

    async def fetch_section_status(self, event: VotingEventRef, key: SectionKey) -> SectionStatus:
        try:
            raw = await self._client.get_json(section_index_path(event, key))
        except TseFileNotFound as exc:
            raise SectionNotFound(f"seção sem arquivos de urna publicados: {exc.path}") from exc
        base = section_dir(event, key)
        return SectionStatus(
            voting_event_code=event.code,
            key=key,
            status=raw.get("st"),
            updated_at=br_date_to_iso(raw.get("dg"), raw.get("hg")),
            file_sets=tuple(self._file_set(base, h) for h in raw.get("hashes", [])),
        )

    def _file_set(self, base: str, raw: dict[str, Any]) -> UrnFileSet:
        return UrnFileSet(
            hash=raw["hash"],
            status=raw.get("st"),
            received_at=br_date_to_iso(raw.get("dr"), raw.get("hr")),
            files=tuple(
                UrnFile(name=a["nm"], kind=a["tp"], url=self._client.url_for(f"{base}/{raw['hash']}/{a['nm']}"))
                for a in raw.get("arq", [])
            ),
        )

    async def fetch_file(self, event: VotingEventRef, key: SectionKey, file_set: UrnFileSet, file: UrnFile) -> bytes:
        path = f"{section_dir(event, key)}/{file_set.hash}/{file.name}"
        try:
            return await self._client.get_bytes(path, persist=True)
        except TseFileNotFound as exc:
            raise UrnFileNotFound(f"arquivo não publicado pelo TSE: {exc.path}") from exc
