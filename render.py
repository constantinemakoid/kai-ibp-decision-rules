import json
import os
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "node_modules", "bpmn-js", "dist")

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{lib}/assets/diagram-js.css">
<link rel="stylesheet" href="file://{lib}/assets/bpmn-js.css">
<link rel="stylesheet" href="file://{lib}/assets/bpmn-font/css/bpmn.css">
<style>html,body{{margin:0;background:#fff}}#c{{width:{w}px;height:{h}px}}</style>
<script src="file://{lib}/bpmn-modeler.development.js"></script></head>
<body><div id="c"></div><pre id="r"></pre><script>
const xml = {xml};
const m = new BpmnJS({{container: '#c'}});
(async () => {{
  const a = await m.importXML(xml);
  const reg = m.get('elementRegistry').getAll().length;
  const exp = (await m.saveXML({{format: true}})).xml;
  const m2 = new BpmnJS({{container: document.createElement('div')}});
  const b = await m2.importXML(exp);
  const reg2 = m2.get('elementRegistry').getAll().length;
  const cv = m.get('canvas');
  cv.viewbox({{x: {vx}, y: {vy}, width: {w}, height: {h}}});
  document.querySelectorAll('.djs-palette,.bjs-powered-by').forEach(e => e.style.display = '{logo}');
  document.querySelector('.djs-palette') && (document.querySelector('.djs-palette').style.display = 'none');
  document.getElementById('r').textContent = 'RESULT' + JSON.stringify({{warn1: a.warnings.length, warn2: b.warnings.length, reg, reg2}});
}})();
</script></body></html>"""


def render(bpmn, png, vx, vy, w, h, scale=2):
    xml = open(bpmn, encoding="utf-8").read()
    html = PAGE.format(lib=LIB, xml=json.dumps(xml), vx=vx, vy=vy, w=w, h=h, logo="block")
    page = os.path.join(HERE, "render_" + os.path.splitext(os.path.basename(png))[0] + ".html")
    open(page, "w", encoding="utf-8").write(html)
    common = [CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
              "--hide-scrollbars", "--virtual-time-budget=8000"]
    dom = subprocess.run(common + ["--dump-dom", "file://" + page], capture_output=True, text=True).stdout
    res = json.loads(dom.split("RESULT", 1)[1].split("<", 1)[0].replace("&quot;", '"'))
    subprocess.run(common + [f"--window-size={w},{h}", f"--force-device-scale-factor={scale}",
                             f"--screenshot={png}", "file://" + page], capture_output=True)
    os.remove(page)
    return res


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])))
