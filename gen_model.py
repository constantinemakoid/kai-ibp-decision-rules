from xml.sax.saxutils import escape

OUT = "Лабораторна_4_модель_з_правилами.bpmn"

POOL_X = 160
POOL_W = 3380
LANE_X = 190
LANE_W = POOL_W - 30

MESSAGES = [
    ("Message_Alert", "Первинне сповіщення"),
    ("Message_RightsReq", "Запит фактичних повноважень"),
    ("Message_HeadNotice", "Повідомлення про підтверджений інцидент"),
    ("Message_Decision", "Рішення про обмеження доступу"),
    ("Message_Done", "Підтвердження обмеження доступу"),
    ("Message_HeadDecision", "Рішення щодо організаційних заходів"),
]

POOLS = [
    ("Participant_Audit", "Система аудиту документообігу", "Process_Audit", 30, 170),
    ("Participant_IB", "Служба ІБ", "Process_IB", 280, 760),
    ("Participant_IAM", "Система IAM", "Process_IAM", 1120, 150),
    ("Participant_Head", "Підрозділ користувача", "Process_Head", 1350, 150),
]

LANES = {
    "Process_IB": [
        ("Lane_SOC", "Черговий SOC", 280, 240),
        ("Lane_IB", "Фахівець з ІБ", 520, 240),
        ("Lane_Platform", "Платформа обробки інцидентів", 760, 280),
    ],
    "Process_Head": [
        ("Lane_Head", "Керівник підрозділу", 1350, 150),
    ],
}

N = []


def size(kind):
    if kind.endswith("Task"):
        return 150, 80
    if kind.endswith("Gateway"):
        return 50, 50
    return 36, 36


def node(id_, kind, name, proc, lane, cx, cy, doc, label=None, msg=None, w=None, decision=None):
    ww, hh = size(kind)
    w = w or ww
    N.append(dict(id=id_, kind=kind, name=name, proc=proc, lane=lane, x=cx - w // 2, y=cy - hh // 2, w=w, h=hh,
                  doc=doc, label=label, msg=msg, decision=decision))


IB, PL, SOC = "Lane_IB", "Lane_Platform", "Lane_SOC"
P = "Process_IB"

node("Start_Audit", "startEvent", "Зафіксовано перегляд і копіювання документів іншого підрозділу",
     "Process_Audit", None, 250, 90, "Початкова подія процесу.", label=(195, 112, 110, 60))
node("Task_Register", "serviceTask", "Сформувати запис аудиту та сповіщення", "Process_Audit", None, 385, 90,
     "Без змін відносно ЛР 3.")
node("End_Audit", "endEvent", "Запис і сповіщення сформовано", "Process_Audit", None, 525, 90,
     "Завершення фрагмента системи аудиту.", label=(465, 112, 120, 44))

node("Start_Alert", "startEvent", "Отримано первинне сповіщення", P, PL, 385, 830,
     "Сповіщення надходить на платформу.", label=(325, 852, 120, 44), msg="Message_Alert")
node("Task_CreateCard", "serviceTask", "Зареєструвати картку інциденту", P, PL, 515, 830,
     "Без змін відносно ЛР 3.")
node("Task_Enrich", "serviceTask", "Зібрати контекст: DLP, IAM, підрозділ", P, PL, 705, 830,
     "Отримання даних для D1 і D2: журнал аудиту, DLP, права і доручення IAM, кадрові дані.")
node("Task_Score", "serviceTask", "Оцінити ризик R і визначити рівень", P, PL, 895, 830,
     "Обчислення R і ознак f1...f6; рівень за порогами Rсер і Rвис.")
node("Rule_D1", "businessRuleTask", "Застосувати правила D1: значущість події", P, PL, 1085, 830,
     "Таблиця рішень D1_Significance, правила R1.1...R1.7.", decision=("D1_Significance", "d1"))
