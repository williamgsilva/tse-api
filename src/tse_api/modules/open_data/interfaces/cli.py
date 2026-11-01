"""Importa dados do Portal de Dados Abertos do TSE para a base local.

Fontes (--fonte):
    boletins  CSV de boletins de urna: votos por candidato em cada seção (padrão)
    urnas     pacote com BU e log de cada urna: biometria detalhada e votos por horário
              (grande: ~400 MB no Acre, ~20 GB em São Paulo por turno)
    ambos     as duas

Exemplos:
    tse-ingest --listar --fonte ambos
    tse-ingest --turno 1 --uf AC SP
    tse-ingest --turno 1 2 --uf AC --fonte ambos
"""

import argparse
import sys

from ..application.import_ballot_datasets import ImportBallotDatasets, ImportReport
from ..application.list_available_datasets import ListAvailableDatasets
from ..domain.models import DatasetKind

SOURCES = {
    "boletins": (DatasetKind.BALLOTS_CSV,),
    "urnas": (DatasetKind.URN_FILES,),
    "ambos": (DatasetKind.BALLOTS_CSV, DatasetKind.URN_FILES),
}


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tse-ingest", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ano", type=int, default=2026)
    parser.add_argument("--turno", type=int, nargs="+", default=[1, 2], choices=[1, 2])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--uf", nargs="+", type=str.upper, help="siglas das UFs (ZZ = exterior)")
    target.add_argument("--todas", action="store_true", help="todas as UFs publicadas")
    target.add_argument("--listar", action="store_true", help="só lista os arquivos disponíveis")
    parser.add_argument("--fonte", choices=sorted(SOURCES), default="boletins", help="o que importar")
    parser.add_argument("--manter-arquivos", action="store_true", help="não apaga os ZIP/CSV baixados")
    return parser.parse_args(argv)


def run(argv: list[str] | None, available: ListAvailableDatasets, importer: ImportBallotDatasets) -> int:
    args = parse_args(argv)
    if args.listar:
        for kind in SOURCES[args.fonte]:
            for f in available.execute(args.ano, args.turno, kind):
                print(f"{kind.value:8}  {f.round}º turno  {f.uf}  {f.url}")
        return 0

    def progress(report: ImportReport) -> None:
        file = report.file
        unit = "linhas" if file.kind == DatasetKind.BALLOTS_CSV else "seções"
        print(f"[{file.kind.value} {file.round}º turno {file.uf}] {report.rows:,} {unit} em {report.seconds:.0f}s")

    def sections(done: int, total: int) -> None:
        print(f"  decodificando urnas: {done:,}/{total:,}", end="\r" if done < total else "\n", flush=True)

    reports = importer.execute(
        args.ano,
        args.turno,
        None if args.todas else args.uf,
        SOURCES[args.fonte],
        args.manter_arquivos,
        progress,
        sections,
        lambda message: print(f"aviso: {message}", file=sys.stderr),
    )
    return 0 if reports else 1
