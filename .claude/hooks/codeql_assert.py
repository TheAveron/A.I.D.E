"""PreToolUse hook: refuse an assert with a side effect in the backend tests.

CodeQL (py/side-effect-in-assert) flags lines such as
    assert env.client.delete(url).status_code == 204
because `python -O` strips asserts, and the request with them. The fix is
    r = env.client.delete(url)
    assert r.status_code == 204

Only the lines the edit adds are checked: the existing tests contain many
such asserts that CodeQL does not report, and they must not block an edit.

Silent (exit 0) when nothing is found, so it costs no tokens. Exit 2 blocks
the edit and sends the message on stderr to Claude.
"""

import json
import re
import sys
from pathlib import Path

CALL = re.compile(r"\bclient\.(get|post|put|patch|delete|request|head|options)\(")


def edits(tool_name, tool_input, path):
    """Return (old_text, new_text) pairs for the edit."""
    if tool_name == "Write":
        try:
            old = path.read_text(encoding="utf-8")
        except OSError:
            old = ""
        return [(old, tool_input.get("content", ""))]
    if tool_name == "MultiEdit":
        return [
            (e.get("old_string", ""), e.get("new_string", ""))
            for e in tool_input.get("edits", [])
        ]
    return [(tool_input.get("old_string", ""), tool_input.get("new_string", ""))]


def added_lines(old, new):
    before = {line.strip() for line in old.splitlines()}
    return [line for line in new.splitlines() if line.strip() not in before]


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    tool_input = event.get("tool_input") or {}
    path = Path(tool_input.get("file_path") or "")
    if path.suffix != ".py" or "/backend/tests/" not in path.as_posix():
        return 0

    hits = [
        line.strip()
        for old, new in edits(event.get("tool_name", ""), tool_input, path)
        for line in added_lines(old, new)
        if line.lstrip().startswith("assert") and CALL.search(line)
    ]
    if not hits:
        return 0

    print(
        "CodeQL py/side-effect-in-assert: never call the client inside an assert. "
        "Write `r = env.client.xxx(...)` then `assert r.status_code == ...`. "
        "Rewrite these lines:\n" + "\n".join(hits),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