node("Task_Review", "userTask", "Підтвердити рекомендацію D1 або змінити з обґрунтуванням", P, SOC, 1085, 450,
     "Рівень B: зміна рекомендації можлива лише при d1.overrideAllowed = true; результат d1Final.")
node("Gateway_Activity", "exclusiveGateway", "Рішення D1: ескалувати?", P, SOC, 1225, 450,
     "Точка рішення D1.", label=(1165, 482, 120, 34))
node("Task_DocRoutine", "userTask", "Закрити картку як штатну подію", P, SOC, 1225, 335,
     "Гілка «Ні» точки рішення D1.")
node("End_Routine", "endEvent", "Подію закрито як штатну", P, SOC, 1365, 335,
     "Кінцевий результат: подія штатна.", label=(1310, 357, 110, 34))
node("Task_Evidence", "serviceTask", "Сформувати пакет доказів і призначити фахівцю з ІБ", P, PL, 1365, 830,
     "Обчислення k, h для D2.")
node("Rule_D2", "businessRuleTask", "Застосувати правила D2: підстави доступу", P, PL, 1555, 830,
     "Таблиця рішень D2_Grounds, правила R2.1...R2.4.", decision=("D2_Grounds", "d2"))
node("Task_CheckGrounds", "userTask", "Перевірити пакет доказів і рекомендацію D2", P, IB, 1555, 680,
     "Рівень B: фахівець з ІБ підтверджує або змінює рекомендацію; результат d2Final.")
node("Gateway_Grounds", "exclusiveGateway", "Рішення D2: підстави відсутні?", P, IB, 1695, 680,
     "Точка рішення D2.", label=(1615, 722, 160, 28))
node("Task_CloseUnconf", "userTask", "Закрити подію як непідтверджену", P, IB, 1695, 575,
     "Гілка «Ні» точки рішення D2.")
node("End_NotConfirmed", "endEvent", "Інцидент не підтверджено", P, IB, 1835, 575,
     "Кінцевий результат: інцидент не підтверджено.", label=(1780, 597, 110, 34))
node("Task_Classify", "userTask", "Підтвердити критичність і захід обмеження", P, IB, 1845, 680,
     "Без змін відносно ЛР 3.")
node("Throw_HeadNotice", "intermediateThrowEvent", "Повідомлення керівнику надіслано", P, PL, 1990, 830,
     "Без змін відносно ЛР 3.", label=(1940, 772, 100, 40), msg="Message_HeadNotice")
node("Gateway_Merge", "exclusiveGateway", "", P, PL, 2070, 830, "Об'єднання основного потоку і повтору R3.2.")
node("Task_SendDecision", "serviceTask", "Передати IAM рішення про обмеження доступу", P, PL, 2205, 830,
     "Лічильник передач attempt збільшується на 1.")
node("Catch_RestrictDone", "intermediateCatchEvent", "Обмеження доступу підтверджено", P, PL, 2350, 830,
     "Очікування підтвердження від IAM.", label=(2282, 856, 64, 44), msg="Message_Done")
node("Task_VerifyRights", "serviceTask", "Визначити розбіжність прав із рішенням", P, PL, 2485, 830,
     "Отримання даних для D3: mismatch.")
node("Rule_D3", "businessRuleTask", "Застосувати правила D3: контроль прав", P, PL, 2665, 830,
     "Таблиця рішень D3_Containment, правила R3.1...R3.4, рівень C.", decision=("D3_Containment", "d3"))
node("Gateway_RightsOk", "exclusiveGateway", "Результат D3", P, PL, 2810, 830,
     "Точка рішення D3, автоматична.", label=(2830, 870, 90, 20))
node("Task_FixRights", "userTask", "Усунути розбіжність прав і підтвердити стан", P, IB, 2940, 680,
     "Правила R3.3 і R3.4: рішення передано фахівцю з ІБ.")
