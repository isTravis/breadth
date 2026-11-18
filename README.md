# Breadth

A bread explorer sketch for Gabe's Breadsheet collection on Underlay
(https://www.underlay.org/gabestein/breadsheet). Not a KF project.

Five views, routed by hash: #portraits, #map, #web, #schedule, #lineage.

- `index.html` — the page (open in a browser; loads `data/*.js`)
- `dist/breadth.html` — single-file build with the data inlined
- `data/records.json` — raw records from the Underlay read API (v1.3.0)
- `data/breads.js` — normalized formulas, from `scripts/prep.py`
- `data/schedule.js` — bake timelines read by hand from each recipe's method steps

Rebuild:

    python3 -I scripts/prep.py data/records.json > data/breads.js
    python3 -I scripts/bundle.py index.html dist/breadth.html
