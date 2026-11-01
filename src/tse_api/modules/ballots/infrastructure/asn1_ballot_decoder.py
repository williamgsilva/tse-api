"""Decodifica o ``*-bu.dat`` (ASN.1/BER) com a especificação publicada pelo TSE (``spec/bu.asn1``).

O arquivo é um ``EntidadeEnvelopeGenerico`` cujo campo ``conteudo`` contém a ``EntidadeBoletimUrna``.
"""

from functools import cache
from pathlib import Path
from typing import Any

import asn1tools

from ..domain.models import BallotReport, ElectionVotes, InvalidBallotReport, OfficeVotes, UrnInfo, VoteCount
from ..domain.ports import BallotDecoder

SPEC_PATH = Path(__file__).parent / "spec" / "bu.asn1"

CONSTITUTIONAL_OFFICES = {
    "presidente": 1,
    "vicePresidente": 2,
    "governador": 3,
    "viceGovernador": 4,
    "senador": 5,
    "deputadoFederal": 6,
    "deputadoEstadual": 7,
    "deputadoDistrital": 8,
    "primeiroSuplenteSenador": 9,
    "segundoSuplenteSenador": 10,
    "prefeito": 11,
    "vicePrefeito": 12,
    "vereador": 13,
}


@cache
def _spec() -> Any:
    return asn1tools.compile_files(str(SPEC_PATH), codec="ber")


def _iso(value: str | None) -> str | None:
    """``YYYYMMDDThhmmss`` (formato da Justiça Eleitoral) → ISO 8601."""
    if not value or len(value) != 15:
        return value
    return f"{value[0:4]}-{value[4:6]}-{value[6:8]}T{value[9:11]}:{value[11:13]}:{value[13:15]}"


def _identification(choice: tuple[str, dict[str, Any]]) -> dict[str, object]:
    kind, data = choice
    mz = data["municipioZona"]
    out: dict[str, object] = {
        "tipo": "secao" if kind == "identificacaoSecaoEleitoral" else "contingencia",
        "municipio": mz["municipio"],
        "zona": mz["zona"],
    }
    if "secao" in data:
        out.update(local=data["local"], secao=data["secao"])
    return out


def _office(code: tuple[str, Any]) -> tuple[int, str]:
    kind, value = code
    if kind == "cargoConstitucional":
        return CONSTITUTIONAL_OFFICES[value], value
    return int(value), f"consulta{value}"


def _urn(urn: dict[str, Any]) -> UrnInfo:
    load = urn["correspondenciaResultado"]["carga"]
    counting_system = None
    if "motivoUtilizacaoSA" in urn:
        _, reason = urn["motivoUtilizacaoSA"]
        counting_system = {
            "tipo": reason.get("tipoApuracao") or reason.get("tipoapuracao"),
            "motivo": reason["motivoApuracao"],
        }
    return UrnInfo(
        kind=urn["tipoUrna"],
        file_kind=urn["tipoArquivo"],
        voting_software_version=urn["versaoVotacao"],
        internal_number=load["numeroInternoUrna"],
        load_flash_serial=load["numeroSerieFC"].hex().upper(),
        voting_flash_serial=urn["numeroSerieFV"].hex().upper(),
        load_code=load["codigoCarga"],
        loaded_at=_iso(load["dataHoraCarga"]),
        load_target=_identification(urn["correspondenciaResultado"]["identificacao"]),
        counting_system=counting_system,
    )


def _office_votes(kind: str, turnout: int, total: dict[str, Any]) -> OfficeVotes:
    code, identifier = _office(total["codigoCargo"])
    votes = tuple(
        VoteCount(
            kind=v["tipoVoto"],
            quantity=v["quantidadeVotos"],
            number=v["identificacaoVotavel"]["codigo"] if "identificacaoVotavel" in v else None,
            party_number=v["identificacaoVotavel"]["partido"] if "identificacaoVotavel" in v else None,
        )
        for v in total["votosVotaveis"]
    )
    return OfficeVotes(
        code=code, identifier=identifier, kind=kind, print_order=total["ordemImpressao"], turnout=turnout, votes=votes
    )


def _election_votes(result: dict[str, Any]) -> ElectionVotes:
    return ElectionVotes(
        election_code=result["idEleicao"],
        eligible_voters=result["qtdEleitoresAptos"],
        eligible_in_section=result["qtdEleitoresAptosSecao"],
        eligible_in_transit=result["qtdEleitoresAptosTTE"],
        offices=tuple(
            _office_votes(rv["tipoCargo"], rv["qtdComparecimento"], total)
            for rv in result["resultadosVotacao"]
            for total in rv["totaisVotosCargo"]
        ),
        last_votes_hash=result["ultimoHashVotosVotavel"].hex().upper(),
    )


class Asn1BallotDecoder(BallotDecoder):
    def decode(self, raw: bytes) -> BallotReport:
        bu = self._decode_content(raw)
        id_kind, id_value = bu["cabecalho"]["idEleitoral"]
        section = bu["identificacaoSecao"]
        data_kind, data = bu["dadosSecaoSA"]
        breakdown = bu.get("detalhamentoComparecimento")
        return BallotReport(
            phase=bu["fase"],
            electoral_id={"tipo": id_kind, "codigo": id_value},
            generated_at=_iso(bu["cabecalho"]["dataGeracao"]),
            issued_at=_iso(bu["dataHoraEmissao"]),
            section={
                "municipio": section["municipioZona"]["municipio"],
                "zona": section["municipioZona"]["zona"],
                "local": section["local"],
                "secao": section["secao"],
            },
            urn=_urn(bu["urna"]),
            turnout=bu["qtdEleitoresCompareceram"],
            voting_window={
                "abertura": _iso(data["dataHoraAbertura"]),
                "encerramento": _iso(data["dataHoraEncerramento"]),
            }
            if data_kind == "dadosSecao"
            else None,
            counting_board={
                "junta": data["juntaApuradora"],
                "turma": data["turmaApuradora"],
                "urna_origem": data.get("numeroInternoUrnaOrigem"),
            }
            if data_kind == "dadosSA"
            else None,
            turnout_breakdown={
                "sem_biometria": breakdown["qtdEleitoresCompareceramSemBiometria"],
                "habilitados_biometria": breakdown["qtdEleitoresHabilitadosPorBiometria"],
                "habilitados_ano_nascimento": breakdown["qtdEleitoresHabilitadosPorBiografia"],
            }
            if breakdown
            else None,
            elections=tuple(_election_votes(r) for r in bu["resultadosVotacaoPorEleicao"]),
            load_code_history=tuple(bu["historicoCodigosCarga"]),
        )

    @staticmethod
    def _decode_content(raw: bytes) -> dict[str, Any]:
        try:
            envelope = _spec().decode("EntidadeEnvelopeGenerico", raw)
        except Exception as exc:  # asn1tools levanta vários tipos de erro de decodificação
            raise InvalidBallotReport(f"envelope ASN.1 inválido: {exc}") from exc
        if envelope.get("tipoEnvelope") != "envelopeBoletimUrna":
            raise InvalidBallotReport(f"tipo de envelope inesperado: {envelope.get('tipoEnvelope')}")
        if "seguranca" in envelope:
            raise InvalidBallotReport("conteúdo do envelope está cifrado")
        try:
            content: dict[str, Any] = _spec().decode("EntidadeBoletimUrna", envelope["conteudo"])
        except Exception as exc:
            raise InvalidBallotReport(f"boletim ASN.1 inválido: {exc}") from exc
        return content
