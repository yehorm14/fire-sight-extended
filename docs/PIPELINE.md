# Data pipeline

`data-pipeline/run_model.py` scores each Glasgow DataZone from five SIMD 2020 indicators (area deprivation decile, overcrowding, comparative illness factor, no central heating, crime rate) with fixed weights. It also fits a recency-weighted linear trend to yearly SFRS dwelling-fire counts for the 23 wards in `backend/data/glasgow_wards.geojson` and writes 6, 12 and 18 month forecasts with a 95% range. `notebook.ipynb` is the exploratory version.

The processed output is committed in `data-pipeline/output/`, so the API runs without the raw data. The raw inputs are not in git (the fire statistics file is about 12 MB).

## Regenerate the output

```bash
python data-pipeline/download_datasets.py
python data-pipeline/run_model.py
```

The downloader fetches the SIMD 2020v2 indicator workbook and the SFRS fire statistics, and exits non-zero if either fails. `data-pipeline/raw/simd2020.csv` (SIMD ranks and deciles per DataZone) is a manual step: save it from the Scottish Government SIMD 2020 page, as the script prints. `--boundaries` also downloads data zone boundaries (needs geopandas).

## Limitations

- The "Mock" source, the premises overlay and the event markers are illustrative sample data.
- Forecasts are a linear trend on yearly counts per ward, with no weather, seasonality or planned development. The "6 months" label is the next yearly step of that trend.
- Risk weights are chosen by hand and not validated against incident outcomes.
- In "Model" mode a ward's score is the average DataZone score for its SIMD decile.
- Census 2022 and EPC data were planned but are not used.