node("Gateway_MergeOk", "exclusiveGateway", "", P, PL, 3090, 960, "Об'єднання гілок R3.1 і ручного усунення.")
node("Catch_HeadDecision", "intermediateCatchEvent", "Отримано рішення керівника", P, PL, 3180, 960,
     "Без змін відносно ЛР 3.", label=(3142, 905, 76, 34), msg="Message_HeadDecision")
node("Task_DraftReport", "serviceTask", "Сформувати чернетку звіту з картки інциденту", P, PL, 3310, 960,
     "До звіту включаються результати D1, D2, D3 і номери правил, що спрацювали.")
node("Task_ApproveReport", "userTask", "Перевірити та затвердити звіт", P, IB, 3310, 680,
     "Без змін відносно ЛР 3.")
node("End_Report", "endEvent", "Інцидент закрито зі звітом", P, IB, 3450, 680,
     "Кінцевий результат: звіт і обмеження доступу.", label=(3395, 702, 110, 34))

node("Start_IAM_Rights", "startEvent", "Отримано запит повноважень", "Process_IAM", None, 670, 1195,
     "Початок обробки запиту повноважень.", label=(548, 1175, 118, 40), msg="Message_RightsReq")
node("Task_ProvideRights", "serviceTask", "Надати дані про фактичні повноваження", "Process_IAM", None, 805, 1195,
     "Без змін.")
node("End_IAM_Rights", "endEvent", "Дані надано", "Process_IAM", None, 940, 1195,
     "Завершення обробки запиту.", label=(895, 1217, 90, 20))
node("Start_IAM_Restrict", "startEvent", "Отримано рішення про обмеження", "Process_IAM", None, 2170, 1195,
     "Початок виконання обмеження.", label=(2030, 1175, 118, 40), msg="Message_Decision")
node("Task_Restrict", "serviceTask", "Обмежити повноваження або заблокувати обліковий запис", "Process_IAM", None,
     2305, 1195, "Без змін.")
node("End_IAM_Restrict", "endEvent", "Обмеження виконано", "Process_IAM", None, 2440, 1195,
     "Завершення виконання обмеження.", label=(2390, 1217, 110, 20))

node("Start_Head", "startEvent", "Отримано повідомлення про інцидент", "Process_Head", "Lane_Head", 1990, 1425,
     "Початок участі керівника.", label=(1940, 1447, 100, 44), msg="Message_HeadNotice")
node("Task_ApproveOrg", "userTask", "Погодити організаційні заходи щодо співробітника", "Process_Head", "Lane_Head",
     2135, 1425, "Без змін.", w=190)
node("End_Head", "endEvent", "Рішення керівника передано", "Process_Head", "Lane_Head", 3180, 1425,
     "Рішення керівника повертається до служби ІБ.", label=(3125, 1447, 110, 34), msg="Message_HeadDecision")

F = []


def flow(id_, src, dst, pts, name=None, cond=None, label=None):
    F.append(dict(id=id_, src=src, dst=dst, pts=pts, name=name, cond=cond, label=label))


flow("Flow_A1", "Start_Audit", "Task_Register", [(268, 90), (310, 90)])
flow("Flow_A2", "Task_Register", "End_Audit", [(460, 90), (507, 90)])
flow("Flow_P1", "Start_Alert", "Task_CreateCard", [(403, 830), (440, 830)])
flow("Flow_P2", "Task_CreateCard", "Task_Enrich", [(590, 830), (630, 830)])
flow("Flow_P3", "Task_Enrich", "Task_Score", [(780, 830), (820, 830)])
flow("Flow_P4", "Task_Score", "Rule_D1", [(970, 830), (1010, 830)])
flow("Flow_P4b", "Rule_D1", "Task_Review", [(1085, 790), (1085, 490)])
flow("Flow_S1", "Task_Review", "Gateway_Activity", [(1160, 450), (1200, 450)])
flow("Flow_S2_yes", "Gateway_Activity", "Task_Evidence", [(1250, 450), (1325, 450), (1325, 790)],
     name="Так", cond='= d1Final = "ескалувати"', label=(1260, 430, 30, 14))
