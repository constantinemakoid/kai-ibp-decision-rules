import itertools
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, deque

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}
B = "{%s}" % NS["bpmn"]
FLOW_NODES = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent",
              "userTask", "serviceTask", "businessRuleTask", "exclusiveGateway", "parallelGateway"}


class Model:
    def __init__(self, path):
        self.root = ET.parse(path).getroot()
        self.nodes, self.seq, self.msg, self.performer = {}, [], [], {}
        pools = {p.get("processRef"): p.get("name") for p in self.root.iter(B + "participant")}
        for proc in self.root.iter(B + "process"):
            pname = pools[proc.get("id")]
            lanes = {}
            for lane in proc.iter(B + "lane"):
                for ref in lane.findall(B + "flowNodeRef"):
                    lanes[ref.text] = lane.get("name")
            for el in proc:
                tag = el.tag.replace(B, "")
                if tag in FLOW_NODES:
                    self.nodes[el.get("id")] = dict(type=tag, name=el.get("name") or "", pool=pname)
                    self.performer[el.get("id")] = lanes.get(el.get("id"), pname)
                elif tag == "sequenceFlow":
                    self.seq.append((el.get("id"), el.get("sourceRef"), el.get("targetRef"), el.get("name")))
        for mf in self.root.iter(B + "messageFlow"):
            self.msg.append((mf.get("id"), mf.get("sourceRef"), mf.get("targetRef"), mf.get("name")))
        self.lanes = [l.get("name") for l in self.root.iter(B + "lane")]
        self.pools = list(pools.values())

    def human(self, nid):
        return self.nodes[nid]["type"] == "userTask"

    def main_path(self, start, end):
        out = {}
        for fid, s, t, name in self.seq:
            out.setdefault(s, []).append((t, name))
        path, cur, seen = [start], start, {start}
        while cur != end:
            nxt = out[cur]
            if len(nxt) > 1:
                nxt = [x for x in nxt if x[1] in ("Так", "Відповідає")]
            cur = nxt[0][0]
            if cur in seen:
                raise RuntimeError("cycle")
            seen.add(cur)
            path.append(cur)
        return path

    def metrics(self, start, end, contain):
        types = Counter(n["type"] for n in self.nodes.values())
        path = self.main_path(start, end)
        before = path[:path.index(contain) + 1]
        changes = sum(1 for a, b in zip(path, path[1:]) if self.performer[a] != self.performer[b])
        transfer = {s for _, s, _, _ in self.msg if self.human(s)}
        people = {self.performer[n] for n in self.nodes if self.human(n)}
        transfer |= {s for _, s, t, _ in self.seq
                     if self.human(s) and self.performer[t] in people and self.performer[s] != self.performer[t]}
        outdeg = Counter(s for _, s, _, _ in self.seq)
        msg_by_human = sum(1 for _, s, _, _ in self.msg if self.human(s))
        gws = [n for n in path if self.nodes[n]["type"] == "exclusiveGateway" and outdeg[n] > 1]
        decisions = [n for n, v in self.nodes.items() if v["type"] == "exclusiveGateway" and outdeg[n] > 1]
        return {
            "user_tasks": types["userTask"],
            "service_tasks": types["serviceTask"],
            "rule_tasks": types["businessRuleTask"],
            "tasks": types["userTask"] + types["serviceTask"] + types["businessRuleTask"],
            "main_path_rule_tasks": sum(self.nodes[n]["type"] == "businessRuleTask" for n in path),
            "conditions": sum(1 for _ in self.root.iter(B + "conditionExpression")),
            "feel_conditions": sum(1 for c in self.root.iter(B + "conditionExpression") if (c.text or "").startswith("=")),
            "exclusive_gateways": types["exclusiveGateway"],
            "start_events": types["startEvent"],
            "end_events": types["endEvent"],
            "catch_events": types["intermediateCatchEvent"],
            "throw_events": types["intermediateThrowEvent"],
            "sequence_flows": len(self.seq),
            "message_flows": len(self.msg),
            "pools": len(self.pools),
            "lanes": len(self.lanes),
            "main_path_len": len(path),
            "main_path_user_tasks": sum(self.human(n) for n in path),
            "main_path_service_tasks": sum(self.nodes[n]["type"] == "serviceTask" for n in path),
            "user_tasks_to_containment": sum(self.human(n) for n in before),
            "waits_to_containment": sum(self.nodes[n]["type"] == "intermediateCatchEvent" for n in before),
            "main_path_waits": sum(self.nodes[n]["type"] == "intermediateCatchEvent" for n in path),
            "performer_changes": changes,
            "transfer_tasks_by_human": len(transfer),
            "transfer_tasks_list": sorted(transfer),
            "decision_gateways": len(decisions),
            "messages_sent_by_human": msg_by_human,
            "decision_gateways_on_path": len(gws),
            "path": path,
        }

    def by_performer(self):
        c = {}
        for nid, n in self.nodes.items():
            if n["type"] in ("userTask", "serviceTask", "businessRuleTask"):
                c.setdefault(self.performer[nid], Counter())[n["type"]] += 1
        return {k: dict(v) for k, v in c.items()}


def bounds(root):
    shapes, edges = {}, {}
    for s in root.iter("{%s}BPMNShape" % NS["bpmndi"]):
        b = s.find("dc:Bounds", NS)
        shapes[s.get("bpmnElement")] = tuple(float(b.get(k)) for k in ("x", "y", "width", "height"))
    for e in root.iter("{%s}BPMNEdge" % NS["bpmndi"]):
        edges[e.get("bpmnElement")] = [(float(w.get("x")), float(w.get("y"))) for w in e.findall("di:waypoint", NS)]
    return shapes, edges


