#!/usr/bin/env python3
"""Build data/host_maps.json for the interactive host-city explorer.

Combines:
  - schedule.json (104 matches, grouped by `ground` -> city)
  - country coastline outlines (GeoJSON in /tmp/geo-{USA,CAN,MEX}.json)
  - a hand-curated city -> {country, lat, lon, stadium} table

Output structure:
{
  "countries": {
     "USA": { "name":"United States", "outline":[[ [lon,lat],... ], ...] (rings),
              "cities":[ {city, stadium, lat, lon, matches:[...]}, ... ] },
     "MEX": {...}, "CAN": {...}
  }
}
Coastline coords are rounded to 2 decimals to keep the file small; pins use full precision.
"""
import json, os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHED = ROOT / "data" / "schedule.json"
OUT = ROOT / "data" / "host_maps.json"
GEO = {"USA": "/tmp/geo-USA.json", "CAN": "/tmp/geo-CAN.json", "MEX": "/tmp/geo-MEX.json"}

# ground string (from schedule.json) -> metadata
CITY = {
  "Atlanta":                                   ("USA", 33.755, -84.401, "Mercedes-Benz Stadium"),
  "Boston (Foxborough)":                       ("USA", 42.091, -71.264, "Gillette Stadium"),
  "Dallas (Arlington)":                        ("USA", 32.747, -97.093, "AT&T Stadium"),
  "Houston":                                   ("USA", 29.685, -95.411, "NRG Stadium"),
  "Kansas City":                               ("USA", 39.049, -94.484, "Arrowhead Stadium"),
  "Los Angeles (Inglewood)":                   ("USA", 33.953, -118.339, "SoFi Stadium"),
  "Miami (Miami Gardens)":                      ("USA", 25.958, -80.239, "Hard Rock Stadium"),
  "New York/New Jersey (East Rutherford)":     ("USA", 40.814, -74.074, "MetLife Stadium"),
  "Philadelphia":                              ("USA", 39.901, -75.168, "Lincoln Financial Field"),
  "San Francisco Bay Area (Santa Clara)":      ("USA", 37.403, -121.970, "Levi's Stadium"),
  "Seattle":                                   ("USA", 47.595, -122.332, "Lumen Field"),
  "Toronto":                                   ("CAN", 43.633, -79.418, "BMO Field"),
  "Vancouver":                                 ("CAN", 49.277, -123.112, "BC Place"),
  "Mexico City":                               ("MEX", 19.303, -99.150, "Estadio Azteca"),
  "Guadalajara (Zapopan)":                     ("MEX", 20.681, -103.463, "Estadio Akron"),
  "Monterrey (Guadalupe)":                     ("MEX", 25.669, -100.244, "Estadio BBVA"),
}
COUNTRY_NAME = {"USA": "United States", "CAN": "Canada", "MEX": "México"}

# Stadium facts (capacity / opened / one curiosity). Photo slug matches assets/stadiums/<slug>.jpg
import re as _re
def _slug(s): return _re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
STADIUM_META = {
  "SoFi Stadium":            (70240, 2020, "El estadio más caro jamás construido (~5.500 M$), con techo translúcido."),
  "Levi's Stadium":          (68500, 2014, "Casa de los San Francisco 49ers, pionero en sostenibilidad (LEED Gold)."),
  "Lumen Field":             (69000, 2002, "De los estadios más ruidosos de la NFL — el público bate récords de decibelios."),
  "AT&T Stadium":            (80000, 2009, "Techo retráctil y una de las pantallas de vídeo colgantes más grandes del mundo."),
  "NRG Stadium":             (72220, 2002, "Primer estadio de la NFL con techo retráctil."),
  "Arrowhead Stadium":       (76416, 1972, "Récord Guinness al estadio más ruidoso (142,2 dB)."),
  "Mercedes-Benz Stadium":   (71000, 2017, "Su techo se abre como el diafragma de una cámara en 8 pétalos."),
  "Hard Rock Stadium":       (65326, 1987, "Acoge a los Miami Dolphins y el GP de Miami de Fórmula 1."),
  "Lincoln Financial Field": (69596, 2003, "Casa de los Philadelphia Eagles, conocido como 'The Linc'."),
  "MetLife Stadium":         (82500, 2010, "Sede de la FINAL (19 jul). Lo comparten Giants y Jets."),
  "Gillette Stadium":        (65878, 2002, "Casa de los New England Patriots, en Foxborough."),
  "BMO Field":               (45000, 2007, "Primer estadio específico de fútbol de la MLS en Canadá; ampliado para el Mundial."),
  "BC Place":                (54500, 1983, "Techo retráctil sostenido por cables; renovado en 2011."),
  "Estadio Azteca":          (83264, 1966, "Único estadio que albergará 3 Mundiales (1970, 1986, 2026). A 2.200 m de altitud."),
  "Estadio Akron":           (46232, 2010, "Casa del Chivas; su exterior cubierto de césped imita un volcán."),
  "Estadio BBVA":            (53500, 2015, "'El Gigante de Acero', con vistas al Cerro de la Silla."),
}


def load_matches():
    raw = json.load(open(SCHED))
    # schedule.json is a dict; find the list of matches
    matches = None
    if isinstance(raw, list):
        matches = raw
    else:
        for v in raw.values():
            if isinstance(v, list):
                matches = v; break
        if matches is None:
            matches = list(raw.values())
    by_city = defaultdict(list)
    for m in matches:
        by_city[m["ground"]].append({
            "round": m.get("round"), "date": m.get("date"), "time": m.get("time"),
            "team1": m.get("team1"), "team2": m.get("team2"), "group": m.get("group"),
        })
    # sort each city's matches by date
    for c in by_city:
        by_city[c].sort(key=lambda x: (x["date"] or "", x["time"] or ""))
    return by_city


def extract_rings(geojson_path, round_to=2, min_ring_pts=8):
    """Return list of rings; each ring = list of [lon,lat]. Drops tiny islands."""
    d = json.load(open(geojson_path))
    rings = []
    for feat in d["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            outer = poly[0]  # exterior ring only (skip holes)
            if len(outer) < min_ring_pts:
                continue
            ring = [[round(pt[0], round_to), round(pt[1], round_to)] for pt in outer]
            rings.append(ring)
    return rings


def main():
    by_city = load_matches()
    out = {"countries": {}}
    for code, geopath in GEO.items():
        rings = extract_rings(geopath)
        cities = []
        for ground, (cc, lat, lon, stadium) in CITY.items():
            if cc != code:
                continue
            cap, opened, fact = STADIUM_META.get(stadium, (None, None, None))
            cities.append({
                "city": ground,
                "stadium": stadium,
                "photo": f"assets/stadiums/{_slug(stadium)}.jpg",
                "capacity": cap,
                "opened": opened,
                "fact": fact,
                "lat": lat, "lon": lon,
                "matches": by_city.get(ground, []),
            })
        # sort cities west->east for a stable list order
        cities.sort(key=lambda c: c["lon"])
        out["countries"][code] = {
            "name": COUNTRY_NAME[code],
            "outline": rings,
            "cities": cities,
        }
        nmatch = sum(len(c["matches"]) for c in cities)
        print(f"{code}: {len(rings)} rings, {len(cities)} cities, {nmatch} matches")

    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"\nWrote {OUT} ({OUT.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
