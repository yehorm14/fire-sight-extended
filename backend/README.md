# FireSight Backend

This backend provides the demo API for FireSight. It intentionally focuses on
our backend-owned app flow only:

```text
1. Strategic ward-level overview across Glasgow
2. City Centre high-risk premises overlay
3. Human-readable explanations for selected wards or premises
```

The ward map and premises overlay are served from files in `backend/data/`.
The "model" data source and the DataZone endpoints load precomputed output from
`data-pipeline/output/` (`glasgowzones.csv` and `glasgow_ward_forecasts.csv`,
written by `data-pipeline/run_model.py`) when `main.py` starts. The API does
not run the pipeline. If those CSVs are missing, the model endpoints return
empty results or 503.

## Data Files

Strategic ward map:

```text
backend/data/glasgow_wards.geojson
```

This contains 23 official Glasgow ward polygons. The frontend uses the
`geometry` field to draw ward shapes and the `properties` field for scores,
drivers, and forecast-style fields.

City Centre premises overlay:

```text
backend/data/city_centre_premises.json
```

This contains 14 illustrative, synthetic premises markers focused on Glasgow City
Centre. They are not real buildings or real inspection data. Areas covered:

```text
Anderston/City/Yorkhill
Calton
Merchant City
George Square
Cowcaddens
Garnethill
Saltmarket
```

The premises layer demonstrates how the app could expand from area-level
planning into building-level prevention and inspection prioritisation.

## Running Locally

From the repository root, with dependencies installed (`pip install -r backend/requirements.txt`):

```bash
python -m uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

Interactive FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

## Frontend Contract

React should use these endpoints:

```text
GET http://localhost:8000/api/strategic/wards.geojson
GET http://localhost:8000/api/premises?focus=city-centre
GET http://localhost:8000/api/explain?mode=premises&id=P001
```

Suggested UI:

```text
Base layer: 23 ward polygons
Toggle: Show High-Risk Premises
Overlay: City Centre premises markers
Popup: score, premises type, inspection priority, drivers, recommended intervention
AI button: Explain this risk
```

## Endpoints

### `GET /api/health`

Returns backend status and loaded dataset counts.

Example:

```json
{
  "status": "ok",
  "wards_loaded": 23,
  "premises_loaded": 14,
  "zones_loaded": 746,
  "prediction_model": "linear_trend_forecast"
}
```

### `GET /api/modes`

Returns the two frontend modes:

```text
strategic = ward-level planning map
premises = City Centre high-risk premises overlay
```

### `GET /api/strategic/wards`

Returns a compact list of 23 wards with:

```text
id
name
ward_id
ward_name
risk_score
risk_band
drivers
prediction
```

### `GET /api/strategic/wards.geojson`

Returns the full ward GeoJSON for the map.

Each ward feature includes:

```text
geometry
properties.ward_id
properties.ward_name
properties.risk_score
properties.risk_band
properties.drivers
properties.prediction
```

### `GET /api/strategic/wards/{ward_id}`

Returns one full ward GeoJSON feature.

Example:

```text
GET /api/strategic/wards/S13002976
```

### `GET /api/premises`

Returns City Centre premises markers.

Useful filters:

```text
GET /api/premises?focus=city-centre
GET /api/premises?ward_id=S13002976
GET /api/premises?risk_band=high
```

Each premises record includes:

```text
id
name
lat
lng
ward_id
ward_name
premises_type
primary_risk_type
risk_score
risk_band
inspection_priority
drivers
future_pressure
recommended_intervention
```

### `GET /api/premises/{premises_id}`

Returns one premises marker.

Example:

```text
GET /api/premises/P001
```

### `GET /api/explain`

Returns a human-readable explanation for a ward or premises.

Ward example:

```text
GET /api/explain?mode=ward&id=S13002976
```

Premises example:

```text
GET /api/explain?mode=premises&id=P001
```

Response shape:

```json
{
  "id": "P001",
  "mode": "premises",
  "source": "fallback",
  "text": "This premises is flagged as Priority 1 because it combines evacuation complexity, dense residential occupancy, and limited appliance access. City-centre demand and planned development pressure may affect prevention demand over the 6 months. This should be treated as a prevention-review and inspection-prioritisation signal, not an official safety judgement."
}
```

If `OPENAI_API_KEY` is available in `backend/.env`, the endpoint attempts to
use OpenAI. If the key is missing or the request fails, the backend returns a
safe fallback explanation.

Important wording rule:

```text
Never say a building is unsafe.
Say it is flagged for prevention review or inspection prioritisation.
```

## Other Endpoints

```text
GET /api/status               model and forecast load status
GET /api/modes                the two map modes
GET /api/zones?top=N          746 Glasgow DataZones with risk scores (from the pipeline)
GET /api/zones/top?n=20       highest-risk DataZones
GET /api/zones/{zoneid}       one DataZone
```

`source=model` on the ward endpoints switches from the prototype scores in
`glasgow_wards.geojson` to pipeline-based scores and SFRS dwelling-fire forecasts.

## Configuration

Copy `.env.example` to `.env`:

```text
OPENAI_API_KEY   optional; without it /api/explain returns template text
OPENAI_MODEL     default gpt-4o-mini
CORS_ORIGINS     comma-separated allowed origins, default http://localhost:5173
```

## Tests

From the repository root: `python -m pytest -q`.

## Fire-Service Language Used

The backend data uses terms such as:

```text
prevention priority
premises risk profile
Home Fire Safety Visit
inspection priority
operational intelligence
mobilisation demand
evacuation complexity
high-risk premises
dwelling fire risk
false alarm demand
community safety intervention
```

These terms help the demo sound closer to a fire and rescue planning workflow
without claiming official operational certainty.
