import fs from 'fs';
import dmn from '@hbtgmbh/dmn-eval-js';
import loglevel from 'loglevel';

loglevel.getLogger('dmn-eval-js').setLevel('silent');
const [dmnPath, casesPath] = process.argv.slice(2);
const xml = fs.readFileSync(dmnPath, 'utf8')
  .replace('https://www.omg.org/spec/DMN/20191111/MODEL/', 'http://www.omg.org/spec/DMN/20151101/dmn.xsd')
  .replace(/<dmndi:DMNDI>[\s\S]*<\/dmndi:DMNDI>/, '');
const cases = JSON.parse(fs.readFileSync(casesPath, 'utf8'));
const decisions = await dmn.decisionTable.parseDmnXml(xml);
const out = cases.map(c => {
  try {
    return { id: c.id, decision: c.decision, result: dmn.decisionTable.evaluateDecision(c.decision, decisions, c.context) ?? null };
  } catch (e) {
    return { id: c.id, decision: c.decision, error: String(e.message || e) };
  }
});
console.log(JSON.stringify(out));