flow("Flow_S2_no", "Gateway_Activity", "Task_DocRoutine", [(1225, 425), (1225, 375)],
     name="Ні", cond='= d1Final = "закрити як штатну"', label=(1232, 392, 30, 14))
flow("Flow_S3", "Task_DocRoutine", "End_Routine", [(1300, 335), (1347, 335)])
flow("Flow_P5", "Task_Evidence", "Rule_D2", [(1440, 830), (1480, 830)])
flow("Flow_P5b", "Rule_D2", "Task_CheckGrounds", [(1555, 790), (1555, 720)])
flow("Flow_I1", "Task_CheckGrounds", "Gateway_Grounds", [(1630, 680), (1670, 680)])
flow("Flow_I2_yes", "Gateway_Grounds", "Task_Classify", [(1720, 680), (1770, 680)],
     name="Так", cond='= d2Final = "підстави відсутні"', label=(1726, 662, 30, 14))
flow("Flow_I2_no", "Gateway_Grounds", "Task_CloseUnconf", [(1695, 655), (1695, 615)],
     name="Ні", cond='= d2Final = "підстави наявні"', label=(1702, 628, 30, 14))
flow("Flow_I3", "Task_CloseUnconf", "End_NotConfirmed", [(1770, 575), (1817, 575)])
flow("Flow_I4", "Task_Classify", "Throw_HeadNotice", [(1845, 720), (1845, 830), (1972, 830)])
flow("Flow_I5", "Throw_HeadNotice", "Gateway_Merge", [(2008, 830), (2045, 830)])
flow("Flow_P6", "Gateway_Merge", "Task_SendDecision", [(2095, 830), (2130, 830)])
flow("Flow_P7", "Task_SendDecision", "Catch_RestrictDone", [(2280, 830), (2332, 830)])
flow("Flow_P8", "Catch_RestrictDone", "Task_VerifyRights", [(2368, 830), (2410, 830)])
flow("Flow_P9", "Task_VerifyRights", "Rule_D3", [(2560, 830), (2590, 830)])
flow("Flow_P9b", "Rule_D3", "Gateway_RightsOk", [(2740, 830), (2785, 830)])
flow("Flow_P10_retry", "Gateway_RightsOk", "Gateway_Merge", [(2810, 805), (2810, 775), (2070, 775), (2070, 805)],
     name="Повторити", cond='= d3.result = "повторити передачу"', label=(2744, 779, 62, 14))
flow("Flow_P10_esc", "Gateway_RightsOk", "Task_FixRights", [(2835, 830), (2940, 830), (2940, 720)],
     name="Ескалувати", cond='= d3.result = "ескалувати фахівцю"', label=(2845, 812, 70, 14))
flow("Flow_P10_ok", "Gateway_RightsOk", "Gateway_MergeOk", [(2810, 855), (2810, 960), (3065, 960)],
     name="Відповідає", cond='= d3.result = "відповідає"', label=(2900, 940, 70, 14))
flow("Flow_F1", "Task_FixRights", "Gateway_MergeOk", [(3015, 680), (3090, 680), (3090, 935)])
flow("Flow_I6a", "Gateway_MergeOk", "Catch_HeadDecision", [(3115, 960), (3162, 960)])
flow("Flow_I6", "Catch_HeadDecision", "Task_DraftReport", [(3198, 960), (3235, 960)])
flow("Flow_P11", "Task_DraftReport", "Task_ApproveReport", [(3310, 920), (3310, 720)])
flow("Flow_I7", "Task_ApproveReport", "End_Report", [(3385, 680), (3432, 680)])
flow("Flow_M1", "Start_IAM_Rights", "Task_ProvideRights", [(688, 1195), (730, 1195)])
flow("Flow_M2", "Task_ProvideRights", "End_IAM_Rights", [(880, 1195), (922, 1195)])
flow("Flow_M3", "Start_IAM_Restrict", "Task_Restrict", [(2188, 1195), (2230, 1195)])
flow("Flow_M4", "Task_Restrict", "End_IAM_Restrict", [(2380, 1195), (2422, 1195)])
flow("Flow_H1", "Start_Head", "Task_ApproveOrg", [(2008, 1425), (2040, 1425)])
flow("Flow_H2", "Task_ApproveOrg", "End_Head", [(2230, 1425), (3162, 1425)])

