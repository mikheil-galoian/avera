# AVERA — Architecture (root pointer)

> Канонический, подробный документ архитектуры: [`docs/AVERA_ARCHITECTURE.md`](docs/AVERA_ARCHITECTURE.md).
> Этот файл — короткая карта верхнего уровня, на которую ссылается `00_AGENT_MENU/ROUTER.md` (шаг 2).

## Что это

AVERA — детерминированный gate регрессий для изменений в коде/верификации безопасно-критичных систем. Сравнивает baseline-прогон тестов с текущим и блокирует релиз только при **доказанной введённой регрессии** (тест проходил раньше — падает сейчас), оставляя tamper-evident след под вердиктом. LLM в пути принятия решения нет.

## Поток данных (детерминированный пайплайн)

```
ingestion → compare → classify → gate → evidence-manifest → audit-log → sign-off
```

Один и тот же вход → один и тот же вердикт → один и тот же `integrity_root` на любой машине.

## Реальная раскладка кода

```
src/
  avera/                  — ядро (импортируемая библиотека)
    core.py               — публичная analyze(): тонкая обвязка пайплайна
    cli.py                — CLI (argparse): analyze, check, gate, pack, action-run, …
    ingestion/            — загрузка requirements / component_map / verification_results / model_card
    models/               — датаклассы артефактов
    adapters/             — форматы вход. артефактов: junit, simulation, logs, requirements, canoe, ai_evaluation
    compare/              — baseline vs current (fail-closed таксономия статусов)
    classify/             — классификация регрессий + proven-total verdict spec
    gates/                — детерминированный gate, policy-as-data (policy_loader)
    evidence/             — content-addressed evidence manifest (integrity_root) + audit binding
    audit/                — hash-chained SHA-256 audit log (опц. keyed HMAC)
    signoff/              — конечный автомат sign-off, привязан к корню манифеста
    graph/                — evidence graph
    memory/               — JSONL memory ledger
    traceability/         — component-first traceability index
    trends/               — trend index по памяти
    query/                — локальные запросы к traceability
    decisions/            — engineering decision engine
    pack/                 — portable workspace pack
    contracts/            — стабильные контракты артефактов + валидатор
    coverage/             — проверка покрытия требований
    mutation/             — fault-injection / mutation lens (доверие)
    copilot/              — review copilot
    registry/             — пороги
    storage/              — sqlite store
    feedback/             — feedback store
    domains/              — профили доменов: powertrain, avionics, space, (railway/medical в политиках)
    reports/              — json/markdown отчёты + schema
    validation/           — валидация workspace и отчёта
    signals/              — signal trace
  avera_api/              — КАНОНИЧЕСКИЙ REST API (FastAPI): main:app, auth, models
                            точка входа pyproject `avera-api`, документирован в README,
                            покрыт tests/test_api.py и tests/test_api_evidence_pack.py

demo/                     — Streamlit demo shell (app.py); запуск через ./start_demo.sh
benchmark/                — публичный blind-replay бенчмарк регрессий (reproduce.sh)
fixtures/                 — эталонные сценарии по доменам
scripts/                  — утилиты (runtime_doctor, blind_replay, record_demo, …)
tests/                    — 66 тест-файлов: юниты + кросс-доменные фикстуры + полный proof verdict-spec
docs/                     — спецификации, hardening, GTM, и docs/AVERA_ARCHITECTURE.md (канон)
.github/workflows/        — CI (avera-gate, avera-analysis, action smoke/dogfood, docker publish)
```

## Известные технические долги (на момент правки)

- `src/avera/api/` (`app.py` + `__init__.py`) — устаревший дубль REST API. Канон — `src/avera_api/`. Ничто, кроме самого пакета, его не импортирует; кандидат на удаление.
- В репозитории физически присутствует `build/` (в `.gitignore`) и несколько macOS-дубликатов вида `* 2.py` / `* 2.json` — подлежат чистке.

См. полную версию: [`docs/AVERA_ARCHITECTURE.md`](docs/AVERA_ARCHITECTURE.md).
