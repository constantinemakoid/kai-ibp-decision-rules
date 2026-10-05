from xml.sax.saxutils import escape

OUT = "Лабораторна_3_модель_TO-BE.bpmn"

POOL_X = 160
POOL_W = 2860
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


def node(id_, kind, name, proc, lane, x, y, doc, label=None, msg=None, w=None, h=None):
    if w is None:
        w, h = {"task": (150, 80), "event": (36, 36), "gateway": (50, 50)}[kind_group(kind)]
    N.append(dict(id=id_, kind=kind, name=name, proc=proc, lane=lane, x=x, y=y, w=w, h=h,
                  doc=doc, label=label, msg=msg))


def kind_group(kind):
    if kind.endswith("Task"):
        return "task"
    if kind.endswith("Gateway"):
        return "gateway"
    return "event"


def ev(cx, cy):
    return cx - 18, cy - 18


def tk(cx, cy, w=150):
    return cx - w // 2, cy - 40


def gw(cx, cy):
    return cx - 25, cy - 25


node("Start_Audit", "startEvent", "Зафіксовано перегляд і копіювання документів іншого підрозділу",
     "Process_Audit", None, *ev(250, 90),
     "Початкова подія процесу, як у ЛР 2.", label=(195, 112, 110, 60))
node("Task_Register", "serviceTask", "Сформувати запис аудиту та сповіщення", "Process_Audit", None,
     *tk(385, 90), "Крок 1 ЛР 1 без змін.")
node("End_Audit", "endEvent", "Запис і сповіщення сформовано", "Process_Audit", None, *ev(525, 90),
     "Завершення фрагмента системи аудиту.", label=(465, 112, 120, 44))

node("Start_Alert", "startEvent", "Отримано первинне сповіщення", "Process_IB", "Lane_Platform",
     *ev(385, 830), "Зміна П1: сповіщення надходить на платформу, а не черговому SOC.",
     label=(325, 852, 120, 44), msg="Message_Alert")
node("Task_CreateCard", "serviceTask", "Зареєструвати картку інциденту", "Process_IB", "Lane_Platform",
     *tk(515, 830), "Зміна П1: автоматична реєстрація замість Task_Accept.")
node("Task_Enrich", "serviceTask", "Зібрати контекст: DLP, IAM, підрозділ",
     "Process_IB", "Lane_Platform", *tk(705, 830),
     "Зміна П1: автоматичний запит IAM замість Task_RequestRights і Catch_RightsData.")
node("Task_Score", "serviceTask", "Оцінити ризик і рекомендувати пріоритет",
     "Process_IB", "Lane_Platform", *tk(895, 830),
     "Зміна П2: інтелектуальна підтримка точки рішення 1.")
node("Task_Review", "userTask", "Перевірити оцінку ризику та підтвердити значущість", "Process_IB",
     "Lane_SOC", *tk(895, 450), "Зміна П2: черговий SOC приймає рішення на основі оцінки.")
node("Gateway_Activity", "exclusiveGateway", "Перевищує звичайну активність?", "Process_IB", "Lane_SOC",
     *gw(1035, 450), "Точка рішення 1 ЛР 1: умови гілок взаємовиключні.", label=(975, 482, 120, 34))
node("Task_DocRoutine", "userTask", "Закрити картку як штатну подію", "Process_IB", "Lane_SOC",
     *tk(1035, 335), "Гілка «Ні» точки рішення 1, без повторного введення даних.")
node("End_Routine", "endEvent", "Подію закрито як штатну", "Process_IB", "Lane_SOC", *ev(1175, 335),
     "Кінцевий результат: подія штатна.", label=(1120, 357, 110, 34))
node("Task_Evidence", "serviceTask", "Сформувати пакет доказів і призначити фахівцю з ІБ", "Process_IB",
     "Lane_Platform", *tk(1175, 830), "Зміна П3: автоматична ескалація і пакет доказів.")
node("Task_CheckGrounds", "userTask", "Перевірити пакет доказів і підстави доступу", "Process_IB",
     "Lane_IB", *tk(1365, 680), "Зміна П3: аналіз і перевірка повноважень за зведеними даними.")
node("Gateway_Grounds", "exclusiveGateway", "Відсутність правомірних підстав підтверджено?",
     "Process_IB", "Lane_IB", *gw(1505, 680), "Точка рішення 2 ЛР 1.", label=(1425, 722, 160, 28))
