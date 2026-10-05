import json
from decimal import ROUND_HALF_UP, Decimal

WEIGHTS = {"f1": 0.30, "f2": 0.15, "f3": 0.20, "f4": 0.20, "f5": 0.05, "f6": 0.10}
LABEL = {0: 0.0, 1: 0.5, 2: 1.0}
FIELDS = ("id", "n", "mu", "sigma", "copied", "label", "grant", "offhours", "dlp")
EVENTS = [
    dict(zip(FIELDS, ("A", 240, 35, 15, 180, 2, False, False, False))),
    dict(zip(FIELDS, ("B", 60, 40, 12, 5, 1, True, False, False))),
    dict(zip(FIELDS, ("C", 70, 30, 20, 10, 1, False, True, False))),
]


def rnd(x, d):
    return float(Decimal(repr(x)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))


def level(r):
    if r >= 70:
        return "високий"
    if r >= 40:
        return "середній"
    return "низький"


def score(e):
    z = (e["n"]-e["mu"]) / e["sigma"]
    f = {
        "f1": min(1.0, max(0.0, z / 3)),
        "f2": e["copied"] / e["n"],
        "f3": LABEL[e["label"]],
        "f4": 0.0 if e["grant"] else 1.0,
        "f5": 1.0 if e["offhours"] else 0.0,
        "f6": 1.0 if e["dlp"] else 0.0,
    }
    contrib = {k: WEIGHTS[k] * v for k, v in f.items()}
    r = 100 * min(1.0, sum(contrib.values()))
    return {"id": e["id"], "z": z, "f": f, "contrib": contrib, "R": r, "level": level(r)}


if __name__ == "__main__":
    res = [score(e) for e in EVENTS]
    for x in res:
        print(x["id"], rnd(x["z"], 2), rnd(x["R"], 2), rnd(x["R"], 1), x["level"])
    with open("risk_examples.json", "w", encoding="utf-8") as fh:
        data = {"weights": WEIGHTS, "events": EVENTS, "results": res}
        json.dump(data, fh, ensure_ascii=False, indent=1)
