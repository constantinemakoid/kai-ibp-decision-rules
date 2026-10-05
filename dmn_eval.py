import operator
import re
import xml.etree.ElementTree as ET

NS = "{https://www.omg.org/spec/DMN/20191111/MODEL/}"
OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "=": operator.eq}
CMP = re.compile(r"^\s*(<=|>=|<|>|=)?\s*(.+?)\s*$")


def literal(tok, ctx=None):
    tok = tok.strip()
    if tok.startswith('"') and tok.endswith('"'):
        return tok[1:-1]
    if tok in ("true", "false"):
        return tok == "true"
    try:
        return float(tok)
    except ValueError:
        return ctx[tok]


def expr(text, ctx):
    m = re.match(r"^\s*(\w+)\s*(<=|>=|<|>|=)\s*(\w+)\s*$", text)
    if m:
        return OPS[m.group(2)](literal(m.group(1), ctx), literal(m.group(3), ctx))
    return ctx[text.strip()]


def split_list(text):
    parts, cur, q = [], "", False
    for ch in text:
        if ch == '"':
            q = not q
        if ch == "," and not q:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def unary(test, value):
    test = test.strip()
    if test in ("-", ""):
        return True
    for part in split_list(test):
        op, rhs = CMP.match(part).groups()
        if OPS[op or "="](value, literal(rhs)):
            return True
    return False


def load(path):
    root = ET.parse(path).getroot()
    out = {}
    for dec in root.iter(NS + "decision"):
        dt = dec.find(NS + "decisionTable")
        inputs = [i.find(NS + "inputExpression").find(NS + "text").text for i in dt.findall(NS + "input")]
        outputs = [(o.get("name"), o.get("typeRef")) for o in dt.findall(NS + "output")]
        rules = []
        for r in dt.findall(NS + "rule"):
            rules.append((r.get("id"), [e.find(NS + "text").text for e in r.findall(NS + "inputEntry")],
                          [e.find(NS + "text").text for e in r.findall(NS + "outputEntry")]))
        out[dec.get("id")] = dict(name=dec.get("name"), hit=dt.get("hitPolicy", "UNIQUE"), inputs=inputs,
                                  outputs=outputs, rules=rules)
    return out


def matches(table, ctx):
    vals = [expr(e, ctx) for e in table["inputs"]]
    return [rid for rid, ins, _ in table["rules"] if all(unary(t, v) for t, v in zip(ins, vals))]


def evaluate(table, ctx):
    hit = matches(table, ctx)
    if len(hit) != 1:
        raise ValueError(f"UNIQUE violated: {hit}")
    rule = next(r for r in table["rules"] if r[0] == hit[0])
    res = {name: literal(t) for (name, _), t in zip(table["outputs"], rule[2])}
    return hit[0], res
