import httpx

from ....shared.errors import UpstreamUnavailableError
from ..domain.models import DatasetFile, DatasetKind
from ..domain.ports import DatasetCatalog

DATASET_IDS = {
    DatasetKind.BALLOTS_CSV: "resultados-{year}-boletim-de-urna",
    DatasetKind.URN_FILES: "resultados-{year}-arquivos-transmitidos-para-totalizacao",
}


class CkanDatasetCatalog(DatasetCatalog):
    """Lista os recursos dos datasets de resultados na API CKAN do Portal de Dados Abertos do TSE."""

    def __init__(self, http: httpx.Client, base_url: str):
        self._http = http
        self._base_url = base_url.rstrip("/")

    def list_files(self, year: int, kind: DatasetKind) -> list[DatasetFile]:
        try:
            response = self._http.get(
                f"{self._base_url}/api/3/action/package_show", params={"id": DATASET_IDS[kind].format(year=year)}
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise UpstreamUnavailableError(f"falha ao consultar o Portal de Dados Abertos: {exc}") from exc
        urls = [r["url"] for r in response.json()["result"]["resources"]]
        checksums = {u.removesuffix(".sha512") for u in urls if u.endswith(".sha512")}
        files = (DatasetFile.from_url(u, u + ".sha512" if u in checksums else None) for u in urls)
        return [f for f in files if f is not None and f.kind == kind]
