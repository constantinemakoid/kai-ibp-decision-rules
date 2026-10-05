import fs from 'fs';
import { BpmnModdle } from 'bpmn-moddle';
import { DmnModdle } from 'dmn-moddle';
import zeebe from 'zeebe-bpmn-moddle/resources/zeebe.json' with { type: 'json' };
import Linter from 'bpmnlint/lib/linter.js';
import NodeResolver from 'bpmnlint/lib/resolver/node-resolver.js';

const files = process.argv.slice(2);
const out = {};
for (const f of files) {
  const xml = fs.readFileSync(f, 'utf8');
  if (f.endsWith('.dmn')) {
    const dm = new DmnModdle();
    const r = await dm.fromXML(xml, 'dmn:Definitions');
    const decisions = r.rootElement.drgElement.filter(e => e.$type === 'dmn:Decision');
    out[f] = { warnings: r.warnings.length, warningDetails: r.warnings.map(w => w.message), decisions: decisions.map(d => ({ id: d.id, hitPolicy: d.decisionLogic.hitPolicy, inputs: d.decisionLogic.input.length, outputs: d.decisionLogic.output.length, rules: d.decisionLogic.rule.length })) };
    continue;
  }
  const moddle = new BpmnModdle({ zeebe });
  const { rootElement, warnings } = await moddle.fromXML(xml);
  const linter = new Linter({ config: { extends: 'bpmnlint:recommended', rules: { 'standard-size': 'off' } }, resolver: new NodeResolver() });
  const res = await linter.lint(rootElement);
  const issues = Object.entries(res).flatMap(([rule, list]) => list.map(r => ({ rule, id: r.id, message: r.message, category: r.category })));
  const linterAll = new Linter({ config: { extends: 'bpmnlint:recommended' }, resolver: new NodeResolver() });
  const resAll = await linterAll.lint(rootElement);
  const std = (resAll['standard-size'] || []).length;
  out[f] = { warnings: warnings.length, warningDetails: warnings.map(w => w.message), lintIssues: issues, standardSizeNotes: std };
}
console.log(JSON.stringify(out, null, 1));
