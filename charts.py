import json
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from PIL import Image

BLUE, ORANGE, TEAL, YELLOW, PINK = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
TXT, TXT2, GRID = "#0b0b0b", "#52514e", "#e1e0d9"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": TXT,
                     "axes.labelcolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT})

res = json.load(open("scenario_results.json", encoding="utf-8"))
COLORS = {
    ("ескалувати", "високий"): (ORANGE, ""),
    ("ескалувати", "середній"): (YELLOW, ""),
    ("закрити як штатну", "низький"): (BLUE, ""),
    ("підстави відсутні", True): (ORANGE, "///"),
    ("підстави відсутні", False): (ORANGE, ""),
    ("потрібне уточнення", True): (PINK, "///"),
    ("потрібне уточнення", False): (PINK, ""),
    ("підстави наявні", False): (BLUE, ""),
    ("відповідає",): (TEAL, ""),
    ("повторити передачу",): (YELLOW, ""),
    ("ескалувати фахівцю",): (ORANGE, ""),
}
LEGENDS = {
    "D1": [(ORANGE, "", "ескалувати, пріоритет високий"), (YELLOW, "", "ескалувати, пріоритет середній"),
           (BLUE, "", "закрити як штатну")],
    "D2": [(ORANGE, "", "підстави відсутні"), (PINK, "", "потрібне уточнення"), (BLUE, "", "підстави наявні"),
           ("white", "///", "обтяжуючі ознаки")],
    "D3": [(TEAL, "", "відповідає"), (YELLOW, "", "повторити передачу"), (ORANGE, "", "ескалувати фахівцю")],
}


def yn(v):
    return "так" if v else "ні"


def legend(ax, key, ncol):
    handles = [Patch(facecolor=c, edgecolor=TXT2 if h else c, hatch=h, label=l) for c, h, l in LEGENDS[key]]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=ncol, frameon=False,
              fontsize=9, handlelength=1.6)


def grid(ax, rows, cols, cell, title, rlab, clab):
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            rule, (color, hatch) = cell(r, c)
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=color, edgecolor="white", linewidth=2))
            if hatch:
                ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor="none", edgecolor=TXT2, hatch=hatch,
                                           linewidth=0))
            ax.text(j + 0.5, i + 0.5, rule, ha="center", va="center", fontsize=10, color=TXT, weight="bold")
    ax.set_xlim(0, len(cols))
    ax.set_ylim(len(rows), 0)
    ax.set_xticks([j + 0.5 for j in range(len(cols))])
    ax.set_xticklabels([clab(c) for c in cols], fontsize=8.5)
    ax.set_yticks([i + 0.5 for i in range(len(rows))])
    ax.set_yticklabels([rlab(r) for r in rows], fontsize=8.5)
    ax.set_title(title, fontsize=11, color=TXT)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)


def lookup(dec, pred):
    for x in res["coverage"][dec]:
        if pred(x["ctx"]):
            return x["rule"], COLORS[tuple(x["out"].values())[:2] if dec != "D3_Containment" else
                                     (x["out"]["result"],)]
    raise KeyError(dec)


