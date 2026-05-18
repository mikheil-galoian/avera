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
  avera/            — основная логика
    core/           — анализ изменений, риска
    reporters/      — форматирование отчётов
    cli/            — CLI точки входа

demo/               — Streamlit демо
scripts/            — утилиты
tests/              — тесты
fixtures/           — тестовые данные
docs/               — документация
```

## Ключевые файлы по типу задачи

| Задача    | Файлы                                      |
| --------- | ------------------------------------------ |
| bugfix    | src/avera/ затронутый модуль               |
| design    | demo/ Streamlit UI                         |
| feature   | src/avera/core/ или src/avera/cli/         |
| refactor  | явно указанные файлы в src/                |
| audit     | docs/, fixtures/, reports/                 |
| deploy    | pyproject.toml, scripts/, start_demo.sh    |
