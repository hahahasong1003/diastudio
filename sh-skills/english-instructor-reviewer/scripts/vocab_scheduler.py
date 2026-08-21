#!/usr/bin/env python3
"""간격 반복 단어장.

다시 보는 것이 아니라 다시 꺼내는 것이 기억을 만든다. 이 스크립트는
인출 성공 여부에 따라 다음에 꺼낼 날을 정한다.

    python3 vocab_scheduler.py init wordlist.txt
    python3 vocab_scheduler.py due                    # 오늘 꺼낼 단어 (뜻을 가린다)
    python3 vocab_scheduler.py due --direction ko     # 한국어를 보고 영어를 떠올린다
    python3 vocab_scheduler.py grade decision ok
    python3 vocab_scheduler.py grade prevail miss
    python3 vocab_scheduler.py stats

단어장 형식은 한 줄에 하나이며 세로줄로 나눈다.
    decision | 결정 | make a decision; reach a decision; a tough decision
뜻과 연어는 생략할 수 있다.
"""

import argparse
import datetime
import json
import os
import sys

DEFAULT_STORE = "vocab.json"

# 상자별 다음 복습까지의 날수. 마지막을 통과하면 졸업으로 본다.
INTERVALS = [1, 2, 4, 8, 16, 32]
GRADUATED = len(INTERVALS) + 1


def today(args):
    if getattr(args, "today", None):
        return datetime.date.fromisoformat(args.today)
    return datetime.date.today()


def load(path):
    if not os.path.exists(path):
        print(f"단어장이 없다: {path}. 먼저 init을 실행한다.", file=sys.stderr)
        sys.exit(2)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def parse_line(line):
    parts = [p.strip() for p in line.split("|")]
    word = parts[0]
    meaning = parts[1] if len(parts) > 1 else ""
    colls = []
    if len(parts) > 2 and parts[2]:
        colls = [c.strip() for c in parts[2].split(";") if c.strip()]
    return word, meaning, colls


def make_entry(word, meaning, colls, day):
    return {
        "word": word,
        "meaning": meaning,
        "collocations": colls,
        "box": 1,
        "due": day.isoformat(),
        "history": [],
    }


def find(data, word):
    for e in data["entries"]:
        if e["word"].lower() == word.lower():
            return e
    return None


