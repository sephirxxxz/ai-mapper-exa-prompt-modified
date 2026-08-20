#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--codex|--claude|--both] [--root PATH] [--config-root PATH] --yes [--purge-data --confirm-root ABSOLUTE_PATH]" >&2
}

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
target="both"
config_root=""
confirmed=false
purge_data=false
confirm_root=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --codex) target="codex" ;;
    --claude) target="claude" ;;
    --both) target="both" ;;
    --root) shift; root="${1:-}" ;;
    --config-root) shift; config_root="${1:-}" ;;
    --yes) confirmed=true ;;
    --purge-data) purge_data=true ;;
    --confirm-root) shift; confirm_root="${1:-}" ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
  shift
done

if [ "$confirmed" != true ] || [ -z "$root" ] || [ ! -d "$root" ]; then
  usage
  exit 2
fi
root="$(cd "$root" && pwd -P)"
if [ "$root" = "/" ]; then
  echo "Refusing filesystem root." >&2
  exit 2
fi

expected=""
if [ -f "$root/.ai-mapper-project" ]; then
  expected="$(tr -d '\n' < "$root/.ai-mapper-project")"
fi
if [ "$expected" != "$root" ] || [ ! -f "$root/SKILL.md" ]; then
  echo "Refusing unverified AI Mapper root: $root" >&2
  exit 2
fi

if [ -n "$config_root" ]; then
  codex_root="$config_root/codex"
  claude_root="$config_root/claude"
else
  codex_root="${CODEX_HOME:-$HOME/.codex}"
  claude_root="$HOME/.claude"
fi

remove_symlink_if_managed() {
  path="$1"
  expected_target="$2"
  if [ -L "$path" ] && [ "$(readlink "$path")" = "$expected_target" ]; then
    rm -f -- "$path"
  fi
}

remove_launcher_if_managed() {
  path="$1"
  quoted_root="$(printf '%q' "$root")"
  if [ -f "$path" ] && grep -Fqx "AI_MAPPER_AGENT_ROOT=$quoted_root" "$path"; then
    rm -f -- "$path"
  fi
}

if [ "$target" = "codex" ] || [ "$target" = "both" ]; then
  remove_symlink_if_managed "$codex_root/skills/ai-mapper-agent" "$root"
  remove_launcher_if_managed "$codex_root/bin/ai-mapper-agent"
fi
if [ "$target" = "claude" ] || [ "$target" = "both" ]; then
  remove_symlink_if_managed "$claude_root/agents/ai-mapper.md" "$root/.claude/agents/ai-mapper.md"
  remove_symlink_if_managed "$claude_root/commands/ai-mapper.md" "$root/.claude/commands/ai-mapper.md"
  remove_launcher_if_managed "$claude_root/bin/ai-mapper-agent"
fi

rm -rf -- "$root/.venv" "$root/.local-harness"
if [ "$purge_data" = true ]; then
  if [ "$confirm_root" != "$root" ]; then
    echo "--purge-data requires --confirm-root with the exact canonical root: $root" >&2
    exit 2
  fi
  rm -rf -- "$root/runs" "$root/.context-mode"
  echo "Removed local runtime and research data. This data cannot be recovered by the uninstaller."
else
  echo "Removed local runtime only; runs/ and .context-mode/ were preserved."
fi
