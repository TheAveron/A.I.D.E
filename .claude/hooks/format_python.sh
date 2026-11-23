#!/usr/bin/env bash
# PostToolUse hook: format a backend Python file after Claude edits it, with
# black then isort in their default settings. isort runs last on purpose: its
# default import wrapping is the one kept in the code, not black's.
#
# Always silent and exits 0: it never blocks an edit and costs no tokens.
# It does nothing if the venv or its formatters are missing.

f=$(jq -r '.tool_input.file_path // empty')
case "$f" in
  */.venv/*) exit 0 ;;
  */backend/*.py) ;;
  *) exit 0 ;;
esac
[ -f "$f" ] || exit 0

venv="$CLAUDE_PROJECT_DIR/backend/.venv/bin"
[ -x "$venv/isort" ] && [ -x "$venv/black" ] || exit 0

# isort tells first-party imports (app.*) from third-party ones using the
# folder it runs in: run it from backend/, as VS Code does.
cd "${f%%/backend/*}/backend" || exit 0
"$venv/black" -q "$f" >/dev/null 2>&1
"$venv/isort" -q "$f" >/dev/null 2>&1
exit 0