def cmd_init(args):
    if os.path.exists(args.store) and not args.force:
        print(f"이미 있다: {args.store}. 덮어쓰려면 --force, 더하려면 add.", file=sys.stderr)
        return 1
    day = today(args)
    entries, skipped = [], 0
    with open(args.wordlist, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            word, meaning, colls = parse_line(raw)
            if not word:
                continue
            if any(e["word"].lower() == word.lower() for e in entries):
                skipped += 1
                continue
            entries.append(make_entry(word, meaning, colls, day))

    data = {"version": 1, "created": day.isoformat(), "entries": entries}
    save(args.store, data)

    no_coll = sum(1 for e in entries if not e["collocations"])
    print(f"단어장을 만들었다: {args.store} ({len(entries)}개)")
    if skipped:
        print(f"중복 {skipped}개를 건너뛰었다.")
    if no_coll:
        print(f"\n연어가 없는 단어가 {no_coll}개다. 단어만 외우면 뜻은 알아도 쓰지 못한다.")
        print("가능하면 'decision | 결정 | make a decision; a tough decision' 형태로 채운다.")
    return 0


def cmd_add(args):
    data = load(args.store)
    day = today(args)
    added = 0
    for raw in args.items:
        word, meaning, colls = parse_line(raw)
        if not word:
            continue
        if find(data, word):
            print(f"이미 있다: {word}")
            continue
        data["entries"].append(make_entry(word, meaning, colls, day))
        added += 1
    save(args.store, data)
    print(f"{added}개를 더했다. 전체 {len(data['entries'])}개.")
    return 0


def cmd_due(args):
    data = load(args.store)
    day = today(args)
    due = [e for e in data["entries"]
           if e["box"] <= len(INTERVALS)
           and datetime.date.fromisoformat(e["due"]) <= day]
    due.sort(key=lambda e: (e["due"], e["box"]))
    if args.limit:
        due = due[: args.limit]

    if not due:
        print("오늘 꺼낼 단어가 없다.")
        return 0

    print(f"오늘 꺼낼 단어 {len(due)}개.")
    if args.direction == "ko":
        print("한국어를 보고 영어를 떠올린다. 이 방향이 되는 단어만 작문과 발화에서 나온다.\n")
    else:
        print("영어를 보고 뜻과 연어를 떠올린다.\n")

    for i, e in enumerate(due, 1):
        if args.direction == "ko":
            prompt = e["meaning"] or "(뜻이 비어 있음)"
        else:
            prompt = e["word"]
        print(f"{i:3d}. {prompt}    [상자 {e['box']}]")
        if args.show:
            answer = e["word"] if args.direction == "ko" else (e["meaning"] or "-")
            print(f"      답: {answer}")
            for c in e["collocations"]:
                print(f"      - {c}")

    if not args.show:
        print("\n답을 보려면 --show를 붙인다. 먼저 스스로 떠올린 뒤에 본다.")
    print("\n채점: vocab_scheduler.py grade <단어> ok|miss")
    return 0


def cmd_grade(args):
    data = load(args.store)
    day = today(args)
    e = find(data, args.word)
    if not e:
        print(f"단어장에 없다: {args.word}", file=sys.stderr)
        return 2

    before = e["box"]
    if args.result == "ok":
        e["box"] = min(e["box"] + 1, GRADUATED)
    else:
        e["box"] = 1

    if e["box"] > len(INTERVALS):
        e["due"] = "-"
        print(f"{e['word']}: 졸업했다. 자동화 층에 들어갔다.")
    else:
        gap = INTERVALS[e["box"] - 1]
        e["due"] = (day + datetime.timedelta(days=gap)).isoformat()
        moved = "올라감" if e["box"] > before else "처음으로"
        print(f"{e['word']}: 상자 {before} → {e['box']} ({moved}). 다음은 {e['due']}.")

    e["history"].append({"date": day.isoformat(), "result": args.result})

    misses = sum(1 for h in e["history"] if h["result"] == "miss")
    if misses >= 3:
        print(f"  {e['word']}은 {misses}번 떨어졌다. 목록에서 빼고 따로 다루는 것을 고려한다.")
        print("  대개 뜻이 추상적이거나 아직 이른 단어다.")

    save(args.store, data)
    return 0


def cmd_stats(args):
    data = load(args.store)
    day = today(args)
    entries = data["entries"]
    if not entries:
        print("단어장이 비어 있다.")
        return 0

    boxes = {}
    for e in entries:
        boxes[e["box"]] = boxes.get(e["box"], 0) + 1
    graduated = boxes.get(GRADUATED, 0)
    due_today = sum(1 for e in entries
                    if e["box"] <= len(INTERVALS)
                    and datetime.date.fromisoformat(e["due"]) <= day)

    print(f"전체 {len(entries)}개, 졸업 {graduated}개 ({graduated * 100 // len(entries)}%)")
    print(f"오늘 꺼낼 것 {due_today}개\n")

    print("상자별 분포")
    for box in range(1, GRADUATED + 1):
        n = boxes.get(box, 0)
        if box <= len(INTERVALS):
            label = f"상자 {box} ({INTERVALS[box - 1]}일)"
        else:
            label = "졸업"
        bar = "#" * min(n, 40)
        print(f"  {label:14} {n:4d}  {bar}")

    repeat = [e for e in entries
              if sum(1 for h in e["history"] if h["result"] == "miss") >= 2]
    if repeat:
        print(f"\n두 번 이상 떨어진 단어 {len(repeat)}개")
        for e in repeat[:15]:
            misses = sum(1 for h in e["history"] if h["result"] == "miss")
            print(f"  {e['word']} ({misses}회)")
        print("이 단어들은 목록에서 빼고 따로 다룬다.")

    if due_today > 60:
        print(f"\n오늘 복습이 {due_today}개다. 하루치를 넘기면 그날 무너진다.")
        print("새 단어를 며칠 멈추고 밀린 것부터 비운다.")

    no_coll = sum(1 for e in entries if not e["collocations"])
    if no_coll:
        print(f"\n연어가 비어 있는 단어 {no_coll}개. 단어만 외우면 생산 층으로 올라가지 않는다.")

    print("\n이 숫자들보다 중요한 것이 하나 있다. 이번 주에 외운 단어가")
    print("학습자의 작문과 발화에 실제로 나왔는가. 그것이 0이면 수용 층에만 쌓이고 있다.")
    return 0


def cmd_list(args):
    data = load(args.store)
    entries = data["entries"]
    if args.box:
        entries = [e for e in entries if e["box"] == args.box]
    entries.sort(key=lambda e: (e["box"], e["word"].lower()))
    for e in entries:
        colls = "; ".join(e["collocations"])
        print(f"[{e['box']}] {e['word']:20} {e['meaning']:16} {colls}")
    print(f"\n{len(entries)}개.")
    return 0


def main():
    # 공통 옵션은 하위 명령 뒤에 오게 한다. 앞뒤 어디에 붙일지 헷갈리지 않는다.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--store", default=DEFAULT_STORE)
    common.add_argument("--today", help="오늘 날짜를 지정한다 (YYYY-MM-DD)")

    ap = argparse.ArgumentParser(description="간격 반복 단어장")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="단어장 만들기", parents=[common])
    p.add_argument("wordlist")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add", help="단어 더하기", parents=[common])
    p.add_argument("items", nargs="+")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("due", help="오늘 꺼낼 단어", parents=[common])
    p.add_argument("--direction", choices=["en", "ko"], default="en",
                   help="ko는 한국어를 보고 영어를 떠올린다")
    p.add_argument("--show", action="store_true", help="답을 함께 본다")
    p.add_argument("--limit", type=int)
    p.set_defaults(func=cmd_due)

    p = sub.add_parser("grade", help="인출 결과를 기록", parents=[common])
    p.add_argument("word")
    p.add_argument("result", choices=["ok", "miss"])
    p.set_defaults(func=cmd_grade)

    sub.add_parser("stats", help="진행 상황", parents=[common]).set_defaults(func=cmd_stats)

    p = sub.add_parser("list", help="단어 목록", parents=[common])
    p.add_argument("--box", type=int)
    p.set_defaults(func=cmd_list)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
