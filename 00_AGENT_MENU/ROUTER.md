# Agent Router

## Обязательный порядок перед любой задачей

1. Прочитай `AGENTS.md`.
2. Прочитай `ARCHITECTURE.md`.
3. Прочитай `00_AGENT_MENU/PROJECT_MAP.md`.
4. Классифицируй запрос используя `00_AGENT_MENU/TASK_TYPES.md`.
5. Проверь `00_AGENT_MENU/ACTIVE_TASK.md`.
6. Если активная задача совпадает — прочитай её папку в `tasks/active/`.
7. Если активной задачи нет и работа нетривиальная — предложи создать task-папку.
8. Работай только внутри разрешённых зон.

## Routing Rules

| Запрос | Тип задачи | Шаблон |
| ------ | ---------- | ------ |
| Сломанное поведение | `bugfix` | `templates/bugfix.task.md` |
| UI/визуал/верстка | `design` | `templates/design.task.md` |
| Новое поведение | `feature` | `templates/feature.task.md` |
| Чистка кода без изменений | `refactor` | `templates/refactor.task.md` |
| Документация, планирование | `docs` | `templates/docs.task.md` |
| Только тесты | `test` | `templates/audit.task.md` |
| Ревью, расследование | `audit` | `templates/audit.task.md` |
| Сборка, деплой, версия | `deploy` | `templates/deploy.task.md` |
| Supabase / backend | `supabase` | `templates/supabase.task.md` |
| Миграция БД | `migration` | `templates/migration.task.md` |
| Сторонний сервис | `integration` | `templates/integration.task.md` |
| Координация нескольких задач | `orchestration` | `templates/orchestration.task.md` |

## Дополнительные правила

Читай перед работой в соответствующей зоне:

- Безопасность → `00_AGENT_MENU/SAFETY_RULES.md` ✅ (есть)
- Деплой/сборка → `.github/workflows/` + `docs/AVERA_GITHUB_ACTION_V0_1_0_RELEASE.md`, `docs/AVERA_RUNTIME_STABILIZATION.md`

Зон-гайдов ниже в проекте **сейчас нет** (нет Supabase/внешней БД). Создавать по запросу,
а до этого — остановись и спроси (см. ниже):

- Supabase-работа → `00_AGENT_MENU/SUPABASE.md` ⚠️ (не создан — Supabase в проекте не используется)
- Интеграции → `00_AGENT_MENU/INTEGRATIONS.md` ⚠️ (не создан)
- БД/миграции → `00_AGENT_MENU/DATABASE.md` ⚠️ (не создан; локально только SQLite store в `src/avera/storage/`)

## Остановись и спроси когда

- тип задачи неясен;
- нет task-папки и работа широкая;
- реализация требует файлов вне разрешённых зон;
- design-задача требует backend/API/database изменений;
- bugfix превращается в рефакторинг архитектуры.
