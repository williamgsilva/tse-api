"""Fluxos pela interface HTTP pública, com o portal do TSE simulado por arquivos reais."""

import dataclasses

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import BU_FILE, FIXTURES, load_sample_database
from tse_api.bootstrap.app import create_app
from tse_api.modules.open_data.infrastructure.duckdb_vote_repository import DuckDbVoteRepository


def test_health(api):
    assert api.get("/health/live").json() == {"status": "ok"}
    ready = api.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"] == {"base_local": "vazia", "portal_tse": "ok"}


def test_list_elections_of_2026(api):
    events = api.get("/v1/eleicoes", params={"ano": 2026}).json()
    assert [e["pleito"] for e in events][:2] == [3220, 3221]
    federal = events[0]["eleicoes"][0]
    assert (federal["codigo"], federal["turno"], federal["ano"]) == (6257, 1, 2026)
    assert federal["cargos"][0] == {"codigo": 1, "nome": "Presidente", "tipo": "majoritario", "abrangencias": ["br"]}


def test_municipalities_and_result(api):
    municipalities = api.get("/v1/eleicoes/6257/municipios", params={"uf": "sp"}).json()
    assert municipalities == [
        {"uf": "sp", "codigo": 71072, "codigo_ibge": 3550308, "nome": "SÃO PAULO", "capital": True, "zonas": [1, 2]}
    ]
    result = api.get("/v1/eleicoes/6257/resultados/ac/1", params={"municipio": 1066}).json()
    assert result["tipo_abrangencia"] == "mu" and result["totalizacao_finalizada"] is True
    leader = result["cargos"][0]["candidatos"][0]
    assert {"numero", "nome_urna", "partido", "votos", "eleito"} <= leader.keys()


def test_ballot_report_with_candidate_names(api):
    body = api.get("/v1/pleitos/3220/secoes/AC/1066/4/77/boletim").json()
    assert (body["arquivo"], body["comparecimento"], body["fase"]) == (BU_FILE, 234, "oficial")
    federal = body["eleicoes"][0]
    assert federal["nome"].startswith("Eleição Ordinária Federal")
    president = federal["cargos"][0]
    assert president["totais"] == {"nominal": 217, "legenda": 0, "branco": 4, "nulo": 13}
    lula = next(v for v in president["votos"] if v["numero"] == 13)
    assert (lula["nome"], lula["sigla_partido"], lula["quantidade"]) == ("LULA", "PT", 99)


def test_sections_and_files(api):
    page = api.get("/v1/pleitos/3220/secoes/ac", params={"municipio": 1066, "limit": 1}).json()
    assert page["total"] == 2 and page["secoes"][0]["secao"] == 77
    second = api.get(
        "/v1/pleitos/3220/secoes/ac", params={"municipio": 1066, "limit": 1, "cursor": page["proximo_cursor"]}
    ).json()
    assert second["secoes"][0]["secao"] == 78 and second["proximo_cursor"] is None

    status = api.get("/v1/pleitos/3220/secoes/ac/1066/4/77").json()
    assert status["transmissoes"][0]["vigente"] is True
    assert {a["tipo"] for a in status["transmissoes"][0]["arquivos"]} == {"bu", "vota", "rdv", "log"}

    raw = api.get("/v1/pleitos/3220/secoes/ac/1066/4/77/arquivos/bu")
    assert raw.content == (FIXTURES / BU_FILE).read_bytes()
    assert BU_FILE in raw.headers["content-disposition"]


def test_errors_are_problem_details(api):
    missing = api.get("/v1/pleitos/3220/secoes/ac/1066/4/78/boletim", headers={"X-Request-ID": "abc"})
    assert missing.status_code == 404
    assert missing.headers["content-type"] == "application/problem+json"
    assert missing.json() | {"detail": None} == {
        "type": "/problems/section-not-found",
        "title": "Seção sem arquivos de urna publicados",
        "status": 404,
        "detail": None,
        "instance": "/v1/pleitos/3220/secoes/ac/1066/4/78/boletim",
        "traceId": "abc",
    }
    assert api.get("/v1/pleitos/3220/secoes/xx/1066/4/77").json()["type"] == "/problems/invalid-input"
    assert api.get("/v1/eleicoes/1").json()["type"] == "/problems/election-not-found"
    assert api.get("/v1/pleitos/3220/secoes/ac/1066/4/77/arquivos/xyz").status_code == 404
    invalid = api.get("/v1/eleicoes/abc")
    assert invalid.status_code == 422 and invalid.json()["errors"][0]["campo"] == "path.eleicao"
    assert api.get("/v1/dados-abertos/2026/1/votacao/1").json()["status"] == 503


def test_open_data_endpoints(settings, tse_transport):
    DuckDbVoteRepository(settings.database_path, read_only=False).load(FIXTURES / "bweb_amostra.csv", 2026, 1, "AC")
    with TestClient(create_app(settings, tse_transport)) as api:
        assert api.get("/v1/dados-abertos/importacoes").json()[0]["linhas"] == 199
        section = api.get("/v1/dados-abertos/2026/1/secoes/ac/1074/4/175").json()
        assert section["nome_municipio"] == "CRUZEIRO DO SUL"
        rows = api.get("/v1/dados-abertos/2026/1/votacao/7", params={"agrupar": "municipio", "limit": 3}).json()
        assert len(rows) == 3 and {"uf", "municipio", "nome_municipio", "nome", "votos"} <= rows[0].keys()
        assert "zona" not in rows[0]
        assert api.get("/v1/dados-abertos/2026/1/secoes/ac/1074/4/9999").status_code == 404