node("Task_CloseUnconf", "userTask", "Закрити подію як непідтверджену", "Process_IB", "Lane_IB",
     *tk(1505, 575), "Гілка «Ні» точки рішення 2.")
node("End_NotConfirmed", "endEvent", "Інцидент не підтверджено", "Process_IB", "Lane_IB",
     *ev(1645, 575), "Кінцевий результат: інцидент не підтверджено.", label=(1590, 597, 110, 34))
node("Task_Classify", "userTask", "Підтвердити критичність і захід обмеження", "Process_IB", "Lane_IB",
     *tk(1655, 680), "Крок 5 ЛР 1 і рішення про захід (зміна П4).")
node("Throw_HeadNotice", "intermediateThrowEvent", "Повідомлення керівнику надіслано", "Process_IB",
     "Lane_Platform", *ev(1800, 830),
     "Зміна П4: платформа надсилає повідомлення керівнику після затвердження класифікації, без очікування.",
     label=(1750, 772, 100, 40), msg="Message_HeadNotice")
node("Gateway_Merge", "exclusiveGateway", "", "Process_IB", "Lane_Platform", *gw(1880, 830),
     "Об'єднання основного потоку і повторної передачі рішення.")
node("Task_SendDecision", "serviceTask", "Передати IAM рішення про обмеження доступу", "Process_IB",
     "Lane_Platform", *tk(2015, 830), "Зміна П5: автоматична передача рішення.")
node("Catch_RestrictDone", "intermediateCatchEvent", "Обмеження доступу підтверджено", "Process_IB",
     "Lane_Platform", *ev(2160, 830), "Очікування підтвердження від IAM.",
     label=(2092, 856, 64, 44), msg="Message_Done")
node("Task_VerifyRights", "serviceTask", "Звірити фактичний стан прав із рішенням", "Process_IB",
     "Lane_Platform", *tk(2295, 830), "Зміна П5: контроль результату обмеження.")
node("Gateway_RightsOk", "exclusiveGateway", "Стан прав відповідає рішенню?", "Process_IB",
     "Lane_Platform", *gw(2430, 830), "Автоматична точка рішення.", label=(2370, 862, 120, 34))
node("Catch_HeadDecision", "intermediateCatchEvent", "Отримано рішення керівника", "Process_IB",
     "Lane_Platform", *ev(2510, 830), "Зміна П4: платформа очікує рішення керівника для звіту.",
     label=(2472, 772, 76, 34), msg="Message_HeadDecision")
node("Task_DraftReport", "serviceTask", "Сформувати чернетку звіту з картки інциденту", "Process_IB",
     "Lane_Platform", *tk(2640, 830), "Зміна П5: автоматичне формування чернетки звіту.")
node("Task_ApproveReport", "userTask", "Перевірити та затвердити звіт", "Process_IB", "Lane_IB",
     *tk(2800, 680), "Крок 7 ЛР 1: звіт затверджує фахівець з ІБ.")
node("End_Report", "endEvent", "Інцидент закрито зі звітом", "Process_IB", "Lane_IB", *ev(2940, 680),
     "Кінцевий результат: звіт і обмеження доступу.", label=(2885, 702, 110, 34))

node("Start_IAM_Rights", "startEvent", "Отримано запит повноважень", "Process_IAM", None, *ev(670, 1195),
     "Початок обробки запиту повноважень.", label=(548, 1175, 118, 40), msg="Message_RightsReq")
node("Task_ProvideRights", "serviceTask", "Надати дані про фактичні повноваження", "Process_IAM", None,
     *tk(805, 1195), "Крок 4 ЛР 1 без змін.")
node("End_IAM_Rights", "endEvent", "Дані надано", "Process_IAM", None, *ev(940, 1195),
     "Завершення обробки запиту.", label=(895, 1217, 90, 20))
node("Start_IAM_Restrict", "startEvent", "Отримано рішення про обмеження", "Process_IAM", None,
     *ev(1980, 1195), "Початок виконання обмеження.", label=(1840, 1175, 118, 40), msg="Message_Decision")
node("Task_Restrict", "serviceTask", "Обмежити повноваження або заблокувати обліковий запис",
     "Process_IAM", None, *tk(2115, 1195), "Крок 6 ЛР 1 без змін.")
