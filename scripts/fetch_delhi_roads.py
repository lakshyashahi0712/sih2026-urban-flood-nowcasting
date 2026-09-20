"""Fetch the Delhi/Kushak pilot road network from OpenStreetMap (build-time).

Acquires the routable road network around the Kushak-Barapullah corridor
(South Delhi) ONCE via the Overpass API and writes it as a committed data
artifact with a provenance sidecar — the same pattern as the Mumbai pilot
network (``mumbai_pilot_roads.geojson``).

This is NOT a runtime dependency: routing reads the committed GeoJSON.
The acquisition bbox, Overpass query, and timestamp are recorded in the
sidecar so the network's provenance is auditable.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Bounded extraction window around the Kushak corridor and its approach
# network (Africa Avenue / Ring Road, AIIMS, Defence Colony, Lajpat Nagar,
# Green Park, Lodhi Road). Deliberately small: a pilot network, not a city
# extract.
BBOX = (77.185, 28.545, 77.275, 28.600)  # (min_lon, min_lat, max_lon, max_lat)

HIGHWAY_FILTER = (
    '["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|'
    'unclassified|motorway_link|trunk_link|primary_link|secondary_link|'
    'tertiary_link|living_street|service)$"]'
)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

QUERY = f"""
[out:json][timeout:60];
way{HIGHWAY_FILTER}({BBOX[1]},{BBOX[0]},{BBOX[3]},{BBOX[2]});
out geom;
"""

OUT_PATH = Path(__file__).resolve().parents[1] / "backend" / "app" / "data" / "roads" / "delhi_kushak_roads.geojson"
PROVENANCE_PATH = OUT_PATH.with_suffix(".provenance.json")


def fetch() -> dict:
    request = urllib.request.Request(
        OVERPASS_URL,
        data=QUERY.encode("utf-8"),
        headers={"User-Agent": "sih2026-flood-nowcasting/1.0 (build-time data acquisition)"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def to_featurecollection(payload: dict) -> dict:
    features = []
    for element in payload.get("elements", []):
        if element.get("type") != "way" or "geometry" not in element:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in element["geometry"]]
        if len(coords) < 2:
            continue
        tags = element.get("tags", {})
        features.append({
            "type": "Feature",
            "properties": {
                "osm_id": element["id"],
                "name": tags.get("name", ""),
                "highway": tags.get("highway", ""),
                "oneway": tags.get("oneway", ""),
                "surface": tags.get("surface", ""),
                "lanes": tags.get("lanes", ""),
            },
            "geometry": {"type": "LineString", "coordinates": coords},
        })
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    payload = fetch()
    fc = to_featurecollection(payload)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    PROVENANCE_PATH.write_text(json.dumps({
        "source": "OpenStreetMap via Overpass API",
        "overpass_url": OVERPASS_URL,
        "bbox": BBOX,
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "query": QUERY,
        "feature_count": len(fc["features"]),
        "note": (
            "Build-time acquisition of the Delhi/Kushak pilot road network. "
            "ODbL license; network geometry is OSM-derived evidence, not an "
            "as-built survey."
        ),
    }, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(fc['features'])} features)")


if __name__ == "__main__":
    main()
