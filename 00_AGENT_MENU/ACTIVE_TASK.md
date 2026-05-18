# ACTIVE TASK

**Task:** AVERA Scale & AI Extension — полная реализация
**Started:** 7 May 2026
**Status:** in_progress
**Priority:** critical

## Контекст сессии

Сессия 7 мая 2026 установила следующее:

1. Ядро AVERA работает — 63 теста, детерминированный пайплайн, BMS + ADAS домены
2. Написан мастер-документ масштабирования: `docs/AVERA_SCALE_FOUNDATION_MASTER.md`
3. Определена стратегия расширения в AI-верификацию как главное новое направление
4. Определён конкретный план реализации AI-extension (4 дня работы)

## Следующая сессия — читать СНАЧАЛА

1. `docs/AVERA_SCALE_FOUNDATION_MASTER.md` — стратегический план масштабирования
2. `docs/AVERA_ACTION_PLAN_2026_05_07.md` — конкретный план действий с задачами
3. `tasks/active/ai-extension/` — рабочая папка задачи

## Allowed Zones

```
src/avera/adapters/          — новый ai_evaluation.py адаптер
src/avera/ingestion/         — новый load_model_card()
fixtures/adas-model-update-regression/   — новый AI fixture
tests/                       — новый test_ai_model_update_fixture.py
docs/                        — документация
```

## Не трогать без запроса

- fixtures/bms-* — стабильные фикстуры
- src/avera/core.py — публичный API
- src/avera/classify/ — классификатор
- src/avera/compare/ — компаратор
