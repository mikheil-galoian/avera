# AVERA — Project Map

## Что это

AVERA (Automotive Verification, Evidence & Risk Architecture) — платформа анализа изменений в автомобильном ПО.
Стек: Python 3.11+, Streamlit (demo), Click CLI.

## Стек

| Слой        | Технология                          |
| ----------- | ----------------------------------- |
| Backend     | Python 3.11+                        |
| Demo UI     | Streamlit                           |
| CLI         | Click                               |
| Тесты       | pytest, fixtures/                   |
| Конфиг      | avera.config.json, pyproject.toml   |

## Code Zones

```text
src/
  avera/            — основная логика (импортируемая библиотека)
    core.py         — публичная analyze(): обвязка пайплайна
    cli.py          — CLI точки входа (argparse)
    compare/        — baseline vs current
    classify/       — классификация регрессий + verdict spec
    gates/          — детерминированный gate (policy-as-data)
    evidence/ audit/ signoff/  — манифест, hash-chained лог, sign-off
    adapters/ ingestion/ models/ — вход. форматы и датаклассы
    reports/        — форматирование отчётов (json/markdown)
    domains/        — профили доменов (powertrain, avionics, space, …)
  avera_api/        — канонический REST API (FastAPI): main:app, auth, models

demo/               — Streamlit демо (app.py); запуск ./start_demo.sh
scripts/            — утилиты
tests/              — тесты (66 файлов)
fixtures/           — тестовые данные
docs/               — документация (канон архитектуры: docs/AVERA_ARCHITECTURE.md)
```

## Ключевые файлы по типу задачи

| Задача    | Файлы                                      |
| --------- | ------------------------------------------ |
| bugfix    | src/avera/ затронутый модуль               |
| design    | demo/ Streamlit UI                         |
| feature   | src/avera/core.py, src/avera/cli.py или нужный пакет в src/avera/ |
| refactor  | явно указанные файлы в src/                |
| audit     | docs/, fixtures/, reports/                 |
| deploy    | pyproject.toml, scripts/, start_demo.sh    |
