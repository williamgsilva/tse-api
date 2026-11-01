from dataclasses import replace

from .models import CandidateNames, OfficeVotes, VoteCount


def name_votes(office: OfficeVotes, names: CandidateNames) -> OfficeVotes:
    """Acrescenta nome do candidato e sigla do partido aos votos de um cargo."""
    return replace(office, name=office.name or names.office_name, votes=tuple(_name(v, names) for v in office.votes))


def _name(vote: VoteCount, names: CandidateNames) -> VoteCount:
    if vote.party_number is not None and vote.party_number in names.parties:
        vote = replace(vote, party_acronym=names.parties[vote.party_number])
    if vote.kind == "nominal" and vote.number is not None and vote.number in names.candidates:
        ballot_name, full_name = names.candidates[vote.number]
        vote = replace(vote, candidate_name=ballot_name, candidate_full_name=full_name)
    return vote
