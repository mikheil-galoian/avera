# AVERA — Action Plan
**Дата создания:** 7 May 2026
**Статус:** активный план
**Горизонт:** краткосрочный (4 дня) + среднесрочный (6 месяцев) + долгосрочный (3 года)

---

## КОНТЕКСТ: Откуда мы стартуем

### Что уже есть и работает
- Рабочий Python kernel: `src/avera/` — 10-слойный пайплайн
- 63 теста проходят, детерминированный вывод
- 12 fixture-сценариев: BMS (8) + ADAS (2) + adapted (2)
- Полный pipeline: ingestion → comparison → classification → report → graph → gate → memory → traceability → decision → trend → pack
- Thin Streamlit demo shell (`demo/app.py`, `./start_demo.sh`)
- Design-partner outreach материалы для CARIAD, Continental, ZF, ETAS, TraceTronic

### Что определено на этой сессии
1. **Стратегия глобального масштабирования** → `docs/AVERA_SCALE_FOUNDATION_MASTER.md`
2. **AI-верификация как главное новое направление** — AVERA становится инструментом доказательства безопасности AI-изменений в регулируемых отраслях
3. **Конкретный путь расширения** — без изменений в ядре, через новые адаптеры и fixtures

---

## БЛОК 1 — НЕМЕДЛЕННО (4 дня)
### AI Extension: доказательство концепции

Цель: доказать что AVERA обнаруживает регрессию AI-модели,
строит evidence chain и выдаёт решение — без изменений в ядре.

---

### День 1 — AI Fixture и данные

**Задача 1.1: Создать fixture `adas-model-update-regression`**

Путь: `fixtures/adas-model-update-regression/`

Файлы для создания:

```
change_description.txt
requirements.csv
component_map.json
baseline_results.json    ← evaluation результаты модели v2.4.0
current_results.json     ← evaluation результаты модели v2.4.1
model_card_baseline.json ← паспорт baseline модели
model_card_current.json  ← паспорт новой модели
```

Сценарий: обновление perception модели ADAS v2.4.0 → v2.4.1.
Регрессия: `pedestrian_night_rain` detection_rate упал с 0.97 → 0.94
(порог требования: 0.95). Ожидаемый verdict: `confirmed_regression`,
risk: `release_blocking`.

**Задача 1.2: Проверить что существующий пайплайн уже работает**

```bash
PYTHONPATH=src python3 -B -m avera analyze \
  --project fixtures/adas-model-update-regression \
  --out reports/fixtures/adas-model-update-regression
```

Если выдаёт `confirmed_regression` — ядро работает без изменений.
Если нет — идентифицировать что именно нужно скорректировать в fixture.

---

### День 2 — Адаптер AI-артефактов

**Задача 2.1: Написать `src/avera/adapters/ai_evaluation.py`**

Конвертирует AI evaluation результаты (метрики по сценариям)
в стандартный AVERA `verification_results` формат.

Интерфейс:
```python
def load_ai_evaluation(path: Path) -> dict:
    """Конвертировать AI evaluation JSON в AVERA verification_results."""
    ...

def model_card_to_metadata(path: Path) -> dict:
    """Загрузить model_card и вернуть метаданные для отчёта."""
    ...
```

**Задача 2.2: Написать `src/avera/ingestion/model_card.py`**

```python
def load_model_card(path: Path) -> dict:
    """Загрузить паспорт AI-модели."""
    ...
```

Добавить в `core.py`: если в папке проекта есть `model_card_current.json`
— подгружать и включать в report как `model_metadata`.

---

### День 3 — Тест и верификация

**Задача 3.1: Написать тест `tests/test_ai_model_update_fixture.py`**

```python
def test_ai_model_regression_detected():
    """AI model update causing regression is detected as confirmed_regression."""
    ...

def test_ai_model_update_verdict():
    """Fixture produces release_blocking risk for safety-critical regression."""
    ...

def test_ai_model_card_in_report():
    """Model card metadata appears in generated report."""
    ...
```

**Задача 3.2: Запустить полный pytest suite**

```bash
PYTHONPATH=src python3 -B -m pytest tests/ -v
```

Ожидание: все 63 существующих теста + новые проходят.

**Задача 3.3: Добавить новый fixture в `scripts/run_all_fixtures.py`**

Убедиться что `adas-model-update-regression` входит в полный прогон.

---

### День 4 — Документация и позиционирование

**Задача 4.1: Обновить `docs/AVERA_IMPLEMENTATION_STATUS.md`**

Добавить AI extension как реализованную возможность.

**Задача 4.2: Написать `docs/AVERA_AI_EXTENSION.md`**

Документ: как AVERA работает с AI-изменениями.
Для кого: engineering teams внедряющие AI в регулируемые системы.
Содержание:
- проблема (AI changes без governance)
- как AVERA решает (baseline/current для AI metrics)
- формат AI-артефактов
- пример из fixture
- регуляторный контекст (FDA AI/ML-SaMD, EU AI Act, UNECE WP.29)

**Задача 4.3: Обновить README.md**

Добавить секцию "AI System Change Verification" с примером команды
для нового fixture.

---

## БЛОК 2 — БЛИЖАЙШИЕ 30 ДНЕЙ

### Первый design-partner контакт

**Задача 5.1: Подготовить AI-focused outreach письмо**

Файл: `docs/outreach/AVERA_EMAIL_AI_TEAMS.md`

