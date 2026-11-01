import hashlib
import zipfile
from pathlib import Path

import httpx

from ....shared.errors import UpstreamDataError, UpstreamUnavailableError
from ..domain.models import DatasetFile
from ..domain.ports import DatasetDownloader

CHUNK = 1 << 20


class HttpDatasetDownloader(DatasetDownloader):
    def __init__(self, http: httpx.Client):
        self._http = http

    def download_archive(self, file: DatasetFile, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        zip_path = dest_dir / file.name
        try:
            if not zip_path.exists():
                self._stream_to(file.url, zip_path)
            if file.checksum_url:
                self._verify(zip_path, self._http.get(file.checksum_url).text)
        except httpx.HTTPError as exc:
            raise UpstreamUnavailableError(f"falha ao baixar {file.name}: {exc}") from exc
        return zip_path

    def _stream_to(self, url: str, path: Path) -> None:
        partial = path.with_suffix(".part")
        with self._http.stream("GET", url) as response, partial.open("wb") as out:
            response.raise_for_status()
            for chunk in response.iter_bytes(CHUNK):
                out.write(chunk)
        partial.replace(path)

    @staticmethod
    def _verify(path: Path, checksum_text: str) -> None:
        expected = checksum_text.split()[0].strip().lower()
        digest = hashlib.sha512()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(CHUNK), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            path.unlink()
            raise UpstreamDataError(f"hash SHA-512 não confere para {path.name}")

    @staticmethod
    def extract_csv(zip_path: Path) -> Path:
        with zipfile.ZipFile(zip_path) as archive:
            members = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(members) != 1:
                raise UpstreamDataError(f"esperado 1 CSV em {zip_path.name}, encontrado {members}")
            csv_path = zip_path.with_suffix(".csv")
            with archive.open(members[0]) as src, csv_path.open("wb") as dst:
                for chunk in iter(lambda: src.read(CHUNK), b""):
                    dst.write(chunk)
        return csv_path