def coverage_chart():
    fig = plt.figure(figsize=(11, 8.2), dpi=200)
    g = fig.add_gridspec(2, 2, height_ratios=[1.25, 1], hspace=0.55, wspace=0.55)
    ax1 = fig.add_subplot(g[0, :])
    rows1 = [(lv, d) for lv in ("високий", "середній", "низький") for d in (True, False)]
    cols1 = [(o, n) for o in (True, False) for n in (True, False)]
    grid(ax1, rows1, cols1,
         lambda r, c: lookup("D1_Significance", lambda x: (x["riskLevel"], x["dlpExternal"], x["overProfile"],
                                                          x["noGrant"]) == (r[0], r[1], c[0], c[1])),
         f"D1: {len(rows1) * len(cols1)} комбінації умов", lambda r: f"рівень {r[0]}, f6 = 1: {yn(r[1])}",
         lambda c: f"f1 > 0: {yn(c[0])}\nf4 = 1: {yn(c[1])}")
    ax2 = fig.add_subplot(g[1, 0])
    rows2 = [(k, hr) for k in (0, 5) for hr in (True, False)]
    cols2 = [(h, d) for h in (1, 0) for d in (True, False)]
    grid(ax2, rows2, cols2,
         lambda r, c: lookup("D2_Grounds", lambda x: (x["outsideFiles"], x["hrOrder"], x["priorIncidents"],
                                                     x["dlpExternal"]) == (r[0], r[1], c[0], c[1])),
         "D2: 16 комбінацій умов", lambda r: f"k {'> 0' if r[0] else '= 0'}, наказ: {yn(r[1])}",
         lambda c: f"h {'> 0' if c[0] else '= 0'}\nf6 = 1: {yn(c[1])}")
    ax3 = fig.add_subplot(g[1, 1])
    rows3 = ["немає", "залишкові права", "надмірне обмеження"]
    cols3 = [1, 2, 3, 4]
    grid(ax3, rows3, cols3,
         lambda r, c: lookup("D3_Containment", lambda x: (x["mismatch"], x["attempt"]) == (r, c)),
         f"D3: 12 комбінацій, Kmax = {res['params']['K_MAX']}", lambda r: r, lambda c: f"n = {c}")
    legend(ax1, "D1", 3)
    legend(ax2, "D2", 2)
    legend(ax3, "D3", 1)
    fig.subplots_adjust(left=0.2, right=0.97, top=0.95, bottom=0.17)
    fig.savefig("fig_coverage.png")


DI = {"bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI", "dc": "http://www.omg.org/spec/DD/20100524/DC"}
FRAGMENTS = {
    "fig_model_part1.png": (290, 280, 1930, 1040),
    "fig_model_part2.png": (1930, 520, 3545, 1040),
}
HEADER = (160, 222)


def boxes(path):
    root = ET.parse(path).getroot()
    out = []
    for tag in ("BPMNShape", "BPMNEdge"):
        for el in root.iter("{%s}%s" % (DI["bpmndi"], tag)):
            if el.get("bpmnElement").startswith(("Participant", "Lane")):
                continue
            for b in el.iter("{%s}Bounds" % DI["dc"]):
                x, y, w, h = (float(b.get(k)) for k in ("x", "y", "width", "height"))
                out.append((el.get("bpmnElement"), x, y, x + w, y + h))
    return out


def clipped(frame, items, margin=4):
    fx0, fy0, fx1, fy1 = frame
    bad = []
    for eid, x0, y0, x1, y1 in items:
        inter = x0 < fx1 and x1 > fx0 and y0 < fy1 and y1 > fy0
        inside = x0 >= fx0 + margin and x1 <= fx1 - margin and y0 >= fy0 + margin and y1 <= fy1 - margin
        if inter and not inside:
            bad.append(eid)
    return bad


def crops(bpmn="Лабораторна_4_модель_з_правилами.bpmn", png="Лабораторна_4_діаграма_з_правилами.png", vx=140,
          vy=10, scale=2):
    im = Image.open(png)
    items = boxes(bpmn)
    for name, frame in FRAGMENTS.items():
        bad = clipped(frame, items)
        if bad:
            raise SystemExit(f"{name}: {bad}")
        x0, y0, x1, y1 = frame
        hx0, hx1 = HEADER
        head = im.crop(tuple(int(v) for v in ((hx0 - vx) * scale, (y0 - vy) * scale, (hx1 - vx) * scale,
                                              (y1 - vy) * scale)))
        body = im.crop(tuple(int(v) for v in ((x0 - vx) * scale, (y0 - vy) * scale,
                                              (x1 - vx) * scale, (y1 - vy) * scale)))
        gap = 6 * scale
        out = Image.new("RGB", (head.width + gap + body.width, body.height), "white")
        out.paste(head, (0, 0))
        out.paste(body, (head.width + gap, 0))
        out.save(name)


coverage_chart()
crops()