M = [
    ("MsgFlow_Alert", "Первинне сповіщення", "Task_Register", "Start_Alert", [(385, 130), (385, 812)],
     (392, 222, 130, 34)),
    ("MsgFlow_RightsReq", "Запит фактичних повноважень", "Task_Enrich", "Start_IAM_Rights",
     [(670, 870), (670, 1177)], (560, 1040, 105, 48)),
    ("MsgFlow_RightsData", "Дані про фактичні повноваження", "Task_ProvideRights", "Task_Enrich",
     [(760, 1155), (760, 870)], (767, 1040, 120, 48)),
    ("MsgFlow_HeadNotice", "Повідомлення про підтверджений інцидент", "Throw_HeadNotice", "Start_Head",
     [(1990, 848), (1990, 1407)], (1997, 1040, 130, 48)),
    ("MsgFlow_Decision", "Рішення про обмеження доступу", "Task_SendDecision", "Start_IAM_Restrict",
     [(2170, 870), (2170, 1177)], (2177, 1040, 105, 48)),
    ("MsgFlow_Done", "Підтвердження обмеження доступу", "Task_Restrict", "Catch_RestrictDone",
     [(2350, 1155), (2350, 848)], (2357, 1040, 120, 48)),
    ("MsgFlow_HeadDecision", "Рішення щодо організаційних заходів", "End_Head", "Catch_HeadDecision",
     [(3180, 1407), (3180, 978)], (3187, 1040, 130, 48)),
]


def a(s):
    return escape(s, {'"': "&quot;"})