node("End_IAM_Restrict", "endEvent", "Обмеження виконано", "Process_IAM", None, *ev(2250, 1195),
     "Завершення виконання обмеження.", label=(2200, 1217, 110, 20))

node("Start_Head", "startEvent", "Отримано повідомлення про інцидент", "Process_Head", "Lane_Head",
     *ev(1800, 1425), "Початок участі керівника.", label=(1750, 1447, 100, 44), msg="Message_HeadNotice")
node("Task_ApproveOrg", "userTask", "Погодити організаційні заходи щодо співробітника", "Process_Head",
     "Lane_Head", *tk(1945, 1425, 190), "Крок 6 ЛР 1 без змін.", w=190, h=80)
node("End_Head", "endEvent", "Рішення керівника передано", "Process_Head", "Lane_Head", *ev(2510, 1425),
     "Зміна П4: рішення керівника повертається до служби ІБ.", label=(2455, 1447, 110, 34),
     msg="Message_HeadDecision")

F = []


def flow(id_, src, dst, pts, name=None, cond=None, label=None):
    F.append(dict(id=id_, src=src, dst=dst, pts=pts, name=name, cond=cond, label=label))


flow("Flow_A1", "Start_Audit", "Task_Register", [(268, 90), (310, 90)])
flow("Flow_A2", "Task_Register", "End_Audit", [(460, 90), (507, 90)])
flow("Flow_P1", "Start_Alert", "Task_CreateCard", [(403, 830), (440, 830)])
flow("Flow_P2", "Task_CreateCard", "Task_Enrich", [(590, 830), (630, 830)])
flow("Flow_P3", "Task_Enrich", "Task_Score", [(780, 830), (820, 830)])
flow("Flow_P4", "Task_Score", "Task_Review", [(895, 790), (895, 490)])
flow("Flow_S1", "Task_Review", "Gateway_Activity", [(970, 450), (1010, 450)])
flow("Flow_S2_yes", "Gateway_Activity", "Task_Evidence", [(1060, 450), (1135, 450), (1135, 790)],
     name="Так", cond="Значущість підтверджено: рівень R високий; або рівень середній і пояснення не "
     "встановлено; або рівень низький, але обсяг перевищує профіль без доручення в IAM (f1 > 0, f4 = 1); "
     "або низький рівень спростовано черговим",
     label=(1070, 430, 30, 14))
flow("Flow_S2_no", "Gateway_Activity", "Task_DocRoutine", [(1035, 425), (1035, 375)],
     name="Ні", cond="Штатний характер підтверджено: рівень R низький, перевищення профілю без доручення в "
     "IAM відсутнє (f1 = 0 або f4 = 0) і низький рівень не спростовано черговим; або рівень середній і "
     "черговий встановив пояснення",
     label=(1042, 392, 30, 14))
flow("Flow_S3", "Task_DocRoutine", "End_Routine", [(1110, 335), (1157, 335)])
flow("Flow_P5", "Task_Evidence", "Task_CheckGrounds", [(1250, 830), (1365, 830), (1365, 720)])
flow("Flow_I1", "Task_CheckGrounds", "Gateway_Grounds", [(1440, 680), (1480, 680)])
flow("Flow_I2_yes", "Gateway_Grounds", "Task_Classify", [(1530, 680), (1580, 680)],
     name="Так", cond="Відсутність правомірних підстав доступу підтверджено", label=(1536, 662, 30, 14))
flow("Flow_I2_no", "Gateway_Grounds", "Task_CloseUnconf", [(1505, 655), (1505, 615)],
     name="Ні", cond="Правомірні підстави доступу виявлено", label=(1512, 628, 30, 14))
flow("Flow_I3", "Task_CloseUnconf", "End_NotConfirmed", [(1580, 575), (1627, 575)])
flow("Flow_I4", "Task_Classify", "Throw_HeadNotice", [(1655, 720), (1655, 830), (1782, 830)])
flow("Flow_I5", "Throw_HeadNotice", "Gateway_Merge", [(1818, 830), (1855, 830)])
flow("Flow_P6", "Gateway_Merge", "Task_SendDecision", [(1905, 830), (1940, 830)])
flow("Flow_P7", "Task_SendDecision", "Catch_RestrictDone", [(2090, 830), (2142, 830)])
flow("Flow_P8", "Catch_RestrictDone", "Task_VerifyRights", [(2178, 830), (2220, 830)])
flow("Flow_P9", "Task_VerifyRights", "Gateway_RightsOk", [(2370, 830), (2405, 830)])
flow("Flow_P10_no", "Gateway_RightsOk", "Gateway_Merge", [(2430, 805), (2430, 775), (1880, 775), (1880, 805)],
     name="Ні", cond="Фактичний стан прав не відповідає рішенню", label=(2437, 782, 30, 14))
