import json
import os
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "node_modules", "dmn-js", "dist")

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{lib}/assets/dmn-js-shared.css">
<link rel="stylesheet" href="file://{lib}/assets/dmn-js-decision-table.css">
<link rel="stylesheet" href="file://{lib}/assets/dmn-js-drd.css">
<link rel="stylesheet" href="file://{lib}/assets/dmn-font/css/dmn.css">
<style>html,body{{margin:0;background:#fff;font-family:Arial,sans-serif}}#c{{width:{w}px;padding:8px;box-sizing:border-box}}
.tjs-table th,.tjs-table td{{min-width:0!important;width:auto!important;max-width:230px;white-space:normal!important}}
.tjs-table{{table-layout:auto!important;width:auto!important;min-width:780px!important}}
.tjs-table .annotation{{min-width:210px!important}}
.tjs-table th.input-cell,.tjs-table th.output-cell{{min-width:135px!important}}
.powered-by-logo,.dmn-definitions,.bjs-powered-by{{display:none!important}}</style>
<script src="file://{lib}/dmn-viewer.development.js"></script></head>
<body><div id="c"></div><pre id="r"></pre><script>
const xml = {xml};
const v = new DmnJS({{container: '#c'}});
(async () => {{
  const res = await v.importXML(xml);
  const view = v.getViews().find(x => x.element.id === '{decision}' && x.type === 'decisionTable');
  await v.open(view);
  document.querySelectorAll('button').forEach(b => {{ if (b.textContent.includes('DRD')) b.parentElement.style.display = 'none'; }});
  const rules = document.querySelectorAll('tbody tr').length;
  document.getElementById('r').textContent = 'RESULT' + JSON.stringify({{warnings: res.warnings.length, rules,
    height: document.getElementById('c').scrollHeight, width: document.querySelector('table').scrollWidth}});
  document.getElementById('r').style.display = 'none';
}})();
</script></body></html>"""


def render(dmn, decision, png, w=1000, scale=2):
    res = shot(dmn, decision, png, w, scale, False)
    return shot(dmn, decision, png, res["width"] + 20, scale, True)


def shot(dmn, decision, png, w, scale, save):
    xml = open(dmn, encoding="utf-8").read()
    html = PAGE.format(lib=LIB, xml=json.dumps(xml), decision=decision, w=w)
    page = os.path.join(HERE, f"render_{decision}.html")
    open(page, "w", encoding="utf-8").write(html)
    common = [CHROME, "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
              "--hide-scrollbars", "--virtual-time-budget=8000"]
    dom = subprocess.run(common + ["--dump-dom", "file://" + page], capture_output=True, text=True).stdout
    res = json.loads(dom.split("RESULT", 1)[1].split("<", 1)[0].replace("&quot;", '"'))
    hh = res["height"] + 4
    if save:
        subprocess.run(common + [f"--window-size={w},{hh}", f"--force-device-scale-factor={scale}",
                                 f"--screenshot={png}", "file://" + page], capture_output=True)
    os.remove(page)
    return res


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2], sys.argv[3]))