def seg_hits_box(p, q, box, pad=1):
    x, y, w, h = box
    x0, x1, y0, y1 = x + pad, x + w - pad, y + pad, y + h - pad
    if p[0] == q[0]:
        lo, hi = sorted((p[1], q[1]))
        return x0 < p[0] < x1 and lo < y1 and hi > y0
    lo, hi = sorted((p[0], q[0]))
    return y0 < p[1] < y1 and lo < x1 and hi > x0


def seg_cross(a, b, c, d):
    if (a[0] == b[0]) == (c[0] == d[0]):
        return False
    if a[0] != b[0]:
        a, b, c, d = c, d, a, b
    x = a[0]
    y = c[1]
    ylo, yhi = sorted((a[1], b[1]))
    xlo, xhi = sorted((c[0], d[0]))
    return xlo < x < xhi and ylo < y < yhi


def geometry(model):
    shapes, edges = bounds(model.root)
    flow_shapes = {k: v for k, v in shapes.items() if k in model.nodes}
    overlaps = [(a, b) for a, b in itertools.combinations(flow_shapes, 2)
                if not (flow_shapes[a][0] + flow_shapes[a][2] <= flow_shapes[b][0]
                        or flow_shapes[b][0] + flow_shapes[b][2] <= flow_shapes[a][0]
                        or flow_shapes[a][1] + flow_shapes[a][3] <= flow_shapes[b][1]
                        or flow_shapes[b][1] + flow_shapes[b][3] <= flow_shapes[a][1])]
    ends = {f[0]: (f[1], f[2]) for f in model.seq + model.msg}
    for task in model.root.iter():
        for da in task.findall(B + "dataInputAssociation"):
            ends[da.get("id")] = (da.findtext(B + "sourceRef"), task.get("id"))
    nonortho, through, crossings = 0, [], []
    segs = {}
    for eid, pts in edges.items():
        segs[eid] = list(zip(pts, pts[1:]))
        for p, q in segs[eid]:
            if p[0] != q[0] and p[1] != q[1]:
                nonortho += 1
            for sid, box in flow_shapes.items():
                if sid in ends[eid]:
                    continue
                if seg_hits_box(p, q, box):
                    through.append((eid, sid))
    for e1, e2 in itertools.combinations(segs, 2):
        for s1 in segs[e1]:
            for s2 in segs[e2]:
                if seg_cross(*s1, *s2):
                    crossings.append((e1, e2))
    pool_box = {p.get("id"): shapes[p.get("id")] for p in model.root.iter(B + "participant")}
    outside = 0
    for proc in model.root.iter(B + "process"):
        pid = [p.get("id") for p in model.root.iter(B + "participant") if p.get("processRef") == proc.get("id")][0]
        px, py, pw, ph = pool_box[pid]
        for el in proc:
            if el.get("id") in flow_shapes:
                x, y, w, h = flow_shapes[el.get("id")]
                if x < px or y < py or x + w > px + pw or y + h > py + ph:
                    outside += 1
    return dict(shapes=len(shapes), edges=len(edges), overlaps=len(overlaps), nonortho=nonortho,
                through=len(through), through_list=through, crossings=len(crossings),
                crossing_list=crossings, outside=outside)


def reachability(model, start):
    adj = {}
    for _, s, t, _ in model.seq + model.msg:
        adj.setdefault(s, []).append(t)
    seen, dq = {start}, deque([start])
    while dq:
        for n in adj.get(dq.popleft(), []):
            if n not in seen:
                seen.add(n)
                dq.append(n)
    radj = {}
    for _, s, t, _ in model.seq:
        radj.setdefault(t, []).append(s)
    ends = [n for n, v in model.nodes.items() if v["type"] == "endEvent"]
    back, dq = set(ends), deque(ends)
    while dq:
        for n in radj.get(dq.popleft(), []):
            if n not in back:
                back.add(n)
                dq.append(n)
    return dict(nodes=len(model.nodes), unreachable=sorted(set(model.nodes) - seen),
                no_path_to_end=sorted(set(model.nodes) - back))


def main(as_is, to_be, out):
    a, t = Model(as_is), Model(to_be)
    res = {
        "as_is": a.metrics("Start_Alert", "End_Report", "Task_SendDecision"),
        "to_be": t.metrics("Start_Alert", "End_Report", "Task_SendDecision"),
        "as_is_perf": a.by_performer(),
        "to_be_perf": t.by_performer(),
        "as_is_geom": geometry(a),
        "to_be_geom": geometry(t),
        "as_is_reach": reachability(a, "Start_Audit"),
        "to_be_reach": reachability(t, "Start_Audit"),
        "to_be_nodes": {k: dict(v, performer=t.performer[k]) for k, v in t.nodes.items()},
        "as_is_nodes": {k: dict(v, performer=a.performer[k]) for k, v in a.nodes.items()},
        "to_be_msg": t.msg,
        "as_is_msg": a.msg,
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    for k in ("as_is", "to_be"):
        print(k, {x: y for x, y in res[k].items() if x != "path"})
    print("geom", {k: v for k, v in res["to_be_geom"].items() if not k.endswith("list")}, res["to_be_geom"]["through_list"], res["to_be_geom"]["crossing_list"])
    print("reach", res["to_be_reach"], res["as_is_reach"])


if __name__ == "__main__":
    main(*sys.argv[1:4])
