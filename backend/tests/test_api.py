"""Smoke tests for the Fire Sight API, run against the committed data files."""

GOVAN = "S13002971"
NORTH_EAST = "S13003133"  # last ward in the model output; easy to miss in filters


def test_health_reports_loaded_datasets(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["wards_loaded"] == 23
    assert body["premises_loaded"] == 14
    assert body["zones_loaded"] == 746


def test_status_reports_model_and_forecasts(client):
    body = client.get("/api/status").json()
    assert body["model_loaded"] is True
    assert body["ward_forecasts_count"] == 23
    assert body["model_components_active"] == 5


def test_modes_lists_strategic_and_premises(client):
    modes = client.get("/api/modes").json()["modes"]
    assert [m["id"] for m in modes] == ["strategic", "premises"]


def test_wards_summary_list(client):
    wards = client.get("/api/strategic/wards").json()
    assert len(wards) == 23
    assert {"ward_id", "risk_score", "risk_band", "drivers", "prediction"} <= wards[0].keys()


def test_wards_geojson_mock_and_model_sources(client):
    for source in ("mock", "model"):
        data = client.get("/api/strategic/wards.geojson", params={"source": source}).json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 23
        props = data["features"][0]["properties"]
        assert props["data_source"] == source
        assert props["risk_band"] in {"low", "medium", "high"}
        assert data["features"][0]["geometry"]["type"] in {"Polygon", "MultiPolygon"}


def test_model_source_has_forecast_for_every_ward(client):
    data = client.get("/api/strategic/wards.geojson", params={"source": "model"}).json()
    for feature in data["features"]:
        prediction = feature["properties"]["prediction"]
        assert prediction["forecast_6mo"] is not None, feature["properties"]["ward_name"]
        assert prediction["forecast_lower"] <= prediction["forecast_6mo"] <= prediction["forecast_upper"]


def test_single_ward_and_404(client):
    ok = client.get(f"/api/strategic/wards/{NORTH_EAST}", params={"source": "model"})
    assert ok.status_code == 200
    assert ok.json()["properties"]["ward_name"] == "North East"
    assert client.get("/api/strategic/wards/NOPE").status_code == 404


def test_zones_top_is_sorted_by_rank(client):
    zones = client.get("/api/zones/top", params={"n": 5}).json()
    assert len(zones) == 5
    ranks = [z["riskrank"] for z in zones]
    assert ranks == sorted(ranks)
    assert ranks[0] == 1


def test_zones_list_and_single_zone(client):
    zones = client.get("/api/zones").json()
    assert len(zones) == 746
    zone_id = zones[0]["zoneid"]
    assert client.get(f"/api/zones/{zone_id}").json()["zoneid"] == zone_id
    assert client.get("/api/zones/NOPE").status_code == 404


def test_premises_list_filters_and_detail(client):
    all_items = client.get("/api/premises").json()
    assert len(all_items) == 14
    high = client.get("/api/premises", params={"risk_band": "high"}).json()
    assert high and all(item["risk_band"] == "high" for item in high)
    assert client.get("/api/premises/P001").json()["id"] == "P001"
    assert client.get("/api/premises/NOPE").status_code == 404


def test_explain_falls_back_without_openai_key(client):
    cases = [
        {"mode": "ward", "id": GOVAN, "source": "mock"},
        {"mode": "ward", "id": GOVAN, "source": "model"},
        {"mode": "premises", "id": "P001"},
        {"mode": "zone", "id": client.get("/api/zones/top", params={"n": 1}).json()[0]["zoneid"]},
    ]
    for params in cases:
        response = client.get("/api/explain", params=params)
        assert response.status_code == 200, params
        body = response.json()
        assert body["source"] == "fallback"
        assert body["text"].count("•") == 3


def test_explain_rejects_bad_input(client):
    assert client.get("/api/explain", params={"mode": "bogus", "id": "x"}).status_code == 400
    assert client.get("/api/explain", params={"mode": "ward", "id": "NOPE"}).status_code == 404


def test_cors_allows_local_frontend_only(client):
    headers = {"Access-Control-Request-Method": "GET"}
    allowed = client.options("/api/health", headers={**headers, "Origin": "http://localhost:5173"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    blocked = client.options("/api/health", headers={**headers, "Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in blocked.headers


def test_model_forecast_reports_years_from_data(client):
    props = client.get(f"/api/strategic/wards/{NORTH_EAST}", params={"source": "model"}).json()["properties"]
    prediction = props["prediction"]
    assert prediction["years_of_data"] == 14
    assert (prediction["first_year"], prediction["last_year"]) == (2009, 2023)
    assert "14 years" in prediction["note"] and "2009–2023" in prediction["note"]


def test_model_explain_text_uses_data_years(client):
    text = client.get("/api/explain", params={"mode": "ward", "id": GOVAN, "source": "model"}).json()["text"]
    assert "14 years of SFRS dwelling fire data (2009–2023)" in text


def test_cors_warning_when_unset_in_production(monkeypatch, caplog):
    import main

    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv("RENDER", "true")
    with caplog.at_level("WARNING", logger="uvicorn.error"):
        origins = main.resolve_cors_origins()
    assert origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert "CORS_ORIGINS is not set" in caplog.text

    caplog.clear()
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example")
    assert main.resolve_cors_origins() == ["https://app.example"]
    assert "CORS_ORIGINS is not set" not in caplog.text