flow("Flow_P10_yes", "Gateway_RightsOk", "Catch_HeadDecision",
     [(2455, 830), (2492, 830)],
     name="Так", cond="Фактичний стан прав відповідає рішенню", label=(2457, 812, 21, 14))
flow("Flow_I6", "Catch_HeadDecision", "Task_DraftReport", [(2528, 830), (2565, 830)])
flow("Flow_P11", "Task_DraftReport", "Task_ApproveReport", [(2715, 830), (2800, 830), (2800, 720)])
flow("Flow_I7", "Task_ApproveReport", "End_Report", [(2875, 680), (2922, 680)])
flow("Flow_M1", "Start_IAM_Rights", "Task_ProvideRights", [(688, 1195), (730, 1195)])
flow("Flow_M2", "Task_ProvideRights", "End_IAM_Rights", [(880, 1195), (922, 1195)])
flow("Flow_M3", "Start_IAM_Restrict", "Task_Restrict", [(1998, 1195), (2040, 1195)])
flow("Flow_M4", "Task_Restrict", "End_IAM_Restrict", [(2190, 1195), (2232, 1195)])
flow("Flow_H1", "Start_Head", "Task_ApproveOrg", [(1818, 1425), (1850, 1425)])
flow("Flow_H2", "Task_ApproveOrg", "End_Head", [(2040, 1425), (2492, 1425)])

M = [
    ("MsgFlow_Alert", "Первинне сповіщення", "Task_Register", "Start_Alert", [(385, 130), (385, 812)],
     (392, 222, 130, 34)),
    ("MsgFlow_RightsReq", "Запит фактичних повноважень", "Task_Enrich", "Start_IAM_Rights",
     [(670, 870), (670, 1177)], (560, 1040, 105, 48)),
    ("MsgFlow_RightsData", "Дані про фактичні повноваження", "Task_ProvideRights", "Task_Enrich",
     [(760, 1155), (760, 870)], (767, 1040, 120, 48)),
    ("MsgFlow_HeadNotice", "Повідомлення про підтверджений інцидент", "Throw_HeadNotice", "Start_Head",
     [(1800, 848), (1800, 1407)], (1807, 1040, 130, 48)),
    ("MsgFlow_Decision", "Рішення про обмеження доступу", "Task_SendDecision", "Start_IAM_Restrict",
     [(1980, 870), (1980, 1177)], (1987, 1040, 105, 48)),
    ("MsgFlow_Done", "Підтвердження обмеження доступу", "Task_Restrict", "Catch_RestrictDone",
     [(2160, 1155), (2160, 848)], (2167, 1040, 120, 48)),
    ("MsgFlow_HeadDecision", "Рішення щодо організаційних заходів", "End_Head", "Catch_HeadDecision",
     [(2510, 1407), (2510, 848)], (2517, 1040, 130, 48)),
]


def a(s):
    return escape(s, {'"': "&quot;"})


def build():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
           'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
           'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
           'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_IBP3" '
           'targetNamespace="http://bpmn.io/schema/bpmn" exporter="ibp3_gen_tobe.py" exporterVersion="1.0">']
    for mid, mname in MESSAGES:
        out.append(f'  <bpmn:message id="{mid}" name="{a(mname)}" />')
    out.append('  <bpmn:collaboration id="Collaboration_IncidentResponse_TOBE">')
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
                out.append(f'      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">{escape(f["cond"])}</bpmn:conditionExpression>')
                out.append('    </bpmn:sequenceFlow>')
            else:
                out.append(f'    <bpmn:sequenceFlow id="{f["id"]}"{nm} sourceRef="{f["src"]}" targetRef="{f["dst"]}" />')
        out.append('  </bpmn:process>')
    out.append('  <bpmndi:BPMNDiagram id="BPMNDiagram_1">')
    out.append('    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collaboration_IncidentResponse_TOBE">')

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
