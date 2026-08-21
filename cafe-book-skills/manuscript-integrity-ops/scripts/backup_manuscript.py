#!/usr/bin/env python3
"""원고 백업과 상태 기록.

원고와 대장과 상태 파일을 한 벌로 묶어 백업하고, 백업 경로를
book-state.json에 기록한다. 기록하지 않으면 무결성 검사가
백업의 부재를 잡아내지 못한다.

    python3 backup_manuscript.py --state book-state.json
    python3 backup_manuscript.py --state book-state.json --label 6차개고
    python3 backup_manuscript.py --state book-state.json --list
"""

import argparse
import json
import os
import shutil
import sys
import time


def load_state(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_state(path, state):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def targets(state, state_path):
    book = state.get("book") or {}
    out = []
    for key in ("manuscript_ko", "manuscript_en", "ledger"):
        value = book.get(key)
        if value and os.path.exists(value):
            out.append(value)
        elif value:
            print(f"경고 — 기록된 파일이 없다: {value}", file=sys.stderr)
    out.append(state_path)
    return out


def cmd_list(backup_dir):
    if not os.path.isdir(backup_dir):
        print(f"백업 디렉터리가 없다: {backup_dir}")
        return 0
    stamps = sorted(d for d in os.listdir(backup_dir)
                    if os.path.isdir(os.path.join(backup_dir, d)))
    if not stamps:
        print("백업이 없다.")
        return 0
    print(f"백업 {len(stamps)}회차:")
    for stamp in stamps:
        files = sorted(os.listdir(os.path.join(backup_dir, stamp)))
        print(f"  {stamp}  ({len(files)}개)  {', '.join(files)}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="원고 백업")
    ap.add_argument("--state", default="book-state.json")
    ap.add_argument("--dir", default="backup", help="백업 디렉터리")
    ap.add_argument("--label", default="", help="회차 이름 (예: 6차개고)")
    ap.add_argument("--list", action="store_true", help="백업 목록만 본다")
    args = ap.parse_args()

    if args.list:
        return cmd_list(args.dir)

    if not os.path.exists(args.state):
        print(f"상태 파일이 없다: {args.state}", file=sys.stderr)
        return 2

    state = load_state(args.state)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    if args.label:
        stamp = f"{stamp}-{args.label}"
    dest = os.path.join(args.dir, stamp)
    os.makedirs(dest, exist_ok=True)

    copied = []
    for path in targets(state, args.state):
        shutil.copy2(path, os.path.join(dest, os.path.basename(path)))
        copied.append(os.path.basename(path))

    if not copied:
        print("백업할 파일이 없다. book-state.json의 경로를 확인한다.", file=sys.stderr)
        return 1

    marker = os.path.join(dest, os.path.basename(
        (state.get("book") or {}).get("manuscript_ko") or "manuscript.md"))
    state.setdefault("backup", {})
    state["backup"]["last"] = marker if os.path.exists(marker) else os.path.join(dest, copied[0])
    state["backup"]["dir"] = dest
    state["backup"]["policy"] = "매 회차 산출물과 함께. 옛 백업을 지우지 않는다."
    save_state(args.state, state)

    print(f"백업했다: {dest}")
    for name in copied:
        print(f"  {name}")
    print(f"\nbook-state.json의 backup.last를 갱신했다: {state['backup']['last']}")
    print("옛 백업은 지우지 않는다. 상태 회귀는 예고 없이 온다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