def build():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
           'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
           'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
           'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
           'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
           'xmlns:modeler="http://camunda.org/schema/modeler/1.0" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_IBP4" '
           'targetNamespace="http://bpmn.io/schema/bpmn" exporter="ibp4_gen_model.py" exporterVersion="1.0" '
           'modeler:executionPlatform="Camunda Cloud" modeler:executionPlatformVersion="8.8.0">']
    for mid, mname in MESSAGES:
        out.append(f'  <bpmn:message id="{mid}" name="{a(mname)}" />')
    out.append('  <bpmn:collaboration id="Collaboration_IncidentResponse_Rules">')
    for pid, pname, proc, _, _ in POOLS:
        out.append(f'    <bpmn:participant id="{pid}" name="{a(pname)}" processRef="{proc}" />')
    for mid, mname, src, dst, _, _ in M:
        out.append(f'    <bpmn:messageFlow id="{mid}" name="{a(mname)}" sourceRef="{src}" targetRef="{dst}" />')
    out.append('  </bpmn:collaboration>')
    for _, _, proc, _, _ in POOLS:
        out.append(f'  <bpmn:process id="{proc}" isExecutable="false">')
        if proc in LANES:
            out.append(f'    <bpmn:laneSet id="LaneSet_{proc}">')
            for lid, lname, _, _ in LANES[proc]:
                out.append(f'      <bpmn:lane id="{lid}" name="{a(lname)}">')
                for n in N:
                    if n["lane"] == lid:
                        out.append(f'        <bpmn:flowNodeRef>{n["id"]}</bpmn:flowNodeRef>')
                out.append('      </bpmn:lane>')
            out.append('    </bpmn:laneSet>')
        for n in N:
            if n["proc"] != proc:
                continue
            nm = f' name="{a(n["name"])}"' if n["name"] else ""
            out.append(f'    <bpmn:{n["kind"]} id="{n["id"]}"{nm}>')
            out.append(f'      <bpmn:documentation>{escape(n["doc"])}</bpmn:documentation>')
            if n["decision"]:
                did, var = n["decision"]
                out.append('      <bpmn:extensionElements>')
                out.append(f'        <zeebe:calledDecision decisionId="{did}" resultVariable="{var}" />')
                out.append('      </bpmn:extensionElements>')
            for f in F:
                if f["dst"] == n["id"]:
                    out.append(f'      <bpmn:incoming>{f["id"]}</bpmn:incoming>')
            for f in F:
                if f["src"] == n["id"]:
                    out.append(f'      <bpmn:outgoing>{f["id"]}</bpmn:outgoing>')
            if n["msg"]:
                out.append(f'      <bpmn:messageEventDefinition id="{n["id"]}_def" messageRef="{n["msg"]}" />')
            out.append(f'    </bpmn:{n["kind"]}>')
        ids = {n["id"] for n in N if n["proc"] == proc}
        for f in F:
            if f["src"] not in ids:
                continue
            nm = f' name="{a(f["name"])}"' if f["name"] else ""
            if f["cond"]:
                out.append(f'    <bpmn:sequenceFlow id="{f["id"]}"{nm} sourceRef="{f["src"]}" targetRef="{f["dst"]}">')
                out.append('      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">'
                           f'{escape(f["cond"])}</bpmn:conditionExpression>')
                out.append('    </bpmn:sequenceFlow>')
            else:
                out.append(f'    <bpmn:sequenceFlow id="{f["id"]}"{nm} sourceRef="{f["src"]}" targetRef="{f["dst"]}" />')
        out.append('  </bpmn:process>')
    out.append('  <bpmndi:BPMNDiagram id="BPMNDiagram_1">')
    out.append('    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collaboration_IncidentResponse_Rules">')

    def shape(eid, x, y, w, h, extra="", label=None):
        out.append(f'      <bpmndi:BPMNShape id="{eid}_di" bpmnElement="{eid}"{extra}>')
        out.append(f'        <dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}" />')
        if label:
            lx, ly, lw, lh = label
            out.append('        <bpmndi:BPMNLabel>')
            out.append(f'          <dc:Bounds x="{lx}" y="{ly}" width="{lw}" height="{lh}" />')
            out.append('        </bpmndi:BPMNLabel>')
        out.append('      </bpmndi:BPMNShape>')

    for pid, _, proc, y, h in POOLS:
        shape(pid, POOL_X, y, POOL_W, h, ' isHorizontal="true"')
    for proc, lanes in LANES.items():
        for lid, _, y, h in lanes:
            shape(lid, LANE_X, y, LANE_W, h, ' isHorizontal="true"')
    for n in N:
        extra = ' isMarkerVisible="true"' if n["kind"] == "exclusiveGateway" else ""
        shape(n["id"], n["x"], n["y"], n["w"], n["h"], extra, n["label"])

    def edge(eid, pts, label=None):
        out.append(f'      <bpmndi:BPMNEdge id="{eid}_di" bpmnElement="{eid}">')
        for x, y in pts:
            out.append(f'        <di:waypoint x="{x}" y="{y}" />')
        if label:
            lx, ly, lw, lh = label
            out.append('        <bpmndi:BPMNLabel>')
            out.append(f'          <dc:Bounds x="{lx}" y="{ly}" width="{lw}" height="{lh}" />')
            out.append('        </bpmndi:BPMNLabel>')
        out.append('      </bpmndi:BPMNEdge>')

    for f in F:
        edge(f["id"], f["pts"], f["label"])
    for mid, _, _, _, pts, lab in M:
        edge(mid, pts, lab)
    out.append('    </bpmndi:BPMNPlane>')
    out.append('  </bpmndi:BPMNDiagram>')
    out.append('</bpmn:definitions>')
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(OUT, len(N), "nodes", len(F), "sequence flows", len(M), "message flows")
