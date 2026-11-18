"""Turn the raw breadsheet export into the compact, normalized data the mockups use.

Usage: python3 -I scripts/prep.py data/records.json > data/breads.js
"""

import json
import math
import sys

raw = json.load(open(sys.argv[1]))["records"]

# Ingredient name -> (canonical ingredient, family). Families drive color.
CANON = [
    ("psyllium", "Psyllium", "binder"),
    ("flax", "Flax", "seed"),
    ("buckwheat", "Buckwheat flour", "grain"),
    ("brown rice", "Rice flour", "gf"),
    ("oat flour", "Oat flour", "gf"),
    ("tapioca", "Tapioca starch", "gf"),
    ("potato starch", "Potato starch", "gf"),
    ("sorghum", "Sorghum flour", "gf"),
    ("bob's 1:1", "GF flour blend", "gf"),
    ("rye berries", "Rye berries", "grain"),
    ("cracked rye", "Cracked rye", "grain"),
    ("rye", "Rye flour", "grain"),
    ("whole wheat", "Whole wheat flour", "grain"),
    ("potato water", "Potato water", "liquid"),
    ("water/milk", "Milk", "dairy"),
    ("water", "Water", "liquid"),
    ("buttermilk", "Buttermilk", "dairy"),
    ("milk", "Milk", "dairy"),
    ("ricotta", "Ricotta", "dairy"),
    ("butter", "Butter", "fat"),
    ("olive oil", "Olive oil", "fat"),
    ("coconut", "Coconut oil", "fat"),
    ("canola", "Neutral oil", "fat"),
    ("oil", "Neutral oil", "fat"),
    ("egg", "Eggs", "egg"),
    ("honey", "Honey", "sweet"),
    ("maple", "Maple syrup", "sweet"),
    ("syrup", "Maple syrup", "sweet"),
    ("malt", "Malt", "sweet"),
    ("brown sugar", "Sugar", "sweet"),
    ("sugar", "Sugar", "sweet"),
    ("lemon", "Lemon", "flavor"),
    ("rum", "Rum", "flavor"),
    ("vanilla", "Vanilla", "flavor"),
    ("poppy", "Poppy seeds", "seed"),
    ("seeds", "Seeds", "seed"),
    ("mix-ins", "Seeds", "seed"),
    ("lye", "Lye bath", "leaven"),
    ("baking powder", "Baking powder", "leaven"),
    ("baking soda", "Baking soda", "leaven"),
    ("poolish", "Poolish", "starter"),
    ("starter", "Starter", "starter"),
    ("salt", "Salt", "salt"),
    ("flour", "White flour", "flour"),
]

# Share of each ingredient that is water, for an effective hydration figure.
WATER_SHARE = {"Water": 1, "Potato water": 1, "Milk": 0.87, "Buttermilk": 0.9, "Eggs": 0.75, "Lemon": 0.9}

GF_IDS = {"gf-c-v-bread", "gf-pizza-dough", "gluten-free-dan-bread"}


def canon(name, rid):
    n = name.lower()
    for key, c, fam in CANON:
        if key in n:
            if c == "White flour" and rid in GF_IDS:
                return "GF flour blend", "gf"
            if c == "Rye flour" and "crack" in n:
                return "Cracked rye", "grain"
            return c, fam
    raise SystemExit(f"unmapped ingredient: {name}")


out = []
for r in raw:
    d = r["data"]
    rid = r["id"]
    ings = []
    flour = water = enrich = 0.0
    for i in d["ingredients"]:
        c, fam = canon(i["name"], rid)
        pct = i.get("percent")
        stage = i.get("stage")
        ings.append(
            {
                "name": i["name"],
                "c": c,
                "fam": fam,
                "pct": pct,
                **({"stage": stage} if stage else {}),
                **({"opt": True} if i.get("optional") else {}),
                **({"note": i["note"]} if i.get("note") else {}),
            }
        )
        if pct is None or stage == "bath":
            continue
        if i["role"] == "flour" or fam == "grain":
            flour += pct
        elif fam in ("starter",):
            flour += pct / 2
            water += pct / 2
        elif c in WATER_SHARE:
            water += pct * WATER_SHARE[c]
        if fam in ("fat", "sweet", "egg") or c == "Ricotta":
            if not i.get("optional"):
                enrich += pct
    starter = sum(i["pct"] or 0 for i in ings if i["fam"] == "starter")
    total = sum(i["pct"] or 0 for i in ings if i.get("stage") != "bath" and not i.get("opt"))
    steps = [s for m in d.get("method", []) for s in m["steps"]]
    out.append(
        {
            "id": rid,
            "title": d["title"],
            "tags": d.get("tags", []),
            "base": d.get("baseFlourGrams"),
            "scale": d.get("scaleNote"),
            "headnotes": d.get("headnotes", []),
            "sources": d.get("sources", []),
            "steps": len(steps),
            "firstStep": steps[0] if steps else None,
            "ings": ings,
            "hyd": round(100 * water / flour, 1),
            "enrich": round(enrich, 1),
            "starter": round(starter, 1),
            "total": round(total, 1),
        }
    )

# Nearest neighbours on a vector of ingredient families (log-scaled so a
# 90% sugar cake doesn't drown everything else).
fams = sorted({i["fam"] for r in out for i in r["ings"]})


def vec(r):
    v = dict.fromkeys(fams, 0.0)
    for i in r["ings"]:
        if i["pct"] and i.get("stage") != "bath":
            v[i["fam"]] += i["pct"]
    return [math.log1p(v[f]) for f in fams]


V = {r["id"]: vec(r) for r in out}
for r in out:
    ds = sorted(
        (math.dist(V[r["id"]], V[o["id"]]), o["id"]) for o in out if o["id"] != r["id"]
    )
    r["near"] = [o for _, o in ds[:2]]

print("window.BREADS = " + json.dumps(out, ensure_ascii=False) + ";")
for r in out:
    print(
        f"// {r['id']:26s} hyd {r['hyd']:6.1f}  enrich {r['enrich']:6.1f}  starter {r['starter']:5.1f}  total {r['total']:6.1f}  near {r['near']}",
    )
