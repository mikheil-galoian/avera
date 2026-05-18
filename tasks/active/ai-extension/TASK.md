# Task: AI Extension — Verification Proof of Concept

**Type:** feature
**Status:** in_progress
**Created:** 7 May 2026
**Priority:** critical

## Goal

Доказать что AVERA обнаруживает регрессию AI-модели без изменений в ядре.
Превратить AVERA из automotive verification tool в AI change verification infrastructure.

## Allowed Zones

```
src/avera/adapters/ai_evaluation.py   ← СОЗДАН ✓
src/avera/ingestion/model_card.py     ← следующий шаг
fixtures/adas-model-update-regression/ ← СОЗДАН ✓ (8 файлов)
tests/test_ai_model_update_fixture.py  ← СОЗДАН ✓
docs/AVERA_AI_EXTENSION.md            ← следующий шаг
```

## Что уже сделано

- [x] `fixtures/adas-model-update-regression/` — полный fixture (8 файлов)
  - change_description.txt
  - requirements.csv (6 требований, включая ASIL-D)
  - component_map.json
  - baseline_results.json (6 тестов, все pass, модель v2.4.0)
  - current_results.json (6 тестов, 1 fail: detection_rate=0.94 < 0.95)
  - model_card_baseline.json (v2.4.0, certified)
  - model_card_current.json (v2.4.1, pending_validation)

- [x] `src/avera/adapters/ai_evaluation.py`
  - `load_ai_evaluation(path)` — конвертер AI eval → AVERA format
  - `model_card_to_metadata(path)` — загрузчик model card
  - `_validate_ai_evaluation()` — валидация входных данных

- [x] `tests/test_ai_model_update_fixture.py`
  - TestAIModelUpdateFixture (6 тестов полного пайплайна)
  - TestAIEvaluationAdapter (8 unit тестов адаптера)

## Что осталось

### Шаг 1: Запустить и проверить (локально)

```bash
# Из корня проекта AVERA:
PYTHONPATH=src python3 -B -m pytest tests/test_ai_model_update_fixture.py -v
```

Ожидаемый результат:
- TestAIModelUpdateFixture::test_ai_regression_detected → PASSED
- TestAIModelUpdateFixture::test_ai_regression_risk_is_high → PASSED
- Все 14 тестов → PASSED

Если что-то не проходит — читать сообщение ошибки и исправлять fixture или адаптер.

### Шаг 2: Запустить полный pipeline на fixture

```bash
PYTHONPATH=src python3 -B -m avera analyze \
  --project fixtures/adas-model-update-regression \
  --out reports/fixtures/adas-model-update-regression
```

Проверить что report содержит:
- `"verdict": "confirmed_regression"`
- `"risk": "high"` или `"release_blocking"`
- `"affected_requirements"` содержит `"REQ-SAFETY-012"`

### Шаг 3: Добавить ingestion/model_card.py

```python
# src/avera/ingestion/model_card.py
from pathlib import Path
import json

def load_model_card(path: Path) -> dict:
    """Load AI model card artifact."""
    path = Path(path)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)
```

### Шаг 4: Добавить model_card в core.py

В `src/avera/core.py` в функции `analyze()` добавить после сигнального трейса:

```python
# Загрузить model card если есть
model_card_path = Path(current_path).parent / "model_card_current.json"
if model_card_path.exists():
    from avera.ingestion.model_card import load_model_card
    report["model_metadata"] = load_model_card(model_card_path)
```

### Шаг 5: Добавить fixture в run_all_fixtures.py

Открыть `scripts/run_all_fixtures.py` и добавить `adas-model-update-regression`
в список fixtures.

### Шаг 6: Написать docs/AVERA_AI_EXTENSION.md

Документ для engineering teams которые внедряют AI в регулируемые системы.

### Шаг 7: Полный pytest suite

```bash
PYTHONPATH=src python3 -B -m pytest tests/ -v
```

Ожидание: все 63 + 14 новых = 77 тестов PASSED.

## Ожидаемый вердикт fixture

```json
{
  "verdict": "confirmed_regression",
  "risk": "high",
  "confidence": "high",
  "affected_components": ["adas-perception-module"],
  "affected_requirements": ["REQ-SAFETY-012"],
  "evidence": {
    "detection_rate": {
      "baseline": 0.97,
      "current": 0.94,
      "operator": ">=",
      "threshold": 0.95
    }
  }
}
```

## Стратегический контекст

Этот fixture доказывает что AVERA решает проблему governance AI-изменений:
- FDA AI/ML-SaMD требует evidence при каждом обновлении модели
- EU AI Act требует risk assessment для high-risk AI систем
- UNECE WP.29 требует доказательство безопасности OTA обновлений

AVERA = первый инструмент который даёт proof chain для AI model changes
без изменений в kernel.
