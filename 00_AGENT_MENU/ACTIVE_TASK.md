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

## Сессия 2026-06-23 — Outreach Wave 1 запущена

### Что сделано:
1. **Выбрана стратегия B** — Industry Outreach как приоритет перед техническими фичами
2. **Создан реальный трекер контактов** — `docs/AVERA_REAL_CONTACT_TRACKER_V1.md`
   - 6 именных контактов с должностями, LinkedIn и персональными сообщениями
   - Источник: спикеры Automotive Functional Safety Week 2025/2026
3. **Отправлены первые сообщения:**
   - ✅ Thomas Kirschbaum (Bosch, Senior Expert System Safety) — LinkedIn DM отправлен
   - ✅ Dr. Roman Krzemien (ZF, Head of Safety CoE) — LinkedIn: de.linkedin.com/in/dr-roman-krzemien-268b603b — сообщение подготовлено
4. **Обновлён .gitignore** — все outreach/contact файлы исключены из GitHub
5. **Marc Henn (LinkedIn)** — определён как финансовый советник из Цинциннати, нерелевантен для AVERA

### Контакты в очереди (не отправлено):
- Marzana Khatun (Bosch, Functional Safety Manager) — найти LinkedIn
- Danilo Da Costa Ribeiro (Continental, System Safety Manager) — найти LinkedIn
- Batuhan Keskintas (ZF, FS Engineer AD/ADAS) — найти LinkedIn
- Abhash Das (ZF, Safety Expert) — найти LinkedIn

### Правило аутрича:
- НЕ писать на общие ящики компаний
- Только именные LinkedIn DM
- Ждать 5 рабочих дней перед follow-up

### Следующая сессия — читать:
1. `docs/AVERA_REAL_CONTACT_TRACKER_V1.md` — статус контактов
2. Проверить ответы от Thomas Kirschbaum и Roman Krzemien

## Не трогать без запроса

- fixtures/bms-* — стабильные фикстуры
- src/avera/core.py — публичный API
- src/avera/classify/ — классификатор
- src/avera/compare/ — компаратор
