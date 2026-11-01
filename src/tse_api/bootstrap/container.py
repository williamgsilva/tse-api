"""Composition root: instancia os adaptadores e liga os casos de uso de cada módulo."""

from dataclasses import dataclass

import httpx

from ..modules.ballots.application.download_urn_file import DownloadUrnFile
from ..modules.ballots.application.get_ballot_report import GetBallotReport
from ..modules.ballots.application.get_section_status import GetSectionStatus
from ..modules.ballots.application.get_vote_timeline import GetVoteTimeline
from ..modules.ballots.application.list_sections import ListSections
from ..modules.ballots.infrastructure.asn1_ballot_decoder import Asn1BallotDecoder
from ..modules.ballots.infrastructure.elections_directories import (
    ElectionsCandidateDirectory,
    ElectionsVotingEventDirectory,
)
from ..modules.ballots.infrastructure.jez_urn_log_reader import JezUrnLogReader
from ..modules.ballots.infrastructure.tse_urn_file_source import TseUrnFileSource
from ..modules.ballots.interfaces.http import BallotUseCases
from ..modules.elections.application.get_coverage import GetCoverage
from ..modules.elections.application.get_election import GetElection
from ..modules.elections.application.get_election_result import GetElectionResult
from ..modules.elections.application.get_subdivision_results import GetSubdivisionResults
from ..modules.elections.application.get_voting_event import GetVotingEvent
from ..modules.elections.application.list_municipalities import ListMunicipalities
from ..modules.elections.application.list_voting_events import ListVotingEvents
from ..modules.elections.infrastructure.tse_election_source import TseElectionSource
from ..modules.elections.interfaces.http import ElectionUseCases
from ..modules.geography.application.get_municipalities_mesh import GetMunicipalitiesMesh
from ..modules.geography.application.get_states_mesh import GetStatesMesh
from ..modules.geography.infrastructure.ibge_mesh_source import IbgeMeshSource
from ..modules.geography.interfaces.http import GeographyUseCases
from ..modules.open_data.application.aggregate_turnout import AggregateTurnout
from ..modules.open_data.application.aggregate_vote_timeline import AggregateVoteTimeline
from ..modules.open_data.application.aggregate_votes import AggregateVotes
from ..modules.open_data.application.estimate_late_votes import EstimateLateVotes
from ..modules.open_data.application.get_import_status import GetImportStatus
from ..modules.open_data.application.get_section_votes import GetSectionVotes
from ..modules.open_data.application.import_ballot_datasets import ImportBallotDatasets
from ..modules.open_data.application.list_available_datasets import ListAvailableDatasets
from ..modules.open_data.infrastructure.ckan_dataset_catalog import CkanDatasetCatalog
from ..modules.open_data.infrastructure.duckdb_vote_repository import DuckDbVoteRepository
from ..modules.open_data.infrastructure.http_dataset_downloader import HttpDatasetDownloader
from ..modules.open_data.infrastructure.zip_urn_package_reader import ZipUrnPackageReader
from ..modules.open_data.interfaces.http import OpenDataUseCases
from ..shared.config import Settings
from ..shared.tse_http import TseHttpClient


@dataclass(frozen=True)
class ApiContainer:
    tse_client: TseHttpClient
    mesh_source: IbgeMeshSource
    elections: ElectionUseCases
    geography: GeographyUseCases
    ballots: BallotUseCases
    open_data: OpenDataUseCases


def build_api_container(
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None = None,
    ibge_transport: httpx.AsyncBaseTransport | None = None,
) -> ApiContainer:
    client = TseHttpClient(settings, transport=transport)
    election_source = TseElectionSource(client)
    get_election_result = GetElectionResult(election_source)

    events = ElectionsVotingEventDirectory(GetVotingEvent(election_source))
    urn_files = TseUrnFileSource(client)
    download = DownloadUrnFile(events, urn_files)
    get_ballot_report = GetBallotReport(
        events, download, Asn1BallotDecoder(), ElectionsCandidateDirectory(get_election_result)
    )

    # A API só lê a base local; a escrita é exclusiva da importação (ADR 0004).
    repository = DuckDbVoteRepository(settings.database_path, read_only=True)

    meshes = IbgeMeshSource(settings.ibge_meshes_base_url, settings.cache_dir / "ibge", ibge_transport)

    return ApiContainer(
        tse_client=client,
        mesh_source=meshes,
        geography=GeographyUseCases(GetStatesMesh(meshes), GetMunicipalitiesMesh(meshes)),
        elections=ElectionUseCases(
            list_voting_events=ListVotingEvents(election_source),
            get_election=GetElection(election_source),
            list_municipalities=ListMunicipalities(election_source),
            get_election_result=get_election_result,
            get_coverage=GetCoverage(election_source),
            get_subdivision_results=GetSubdivisionResults(election_source),
        ),
        ballots=BallotUseCases(
            list_sections=ListSections(events, urn_files),
            get_section_status=GetSectionStatus(events, urn_files),
            get_ballot_report=get_ballot_report,
            download_urn_file=download,
            get_vote_timeline=GetVoteTimeline(get_ballot_report, download, JezUrnLogReader()),
        ),
        open_data=OpenDataUseCases(
            get_import_status=GetImportStatus(repository),
            get_section_votes=GetSectionVotes(repository),
            aggregate_votes=AggregateVotes(repository),
            aggregate_turnout=AggregateTurnout(repository),
            aggregate_vote_timeline=AggregateVoteTimeline(repository),
            estimate_late_votes=EstimateLateVotes(repository),
        ),
    )


@dataclass(frozen=True)
class IngestContainer:
    available: ListAvailableDatasets
    importer: ImportBallotDatasets


def build_ingest_container(settings: Settings, http: httpx.Client) -> IngestContainer:
    available = ListAvailableDatasets(CkanDatasetCatalog(http, settings.tse_open_data_base_url))
    importer = ImportBallotDatasets(
        available,
        HttpDatasetDownloader(http),
        ZipUrnPackageReader(),
        DuckDbVoteRepository(settings.database_path, read_only=False),
        settings.raw_dir,
    )
    return IngestContainer(available, importer)
