#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --codex|--claude|--both [--root PATH] [--config-root PATH] [--dry-run]" >&2
}

target=""
source_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
config_root=""
dry_run=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --codex) target="codex" ;;
    --claude) target="claude" ;;
    --both) target="both" ;;
    --root) shift; source_root="${1:-}" ;;
    --config-root) shift; config_root="${1:-}" ;;
    --dry-run) dry_run=true ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
  shift
done

if [ -z "$target" ] || [ -z "$source_root" ]; then
  usage
  exit 2
fi

if [ -n "$config_root" ]; then
  codex_root="$config_root/codex"
  claude_root="$config_root/claude"
else
  codex_root="${CODEX_HOME:-$HOME/.codex}"
  claude_root="$HOME/.claude"
fi

echo "AI Mapper Agent installation target: $target"
echo "Context Mode is mandatory and is not installed or configured automatically."
echo "Install Context Mode in each selected harness, restart it, and verify ctx_doctor before running AI Mapper."
echo "This installer does not modify global plugin settings."

if [ "$dry_run" = true ]; then
  echo "Dry run: would link the repository into $codex_root and/or $claude_root."
  exit 0
fi

source_root="$(cd "$source_root" && pwd -P)"
if [ ! -f "$source_root/SKILL.md" ] || [ ! -f "$source_root/.claude/agents/ai-mapper.md" ] || [ ! -f "$source_root/.claude/commands/ai-mapper.md" ]; then
  echo "Refusing source without the complete AI Mapper harness files: $source_root" >&2
  exit 2
fi

install_link() {
  source_path="$1"
  destination="$2"
  mkdir -p "$(dirname "$destination")"
  if [ -L "$destination" ] && [ "$(readlink "$destination")" = "$source_path" ]; then
    return
  fi
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    echo "Refusing to overwrite unrelated harness target: $destination" >&2
    exit 2
  fi
  ln -s "$source_path" "$destination"
}

install_launcher() {
  destination="$1/bin/ai-mapper-agent"
  mkdir -p "$(dirname "$destination")"
  quoted_root="$(printf '%q' "$source_root")"
  marker_line="AI_MAPPER_AGENT_ROOT=$quoted_root"
  managed=false
  if [ -f "$destination" ] && grep -Fqx "$marker_line" "$destination"; then
    managed=true
  fi
  if [ "$managed" != true ] && { [ -e "$destination" ] || [ -L "$destination" ]; }; then
    echo "Refusing to overwrite unrelated launcher: $destination" >&2
    exit 2
  fi
  {
    echo '#!/usr/bin/env bash'
    echo 'set -euo pipefail'
    echo "$marker_line"
    echo 'export PYTHONPATH="$AI_MAPPER_AGENT_ROOT${PYTHONPATH:+:$PYTHONPATH}"'
    echo 'export CONTEXT_MODE_PROJECT_DIR="$AI_MAPPER_AGENT_ROOT"'
    echo 'export CONTEXT_MODE_DIR="$AI_MAPPER_AGENT_ROOT/.context-mode"'
    echo 'exec python3 -m ai_mapper_agent "$@"'
  } > "$destination"
  chmod 755 "$destination"
}

install_codex() {
  install_link "$source_root" "$codex_root/skills/ai-mapper-agent"
  install_launcher "$codex_root"
}

install_claude() {
  install_link "$source_root/.claude/agents/ai-mapper.md" "$claude_root/agents/ai-mapper.md"
  install_link "$source_root/.claude/commands/ai-mapper.md" "$claude_root/commands/ai-mapper.md"
  install_launcher "$claude_root"
}

case "$target" in
  codex) install_codex ;;
  claude) install_claude ;;
  both)
    install_codex
    install_claude
    ;;
esac

echo "AI Mapper Agent is discoverable in the selected harness. Context Mode must pass ctx_doctor before research."