def test_serves_frontend_with_spa_fallback(settings, tse_transport, tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path / "segredo.txt").write_text("nao")
    with TestClient(create_app(dataclasses.replace(settings, frontend_dist=dist), tse_transport)) as api:
        assert api.get("/").text == "<html>app</html>"
        assert api.get("/assets/app.js").text == "console.log(1)"
        assert api.get("/secoes/ac/1066").text == "<html>app</html>"
        assert "nao" not in api.get("/../segredo.txt").text
        assert api.get("/v1/rota-inexistente").status_code == 404
        assert api.get("/v1/eleicoes").status_code == 200


def test_section_vote_timeline_live(api):
    body = api.get("/v1/pleitos/3220/secoes/ac/1066/4/77/horarios", params={"apos": "17:00"}).json()
    assert (body["votos_apos"], body["comparecimento"], body["fonte_fuso"]) == (22, 234, "uf")
    timeline = body["horarios"]
    assert timeline["horas_para_brasilia"] == 2
    assert timeline["primeiro_voto"] == "2026-10-04T08:09:09"
    assert timeline["por_habilitacao"] == {"biometria": 212, "ano_nascimento": 13, "sem_biometria": 9}
    assert sum(i["votos"] for i in timeline["intervalos"]) == 234
    president = next(c for c in body["estimativa_por_cargo"] if c["codigo"] == 1)
    assert president["votos_tardios"] == 22
    assert sum(e["votos_tardios_estimados"] for e in president["estimativas"]) == pytest.approx(22, abs=0.1)
    assert api.get("/v1/pleitos/3220/secoes/ac/1066/4/77/horarios", params={"apos": "5pm"}).status_code == 422


def test_turnout_timeline_and_late_votes_endpoints(settings, tse_transport):
    load_sample_database(settings)
    with TestClient(create_app(settings, tse_transport)) as api:
        base = "/v1/dados-abertos/2026/1"
        [total] = api.get(f"{base}/comparecimento", params={"uf": "ac"}).json()
        assert total["secoes"] == 181 and total["secoes_com_arquivos_urna"] == 1
        assert {
            "aptos",
            "comparecimento",
            "habilitados_biometria",
            "sem_biometria",
            "ultimo_encerramento",
        } <= total.keys()
        by_place = api.get(f"{base}/comparecimento", params={"agrupar": "local", "municipio": 1074}).json()
        assert all({"zona", "local"} <= set(r["grupo"]) for r in by_place)

        points = api.get(f"{base}/horarios", params={"intervalo": 60}).json()
        assert [(p["inicio"], p["votos"]) for p in points] == [("08:00", 100), ("17:00", 91)]

        late = api.get(f"{base}/votos-apos/7", params={"apos": "17:00", "agrupar": "uf"}).json()
        assert late["resumo"]["votos_apos"] == 91
        assert late["metodo"].startswith("ESTIMATIVA")
        assert late["votaveis"][0]["grupo"] == {"uf": "AC"}

        by_local = api.get(f"{base}/votacao/7", params={"agrupar": "local", "tipo_urna": "apurada", "limit": 2}).json()
        assert by_local and "local" in by_local[0]

        assert api.get(f"{base}/horarios", params={"intervalo": 20}).status_code == 422
        assert api.get(f"{base}/votos-apos/7", params={"apos": "17:05"}).status_code == 422
        kinds = {d["tipo"] for d in api.get("/v1/dados-abertos/importacoes").json()}
        assert kinds == {"boletins", "urnas"}


def test_new_endpoints_without_urn_files(settings, tse_transport):
    DuckDbVoteRepository(settings.database_path, read_only=False).load(FIXTURES / "bweb_amostra.csv", 2026, 1, "AC")
    with TestClient(create_app(settings, tse_transport)) as api:
        assert api.get("/v1/dados-abertos/2026/1/comparecimento").json()[0]["sem_biometria"] is None
        missing = api.get("/v1/dados-abertos/2026/1/horarios")
        assert missing.status_code == 503 and "pacote" in missing.json()["detail"]


def test_maps_and_subdivisions(settings, tse_transport):
    feature = {
        "type": "Feature",
        "properties": {"codarea": "12"},
        "geometry": {"type": "Point", "coordinates": [-70, -9]},
    }
    ibge = httpx.MockTransport(lambda r: httpx.Response(200, json={"type": "FeatureCollection", "features": [feature]}))
    with TestClient(create_app(settings, tse_transport, ibge)) as api:
        brazil = api.get("/v1/mapas/brasil")
        assert brazil.headers["content-type"] == "application/geo+json"
        assert "max-age" in brazil.headers["cache-control"]
        assert brazil.json()["features"][0]["properties"] == {"codigo_ibge": 12, "uf": "ac", "regiao": "norte"}
        assert api.get("/v1/mapas/ac").status_code == 200
        assert api.get("/v1/mapas/zz").status_code == 422

        [porto_walter] = api.get("/v1/eleicoes/6257/resultados/ac/1/subdivisoes", params={"limite": 2}).json()
        assert (porto_walter["codigo"], porto_walter["codigo_ibge"], porto_walter["nome"]) == (
            "1066",
            1200393,
            "PORTO WALTER",
        )
        assert len(porto_walter["candidatos"]) == 2
        assert porto_walter["candidatos"][0]["votos"] >= porto_walter["candidatos"][1]["votos"]
        assert api.get("/v1/eleicoes/6257/resultados/br/1/subdivisoes").json() == []
        assert api.get("/v1/eleicoes/6257/resultados/ac/1/subdivisoes", params={"limite": 50}).status_code == 422
