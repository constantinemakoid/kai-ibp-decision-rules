import itertools
import json
import subprocess

import dmn_eval
import rules
from risk_score import score

DMN = "Лабораторна_4_правила_рішень.dmn"
LEVELS = ("високий", "середній", "низький")
MISMATCH = ("немає", "залишкові права", "надмірне обмеження")

FIELDS = ("id", "n", "mu", "sigma", "copied", "label", "grant", "offhours", "dlp", "soc_override")
EVENTS = [
    dict(zip(FIELDS, ("A", 240, 35, 15, 180, 2, False, False, False, False))),
    dict(zip(FIELDS, ("B", 60, 40, 12, 5, 1, True, False, False, False))),
    dict(zip(FIELDS, ("C", 70, 30, 20, 10, 1, False, True, False, False))),
    dict(zip(FIELDS, ("D", 50, 40, 10, 10, 1, False, False, True, False))),
    dict(zip(FIELDS, ("E", 20, 30, 10, 2, 0, False, False, True, False))),
    dict(zip(FIELDS, ("F", 45, 40, 10, 3, 0, False, False, False, False))),
    dict(zip(FIELDS, ("G", 25, 30, 10, 0, 1, False, False, False, True))),
]
GROUNDS = [
    ("A", 240, False, 0),
    ("C", 70, True, 0),
    ("D", 50, False, 0),
    ("E", 20, False, 2),
    ("F", 0, False, 0),
    ("G", 25, True, 1),
]
CONTAINMENT = [
    ("S1", "немає", 1),
    ("S2", "залишкові права", 1),
    ("S3", "залишкові права", 2),
    ("S4", "залишкові права", 3),
    ("S5", "надмірне обмеження", 1),
]
BOUNDARY = [39.9, 40.0, 69.9, 70.0]


def rid(x):
    return x.replace("_", ".").rstrip("ab")


def d1_ctx(level, over, no_grant, dlp):
    return {"riskLevel": level, "overProfile": over, "noGrant": no_grant, "dlpExternal": dlp}


def d2_ctx(k, hr, h, dlp):
    return {"outsideFiles": k, "hrOrder": hr, "priorIncidents": h, "dlpExternal": dlp}


def d3_ctx(mismatch, attempt):
    return {"mismatch": mismatch, "attempt": attempt, "maxAttempts": rules.K_MAX}


