# ЛР 4: правила прийняття рішень у процесі реагування на інцидент

Матеріали лабораторної роботи № 4 з дисципліни «Інтелектуальні бізнес-процеси в системах захисту інформації», варіант 14.

## Вміст

* Лабораторна_4_правила_рішень.dmn: таблиці рішень D1_Significance, D2_Grounds, D3_Containment (DMN 1.3, Camunda 8)
* Лабораторна_4_модель_з_правилами.bpmn: модель BPMN з Business Rule Task і умовами FEEL
* Лабораторна_4_діаграма_з_правилами.png, fig_model_part1.png, fig_model_part2.png: рендер моделі bpmn-js
* fig_dmn_*.png: рендер таблиць рішень dmn-js
* fig_coverage.png: покриття комбінацій умов правилами
* rules.py: еталонна реалізація правил
* dmn_eval.py: інтерпретатор таблиць DMN на Python
* eval_dmn.mjs: виконання таблиць рушієм dmn-eval-js
* scenarios.py: тестові сценарії і перебір комбінацій, результат у scenario_results.json
* gen_dmn.py, gen_model.py: генерація файлів DMN і BPMN
* validate.mjs, render.py, render_dmn.py, compare_models.py, charts.py: перевірка, рендер, показники, рисунки
* risk_score.py: оцінка ризику R з ЛР 3

## Запуск

Потрібні Python 3 з matplotlib і Pillow, Node.js, Google Chrome.

```
npm install
python3 gen_dmn.py
python3 gen_model.py
node validate.mjs Лабораторна_4_модель_з_правилами.bpmn Лабораторна_4_правила_рішень.dmn
python3 render.py Лабораторна_4_модель_з_правилами.bpmn Лабораторна_4_діаграма_з_правилами.png 140 10 3420 1510
python3 render_dmn.py Лабораторна_4_правила_рішень.dmn D1_Significance fig_dmn_D1_Significance.png
python3 scenarios.py
python3 compare_models.py Лабораторна_3_модель_TO-BE.bpmn Лабораторна_4_модель_з_правилами.bpmn metrics.json
python3 charts.py
```
