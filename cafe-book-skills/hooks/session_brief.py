#!/usr/bin/env python3
"""SessionStart 훅 — 세션을 열 때 책의 현재 상태를 한눈에 보여 준다.

어느 장이 어느 게이트에 걸려 있는지 모르는 채로 작업을 시작하면
통과하지 않은 앞 단계를 건너뛰게 된다.

settings.json의 SessionStart에 건다.
"""

import json
import os
import sys

STATE = os.environ.get("BOOK_STATE", "book-state.json")
LEDGER_ORDER = ["concept", "ledger_reserved", "draft", "voice", "ledger_committed",
                "copyedit", "transcreation", "en_review", "integrity"]
LABELS = {
    "concept": "콘셉트", "ledger_reserved": "변주예약", "draft": "초고",
    "voice": "문체", "ledger_committed": "변주확정", "copyedit": "교열",
    "transcreation": "재저작", "en_review": "영어검수", "integrity": "무결성",
}


def main():
    if not os.path.exists(STATE):
        return 0
    try:
        with open(STATE, encoding="utf-8") as fh:
            state = json.load(fh)
    except (ValueError, OSError):
        return 0

    book = state.get("book") or {}
    chapters = state.get("chapters") or []
    lines = [f"# {book.get('title_ko', '제목 미정')} — 현재 상태",
             f"단계: {book.get('stage', '미정')}   장 수: {len(chapters)}/{book.get('chapter_count', '?')}"]

    stuck, failed = [], []
    for ch in chapters:
        status = ch.get("status") or {}
        if any(v == "failed" for v in status.values()):
            failed.append(f"{ch.get('no')}장 {ch.get('space_ko', '')}")
            continue
        for gate in LEDGER_ORDER:
            value = status.get(gate, "none")
            if value in ("none", "pending"):
                stuck.append(f"{ch.get('no')}장 {ch.get('space_ko', '')} → {LABELS[gate]}")
                break

    if failed:
        lines.append("\n반려 상태 — 다음 단계를 시작하기 전에 처리한다")
        lines += [f"  {x}" for x in failed]
    if stuck:
        lines.append("\n다음에 할 일")
        lines += [f"  {x}" for x in stuck[:12]]
        if len(stuck) > 12:
            lines.append(f"  ... 그 밖에 {len(stuck) - 12}장")
    if not failed and not stuck:
        lines.append("\n모든 장이 마지막 게이트를 통과했다.")

    handoffs = state.get("handoffs") or {}
    waiting = [k for k, v in handoffs.items() if (v or {}).get("state") == "pending"]
    if waiting:
        lines.append(f"\n인계 대기: {', '.join(waiting)}")

    lines.append("\n작업은 cafe-book-conductor 스킬로 시작한다.")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
