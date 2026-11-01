"""Lê o log da urna (``*-log.jez``: ZIP com ``logd.dat``, texto latin-1 separado por TAB).

Formato de cada linha: ``dd/mm/aaaa hh:mm:ss<TAB>nível<TAB>urna<TAB>aplicação<TAB>mensagem<TAB>hash``.
Para cada eleitor, no dia da eleição, a urna registra:

- ``Aguardando digitação do identificador do eleitor``: início do atendimento;
- ``Tipo de habilitação do eleitor [biométrica]``: habilitado pela digital;
- ``Solicitação de dado pessoal do eleitor para habilitação manual``: tem biometria, mas foi habilitado
  pelo ano de nascimento;
- nenhuma das duas: eleitor sem biometria cadastrada;
- ``O voto do eleitor foi computado``: fim do voto (é o horário usado).

As contagens por tipo batem com o detalhamento de comparecimento do BU.
"""

import io
import zipfile
from datetime import date, datetime

from ..domain.models import InvalidBallotReport
from ..domain.ports import UrnLogReader
from ..domain.timeline import BIOMETRICS, BIRTH_YEAR, NO_BIOMETRICS, VoteEvent

_NEXT_VOTER = b"Aguardando digita\xe7\xe3o do identificador do eleitor"
_BIOMETRIC = b"Tipo de habilita\xe7\xe3o do eleitor [biom"
_MANUAL = b"para habilita\xe7\xe3o manual"
_COMPUTED = b"O voto do eleitor foi computado"


class JezUrnLogReader(UrnLogReader):
    def read_votes(self, raw: bytes, voting_date: date) -> list[VoteEvent]:
        try:
            archive = zipfile.ZipFile(io.BytesIO(raw))
            members = [n for n in archive.namelist() if n.lower().endswith(".dat")]
            texts = [archive.read(n) for n in members]
        except (zipfile.BadZipFile, KeyError) as exc:
            raise InvalidBallotReport(f"log da urna inválido: {exc}") from exc
        prefix = voting_date.strftime("%d/%m/%Y").encode()
        events: list[VoteEvent] = []
        for text in texts:
            events.extend(_events(text, prefix))
        return events


def _events(text: bytes, day_prefix: bytes) -> list[VoteEvent]:
    events: list[VoteEvent] = []
    enablement = NO_BIOMETRICS
    for line in text.split(b"\n"):
        if not line.startswith(day_prefix):
            continue
        if _COMPUTED in line:
            at = datetime.strptime(line[:19].decode(), "%d/%m/%Y %H:%M:%S")
            events.append(VoteEvent(at, enablement))
            enablement = NO_BIOMETRICS
        elif _NEXT_VOTER in line:
            enablement = NO_BIOMETRICS
        elif _BIOMETRIC in line:
            enablement = BIOMETRICS
        elif _MANUAL in line:
            enablement = BIRTH_YEAR
    return events