Целевая аудитория: команды, которые уже внедряют AI в safety-critical системы
и не знают как доказывать безопасность изменений модели.

Конкретные targets:
- TraceTronic (Дрезден) — automotive test management, знают боль
- ETAS (Stuttgart) — embedded tools, Bosch ecosystem
- Любая команда на LinkedIn с тегами: "ISO 26262", "ADAS validation",
  "AI safety", "functional safety engineer"

**Задача 5.2: PyPI packaging**

```bash
pip install avera
```

Что нужно:
- финализировать `pyproject.toml` с правильными metadata
- написать `CHANGELOG.md` v0.1.0
- создать `src/avera/contracts/versions.py` (artifact version registry)
- опубликовать на PyPI

**Задача 5.3: GitHub Actions workflow**

Файл: `.github/workflows/avera-analysis.yml`

Позволяет любой команде добавить AVERA в CI одной строкой.

---

## БЛОК 3 — Q3 2026 (Июль–Сентябрь)

| # | Задача | Выход |
|---|--------|-------|
| 6.1 | FastAPI REST wrapper | `src/avera_api/` с основными endpoints |
| 6.2 | Powertrain domain module | `src/avera/domains/powertrain/` |
| 6.3 | SQLite storage backend | `src/avera/storage/sqlite_store.py` |
| 6.4 | Docker image (CLI) | `averaeng/avera:cli` на Docker Hub |
| 6.5 | Determinism regression tests | `tests/test_kernel_determinism.py` |
| 6.6 | Adapter SDK interface | `src/avera/adapters/interface.py` |
| 6.7 | CANoe/CAPL adapter | `src/avera/adapters/canoe.py` |
| 6.8 | xUnit adapter hardening | расширение `adapters/junit.py` |

---

## БЛОК 4 — Q4 2026

| # | Задача | Выход |
|---|--------|-------|
| 7.1 | ISO 26262 report template | `src/avera/compliance/iso26262.py` |
| 7.2 | Chassis domain module | `src/avera/domains/chassis/` |
| 7.3 | GitLab CI + Jenkins integration | примеры конфигурации + docs |
| 7.4 | API authentication (API key) | middleware в `avera_api` |
| 7.5 | ASPICE report template | `src/avera/compliance/aspice.py` |
| 7.6 | AI drift monitoring adapter | `src/avera/adapters/ai_drift.py` |

---

## БЛОК 5 — Q1 2027

| # | Задача | Выход |
|---|--------|-------|
| 8.1 | Cybersecurity domain (ISO 21434) | `src/avera/domains/cybersecurity/` |
| 8.2 | PostgreSQL storage backend | `src/avera/storage/postgres_store.py` |
| 8.3 | OIDC/SSO authentication | enterprise auth layer |
| 8.4 | Kubernetes manifests | `deploy/k8s/` |
| 8.5 | gRPC interface | `proto/avera.proto` |
| 8.6 | AI/ML-SaMD compliance template | FDA-aligned report structure |
| 8.7 | Jama Connect adapter | `src/avera/adapters/jama.py` |

---

## БЛОК 6 — 2027 И ДАЛЕЕ

### 2027 H1
- ADAS++ (L3/L4) domain module
- Cross-domain evidence chains
- AI root cause suggestion engine (opt-in, conservative)
- Documentation site v1 (docs.avera.engineering)
- Program memory layer (cross-project)

### 2027 H2
- Polarion ALM adapter
- DOORS Next adapter
- Multi-region deployment support
- OTA update domain module
- EU AI Act compliance mode

### 2028–2030
- Commercial truck / off-highway domains
- Robotics domain
- Organization memory layer (cross-program)
- Field feedback + lifecycle correlation
- First Series A / strategic partnership target

### 2030–2035 (Vision)
```
AVERA = Universal Engineering Evidence Infrastructure

Любое изменение в любой safety-critical системе —
automotive, medical, aviation, industrial, AI —
оставляет дурабельный, трассируемый, proof-backed след.

Engineering truth, preserved as evidence.
```

---

## КЛЮЧЕВЫЕ ПРИНЦИПЫ — не нарушать никогда

1. **Ядро не трогать ради product удобства** — kernel = proof machine
2. **Детерминизм обязателен** — одинаковые входы = одинаковые выходы
3. **Консервативность по умолчанию** — лучше uncertainty чем false confidence
4. **Air-gapped должен работать всегда** — zero internet = full function
5. **CLI — первый класс, не legacy** — каждая новая функция = CLI команда
6. **Schema breaks = deprecation window** — 90 дней минимум
7. **Memory append-only** — ни одна запись не удаляется
8. **AI предлагает, evidence решает** — AI = suggestion, не verdict

---

## ЗАВТРА — ПЕРВЫЕ ДЕЙСТВИЯ

```
1. Открыть AVERA_ACTION_PLAN_2026_05_07.md (этот файл)
2. Прочитать AVERA_SCALE_FOUNDATION_MASTER.md для контекста
3. Начать с Задачи 1.1: создать fixtures/adas-model-update-regression/
4. Задача 1.2: запустить пайплайн на новом fixture
5. Задача 2.1: написать adapters/ai_evaluation.py
6. Задача 3.1: написать тест
7. Задача 3.2: запустить pytest — все тесты должны пройти
```

---

*AVERA — Engineering Memory Infrastructure for Mobility*
*Action Plan v1.0 — 7 May 2026*
