#!/bin/bash
# ╔══════════════════════════════════════════════════════╗
# ║  Kin — Запуск агента в новом видимом терминале       ║
# ║  Использование:                                       ║
# ║    ./scripts/new-agent.sh <тип> <папка-задачи>       ║
# ║  Пример:                                             ║
# ║    ./scripts/new-agent.sh bugfix fix-notifications   ║
# ║    ./scripts/new-agent.sh design redesign-settings   ║
# ╚══════════════════════════════════════════════════════╝

PROJECT_ROOT="/Users/mac/Desktop/AVERA"
TASK_TYPE="${1:-}"
TASK_NAME="${2:-}"

# Цвета для вывода
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

if [ -z "$TASK_TYPE" ]; then
  echo -e "${YELLOW}Использование: $0 <тип> [папка-задачи]${NC}"
  echo ""
  echo "Типы задач:"
  echo "  bugfix       — исправление бага"
  echo "  design       — UI/визуал"
  echo "  feature      — новая функциональность"
  echo "  supabase     — работа с БД/backend"
  echo "  migration    — миграция схемы"
  echo "  integration  — сторонние сервисы"
  echo "  deploy       — сборка и деплой"
  echo "  refactor     — рефакторинг"
  echo "  audit        — ревью/расследование"
  echo ""
  echo "Пример: $0 bugfix fix-settings-crash"
  exit 1
fi

# Определяем папку задачи
if [ -n "$TASK_NAME" ]; then
  TASK_DIR="$PROJECT_ROOT/tasks/active/$TASK_NAME"
  TASK_LABEL="$TASK_TYPE: $TASK_NAME"
else
  TASK_DIR=""
  TASK_LABEL="$TASK_TYPE (без активной задачи)"
fi

# Создаём папку задачи если не существует
if [ -n "$TASK_DIR" ] && [ ! -d "$TASK_DIR" ]; then
  mkdir -p "$TASK_DIR"
  TEMPLATE="$PROJECT_ROOT/00_AGENT_MENU/templates/${TASK_TYPE}.task.md"
  if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$TASK_DIR/TASK.md"
    echo -e "${GREEN}✅ Создана папка задачи: tasks/active/$TASK_NAME/TASK.md${NC}"
    echo -e "${YELLOW}⚠️  Заполни TASK.md перед запуском агента${NC}"
  else
    echo "# $TASK_TYPE Task — $TASK_NAME" > "$TASK_DIR/TASK.md"
    echo "Status: active" >> "$TASK_DIR/TASK.md"
  fi
fi

# Формируем prompt для Claude
if [ -n "$TASK_DIR" ] && [ -f "$TASK_DIR/TASK.md" ]; then
  PROMPT="Прочитай tasks/active/$TASK_NAME/TASK.md и 00_AGENT_MENU/ROUTER.md. Это задача типа $TASK_TYPE. Выполни её в соответствии с правилами проекта."
else
  PROMPT="Это сессия для задачи типа: $TASK_TYPE. Прочитай AGENTS.md и 00_AGENT_MENU/ROUTER.md чтобы понять контекст."
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🚀 Запуск агента: $TASK_LABEL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Открываем новое окно Terminal.app с Claude
osascript <<EOF
tell application "Terminal"
  activate
  set newTab to do script "cd '$PROJECT_ROOT' && echo '╔══════════════════════════════════════════╗' && echo '║  КIN АГЕНТ: $TASK_LABEL' && echo '╚══════════════════════════════════════════╝' && echo '' && claude"
  set custom title of newTab to "Kin: $TASK_LABEL"
end tell
EOF

echo -e "${GREEN}✅ Терминал открыт — агент запускается${NC}"
