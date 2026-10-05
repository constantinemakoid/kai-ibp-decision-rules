from xml.sax.saxutils import escape

OUT = "Лабораторна_4_правила_рішень.dmn"
ANY = "-"

DECISIONS = [
    {
        "id": "D1_Significance",
        "name": "D1 Значущість події",
        "inputs": [
            ("riskLevel", "Рівень R", "string"),
            ("overProfile", "Перевищення профілю, f1 > 0", "boolean"),
            ("noGrant", "Доручення відсутнє, f4 = 1", "boolean"),
            ("dlpExternal", "Зовнішній носій, f6 = 1", "boolean"),
        ],
        "outputs": [
            ("recommendation", "Рекомендація", "string"),
            ("priority", "Пріоритет", "string"),
            ("overrideAllowed", "Зміна дозволена", "boolean"),
        ],
        "rules": [
            ("R1_1", "R1.1 високий рівень", ['"високий"', ANY, ANY, ANY],
             ['"ескалувати"', '"високий"', "false"]),
            ("R1_2", "R1.2 середній рівень і DLP", ['"середній"', ANY, ANY, "true"],
             ['"ескалувати"', '"високий"', "false"]),
            ("R1_3", "R1.3 середній рівень без DLP", ['"середній"', ANY, ANY, "false"],
             ['"ескалувати"', '"середній"', "true"]),
            ("R1_4", "R1.4 низький рівень і DLP", ['"низький"', ANY, ANY, "true"],
             ['"ескалувати"', '"середній"', "false"]),
            ("R1_5", "R1.5 перевищення без доручення", ['"низький"', "true", "true", "false"],
             ['"ескалувати"', '"середній"', "false"]),
            ("R1_6", "R1.6 перевищення з дорученням", ['"низький"', "true", "false", "false"],
             ['"закрити як штатну"', '"низький"', "true"]),
            ("R1_7", "R1.7 у межах профілю", ['"низький"', "false", ANY, "false"],
             ['"закрити як штатну"', '"низький"', "true"]),
        ],
    },
    {
        "id": "D2_Grounds",
        "name": "D2 Підстави доступу",
        "inputs": [
            ("outsideFiles", "Файли поза правами, k", "number"),
            ("hrOrder", "Кадровий наказ", "boolean"),
            ("priorIncidents", "Попередні інциденти, h", "number"),
            ("dlpExternal", "Зовнішній носій, f6 = 1", "boolean"),
        ],
        "outputs": [
            ("grounds", "Підстави", "string"),
            ("aggravating", "Обтяжуючі ознаки", "boolean"),
        ],
        "rules": [
            ("R2_1", "R2.1 усі файли в межах прав", ["0", ANY, ANY, ANY], ['"підстави наявні"', "false"]),
            ("R2_2", "R2.2 є кадровий наказ", ["> 0", "true", ANY, ANY], ['"потрібне уточнення"', "false"]),
            ("R2_3a", "R2.3 повторний інцидент", ["> 0", "false", "> 0", ANY], ['"підстави відсутні"', "true"]),
            ("R2_3b", "R2.3 передача на носій", ["> 0", "false", "0", "true"], ['"підстави відсутні"', "true"]),
            ("R2_4", "R2.4 без обтяжуючих ознак", ["> 0", "false", "0", "false"], ['"підстави відсутні"', "false"]),
        ],
    },
    {
        "id": "D3_Containment",
        "name": "D3 Контроль обмеження доступу",
        "inputs": [
            ("mismatch", "Розбіжність прав", "string"),
            ("attempt < maxAttempts", "Повтор, n < Kmax", "boolean"),
        ],
        "outputs": [
            ("result", "Результат", "string"),
        ],
        "rules": [
            ("R3_1", "R3.1 розбіжності немає", ['"немає"', ANY], ['"відповідає"']),
            ("R3_2", "R3.2 залишкові права, повтор", ['"залишкові права"', "true"], ['"повторити передачу"']),
            ("R3_3", "R3.3 залишкові права, ліміт", ['"залишкові права"', "false"], ['"ескалувати фахівцю"']),
            ("R3_4", "R3.4 надмірне обмеження", ['"надмірне обмеження"', ANY], ['"ескалувати фахівцю"']),
        ],
    },
]


def a(s):
    return escape(s, {'"': "&quot;"})


def build():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<definitions xmlns="https://www.omg.org/spec/DMN/20191111/MODEL/" '
           'xmlns:dmndi="https://www.omg.org/spec/DMN/20191111/DMNDI/" '
           'xmlns:dc="http://www.omg.org/spec/DMN/20180521/DC/" '
           'xmlns:modeler="http://camunda.org/schema/modeler/1.0" '
           'id="Definitions_IBP4" name="Правила прийняття рішень ЛР 4" '
           'namespace="http://camunda.org/schema/1.0/dmn" exporter="ibp4_gen_dmn.py" exporterVersion="1.0" '
           'modeler:executionPlatform="Camunda Cloud" modeler:executionPlatformVersion="8.8.0">']
    for d in DECISIONS:
        out.append(f'  <decision id="{d["id"]}" name="{a(d["name"])}">')
        out.append(f'    <decisionTable id="DT_{d["id"]}" hitPolicy="UNIQUE">')
        for i, (expr, label, tref) in enumerate(d["inputs"], 1):
            out.append(f'      <input id="In_{d["id"]}_{i}" label="{a(label)}">')
            out.append(f'        <inputExpression id="InExpr_{d["id"]}_{i}" typeRef="{tref}">')
            out.append(f'          <text>{escape(expr)}</text>')
            out.append('        </inputExpression>')
            out.append('      </input>')
        for i, (name, label, tref) in enumerate(d["outputs"], 1):
            out.append(f'      <output id="Out_{d["id"]}_{i}" label="{a(label)}" name="{name}" typeRef="{tref}" />')
        for rid, desc, ins, outs in d["rules"]:
            out.append(f'      <rule id="{rid}">')
            out.append(f'        <description>{escape(desc)}</description>')
            for i, t in enumerate(ins, 1):
                out.append(f'        <inputEntry id="{rid}_in{i}">')
                out.append(f'          <text>{escape(t)}</text>')
                out.append('        </inputEntry>')
            for i, t in enumerate(outs, 1):
                out.append(f'        <outputEntry id="{rid}_out{i}">')
                out.append(f'          <text>{escape(t)}</text>')
                out.append('        </outputEntry>')
            out.append('      </rule>')
        out.append('    </decisionTable>')
        out.append('  </decision>')
    out.append('  <dmndi:DMNDI>')
    out.append('    <dmndi:DMNDiagram id="DMNDiagram_IBP4">')
    for i, d in enumerate(DECISIONS):
        out.append(f'      <dmndi:DMNShape id="DMNShape_{d["id"]}" dmnElementRef="{d["id"]}">')
        out.append(f'        <dc:Bounds height="80" width="180" x="{160 + i * 240}" y="100" />')
        out.append('      </dmndi:DMNShape>')
    out.append('    </dmndi:DMNDiagram>')
    out.append('  </dmndi:DMNDI>')
    out.append('</definitions>')
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(OUT, sum(len(d["rules"]) for d in DECISIONS), "rules")
