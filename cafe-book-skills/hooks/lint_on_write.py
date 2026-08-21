#!/usr/bin/env python3
"""PostToolUse 훅 — 원고 파일을 쓰거나 고칠 때마다 문체 검사를 돌린다.

문체 게이트는 사람이 기억해서 돌리는 것이 아니라 원고를 건드릴 때마다
저절로 돌아야 한다. 오류가 남으면 종료 코드 2로 알려 그 자리에서 고치게 한다.

settings.json의 PostToolUse(Write|Edit)에 건다.
원고 경로는 MANUSCRIPT_GLOB 환경변수로 좁힌다. 기본값은 manuscript/.
"""

import json
import os
import subprocess
import sys

SUITE = os.environ.get("CAFE_BOOK_SKILLS",
                       os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINTER = os.path.join(SUITE, "literary-prose-voice", "scripts", "prose_lint.py")
SCOPE = os.environ.get("MANUSCRIPT_GLOB", "manuscript/")


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0

    path = (event.get("tool_input") or {}).get("file_path", "")
    if not path or not path.endswith((".md", ".txt")):
        return 0
    if SCOPE not in path.replace(os.sep, "/"):
        return 0
    if not os.path.exists(LINTER) or not os.path.exists(path):
        return 0

    proc = subprocess.run([sys.executable, LINTER, path, "--only", "error"],
                          capture_output=True, text=True)
    if proc.returncode != 1:
        return 0

    sys.stderr.write(
        "문체 게이트에 걸렸다. 아래 오류를 고친 뒤 계속한다.\n"
        "판정 기준은 literary-prose-voice 스킬의 references/forbidden-patterns.md에 있다.\n\n"
        + proc.stdout)
    return 2


if __name__ == "__main__":
    sys.exit(main())