def main():
    tables = dmn_eval.load(DMN)
    cases, d1_rows, d2_rows, d3_rows = [], [], [], []
    flags = {}
    for e in EVENTS:
        s = score(e)
        level = rules.risk_level(s["R"])
        over, no_grant, dlp = s["f"]["f1"] > 0, s["f"]["f4"] == 1, s["f"]["f6"] == 1
        flags[e["id"]] = dlp
        ref = rules.d1(level, over, no_grant, dlp)
        ctx = d1_ctx(level, over, no_grant, dlp)
        hit, out = dmn_eval.evaluate(tables["D1_Significance"], ctx)
        final = rules.d1_final(ref[1], ref[3], e["soc_override"])
        d1_rows.append(dict(id=e["id"], z=s["z"], R=s["R"], level=level, over=over, no_grant=no_grant, dlp=dlp,
                            ref_rule=ref[0], ref=list(ref[1:]), dmn_rule=rid(hit), dmn=out,
                            soc_override=e["soc_override"], final=final))
        cases.append({"id": "D1_" + e["id"], "decision": "D1_Significance", "context": ctx})
    for eid, k, hr, h in GROUNDS:
        dlp = flags[eid]
        ref = rules.d2(k, hr, h, dlp)
        ctx = d2_ctx(k, hr, h, dlp)
        hit, out = dmn_eval.evaluate(tables["D2_Grounds"], ctx)
        d2_rows.append(dict(id=eid, k=k, hr=hr, h=h, dlp=dlp, ref_rule=ref[0], ref=list(ref[1:]),
                            dmn_rule=rid(hit), dmn=out))
        cases.append({"id": "D2_" + eid, "decision": "D2_Grounds", "context": ctx})
    for sid, mm, att in CONTAINMENT:
        ref = rules.d3(mm, att)
        ctx = d3_ctx(mm, att)
        hit, out = dmn_eval.evaluate(tables["D3_Containment"], ctx)
        d3_rows.append(dict(id=sid, mismatch=mm, attempt=att, k_max=rules.K_MAX, ref_rule=ref[0], ref=list(ref[1:]),
                            dmn_rule=rid(hit), dmn=out))
        cases.append({"id": "D3_" + sid, "decision": "D3_Containment", "context": ctx})

    domains = {
        "D1_Significance": [d1_ctx(*c) for c in itertools.product(LEVELS, (True, False), (True, False),
                                                                   (True, False))],
        "D2_Grounds": [d2_ctx(*c) for c in itertools.product((0, 5), (True, False), (0, 1), (True, False))],
        "D3_Containment": [d3_ctx(*c) for c in itertools.product(MISMATCH, (1, 2, 3, 4))],
    }
    refs = {
        "D1_Significance": lambda c: rules.d1(c["riskLevel"], c["overProfile"], c["noGrant"], c["dlpExternal"]),
        "D2_Grounds": lambda c: rules.d2(c["outsideFiles"], c["hrOrder"], c["priorIncidents"], c["dlpExternal"]),
        "D3_Containment": lambda c: rules.d3(c["mismatch"], c["attempt"]),
    }
    exhaustive, coverage = {}, {}
    for dec, ctxs in domains.items():
        stat = dict(combinations=len(ctxs), no_rule=0, multi_rule=0, ref_mismatch=0, rules_used=set())
        cov = []
        for i, c in enumerate(ctxs):
            hits = dmn_eval.matches(tables[dec], c)
            if not hits:
                stat["no_rule"] += 1
                continue
            if len(hits) > 1:
                stat["multi_rule"] += 1
                continue
            _, out = dmn_eval.evaluate(tables[dec], c)
            ref = refs[dec](c)
            if rid(hits[0]) != ref[0] or list(out.values())[:len(ref) - 1] != list(ref[1:]):
                stat["ref_mismatch"] += 1
            stat["rules_used"].add(hits[0])
            cov.append(dict(ctx=c, rule=rid(hits[0]), out=out))
            cases.append({"id": f"X_{dec}_{i}", "decision": dec, "context": c})
        stat["rules_used"] = len(stat["rules_used"])
        stat["rules_total"] = len(tables[dec]["rules"])
        exhaustive[dec] = stat
        coverage[dec] = cov

    with open("cases.json", "w", encoding="utf-8") as fh:
        json.dump(cases, fh, ensure_ascii=False)
    js = json.loads(subprocess.run(["node", "eval_dmn.mjs", DMN, "cases.json"], capture_output=True, text=True,
                                   check=True).stdout)
    py = {}
    for c in cases:
        _, out = dmn_eval.evaluate(tables[c["decision"]], c["context"])
        py[c["id"]] = out
    js_diff = [x["id"] for x in js if x.get("result") != py[x["id"]]]
    boundary = [(r, rules.risk_level(r)) for r in BOUNDARY]
    res = dict(d1=d1_rows, d2=d2_rows, d3=d3_rows, exhaustive=exhaustive, coverage=coverage,
               js_cases=len(js), js_diff=js_diff, boundary=boundary,
               params=dict(R_MED=rules.R_MED, R_HIGH=rules.R_HIGH, K_MAX=rules.K_MAX))
    with open("scenario_results.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    for k in ("d1", "d2", "d3"):
        for row in res[k]:
            print(k, row["id"], row["ref_rule"], row["dmn_rule"], row["ref"], row["dmn"], row.get("final", ""))
    print(json.dumps(exhaustive, ensure_ascii=False))
    print("js", len(js), "diff", js_diff, boundary)


if __name__ == "__main__":
    main()
