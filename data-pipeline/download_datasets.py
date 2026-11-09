"""
Fire Sight - dataset downloader.

Fetches the raw inputs that run_model.py needs into data-pipeline/raw/
(gitignored). Run from anywhere:

    python data-pipeline/download_datasets.py

Files written:
    raw/simd2020_indicators.xlsx      SIMD 2020v2 indicator data (Scottish Government)
    raw/fire_statistics_scotland.csv  Fires by type of incident, per ward (statistics.gov.scot)

Manual step: raw/simd2020.csv (SIMD 2020v2 ranks and deciles per data zone).
See the message printed at the end.

Optional: pass --boundaries to also download the 2011 data zone boundaries as
GeoJSON (needs geopandas). run_model.py does not use them.
"""

import argparse
import io
import shutil
import sys
import zipfile
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parent / "raw"
HEADERS = {"User-Agent": "Mozilla/5.0 (Fire Sight data pipeline)"}

SIMD_INDICATORS_URL = (
    "https://www.gov.scot/binaries/content/documents/govscot/publications/"
    "statistics/2020/01/scottish-index-of-multiple-deprivation-2020-indicator-data/"
    "documents/simd_2020_indicators/simd_2020_indicators/"
    "govscot%3Adocument/SIMD%2B2020v2%2B-%2Bindicators.xlsx"
)
FIRE_STATS_URL = (
    "https://statistics.gov.scot/downloads/cube-table"
    "?uri=http%3A%2F%2Fstatistics.gov.scot%2Fdata%2Ffire---type-of-incident"
)
DATAZONE_BOUNDARIES_URL = "https://maps.gov.scot/ATOM/shapefiles/SG_DataZoneBdry_2011.zip"
SIMD_PAGE = "https://www.gov.scot/collections/scottish-index-of-multiple-deprivation-2020/"


def download(url: str, dest: Path, label: str) -> bool:
    if dest.exists():
        print(f"  [skip] {label} already exists ({dest.name})")
        return True
    print(f"  Downloading {label} ...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  Saved {len(r.content) / 1024:.0f} KB -> {dest}")
        return True
    except requests.RequestException as e:
        print(f"  FAILED: {e}")
        return False


def download_boundaries() -> None:
    """Optional: Scotland 2011 data zone polygons as GeoJSON (needs geopandas)."""
    dest = RAW / "scotland_datazones.geojson"
    if dest.exists():
        print(f"  [skip] {dest.name} already exists")
        return
    try:
        import geopandas as gpd
    except ImportError:
        print("  geopandas not installed - run: pip install geopandas")
        return

    tmp = RAW / "_dz_tmp"
    try:
        r = requests.get(DATAZONE_BOUNDARIES_URL, headers=HEADERS, timeout=180)
        r.raise_for_status()
        zipfile.ZipFile(io.BytesIO(r.content)).extractall(tmp)
        shp_files = list(tmp.rglob("*.shp"))
        if not shp_files:
            raise FileNotFoundError("No .shp file found in ZIP")
        gdf = gpd.read_file(shp_files[0]).to_crs("EPSG:4326")
        gdf.to_file(dest, driver="GeoJSON")
        print(f"  Saved {len(gdf)} zones -> {dest}")
    except (requests.RequestException, zipfile.BadZipFile, FileNotFoundError, OSError, ValueError) as e:
        print(f"  FAILED: {e}")
    except Exception as e:  # geopandas/pyogrio raise their own error types on read or reprojection
        print(f"  FAILED: {type(e).__name__}: {e}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--boundaries", action="store_true",
                        help="also download data zone boundaries (needs geopandas)")
    args = parser.parse_args()

    RAW.mkdir(exist_ok=True)

    print("\n[1] SIMD 2020v2 indicators (Scottish Government)")
    required_ok = [
        download(SIMD_INDICATORS_URL, RAW / "simd2020_indicators.xlsx", "SIMD 2020v2 indicators")
    ]

    print("\n[2] Fire statistics by type of incident (statistics.gov.scot)")
    required_ok.append(download(FIRE_STATS_URL, RAW / "fire_statistics_scotland.csv", "fire statistics"))

    if args.boundaries:
        print("\n[3] Data zone 2011 boundaries")
        download_boundaries()

    print("\n[manual] raw/simd2020.csv")
    if (RAW / "simd2020.csv").exists():
        print("  [skip] simd2020.csv already exists")
    else:
        print("  Download the SIMD 2020v2 ranks file (CSV with columns DataZone, IntZone, CA,")
        print("  SIMD2020V2CountryDecile, ...) from:")
        print(f"  {SIMD_PAGE}")
        print(f"  and save it as {RAW / 'simd2020.csv'}")

    print("\nFiles in raw/:")
    for f in sorted(RAW.iterdir()):
        print(f"  {f.name:40s} {f.stat().st_size / 1024:>8.0f} KB")

    if not all(required_ok):
        print("\nERROR: a required download failed (see FAILED above).")
        sys.exit(1)


if __name__ == "__main__":
    main()
