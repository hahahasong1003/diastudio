#!/usr/bin/env python3
"""연작 변주 대장.

스물한 장이 같은 악보를 쓰되 소제목·키워드·잠언·인물은 장마다 전부 달라야
한다. 항목이 열한 종류이므로 사람의 기억으로 관리할 수 있는 양이 아니다.
이 대장이 조회·예약·확정의 세 단계로 중복을 막는다.

    python3 variation_ledger.py init --seed
    python3 variation_ledger.py check trend_keyword "고요 소비"
    python3 variation_ledger.py reserve trend_keyword "빈 그릇 소비" --chapter 22
    python3 variation_ledger.py commit --chapter 22
    python3 variation_ledger.py report --chapter 22
    python3 variation_ledger.py rename-impact --from 카브 --to 풀 --scan manuscript/
"""

import argparse
import difflib
import json
import os
import re
import sys

DEFAULT_LEDGER = "ledger.json"

FIELDS = {
    "space_name": "공간의 이름",
    "trend_keyword": "트렌드 키워드 (14악장)",
    "chronicle_aphorism": "연대기의 잠언 (17악장)",
    "coaching_subtitle": "코칭의 소제목 (15악장)",
    "travel_writer_title": "여행작가 고백의 제목 (11악장)",
    "anthropology_question": "인류학의 물음 (16악장)",
    "philosophy_question": "철학의 물음 (18악장)",
    "finale_line": "피날레의 한 문장 (19악장)",
    "regen_character_job": "지역재생 인물의 직업 (8악장)",
    "signature_menu": "시그니처 메뉴 (9악장)",
    "customer_quote": "핵심 고객의 인용문 (10악장)",
}

# 키워드에서 떼어 내고 줄기만 비교할 상투 접미
KEYWORD_SUFFIXES = ["소비", "사치", "구독", "원정", "재발견", "선물", "여행", "입장", "답장", "확인"]

DUP_THRESHOLD = 0.80
NEAR_THRESHOLD = 0.58

# 글자가 달라도 발상이 같은 것을 잡기 위한 뜻 묶음.
# 문자열 비교만으로는 '고요 소비'와 '정적 소비'를 구별하지 못한다.
CONCEPT_CLUSTERS = [
    {"고요", "정적", "침묵", "적막", "조용", "무음"},
    {"느림", "느린", "천천", "더딘", "지연", "늦은"},
    {"비움", "빈", "공백", "텅", "여백", "empty"},
    {"낯섦", "낯선", "생소", "이질", "이방"},
    {"발견", "탐색", "탐험", "찾기", "찾아"},
    {"안심", "안전", "편안", "안온"},
    {"돌봄", "보살", "기르", "키우"},
    {"조망", "전망", "풍경", "경관", "眺望"},
    {"손맛", "수작", "손길", "손으로"},
    {"과정", "여정", "경로", "도정"},
    {"높이", "눈높이", "고도", "층위"},
    {"기다림", "기다리", "대기", "지켜봄"},
    {"기록", "아카이브", "보관", "저장"},
    {"회복", "치유", "재생", "복원"},
]


def concept_of(value):
    """값이 속한 뜻 묶음의 번호들을 돌려준다."""
    norm = normalize(value)
    return {i for i, cluster in enumerate(CONCEPT_CLUSTERS)
            if any(term in norm for term in cluster)}


def suffix_of(value):
    norm = normalize(value)
    for suf in KEYWORD_SUFFIXES:
        if norm.endswith(suf):
            return suf
    return ""

SEED = {
    "space_name": ["알티튜드", "오리엔트", "룩스", "웨이브", "풀", "레인", "모스", "올드 그로스",
                   "버치", "오비트", "마스", "딥 스페이스", "잉크", "포스트", "아틀라스",
                   "그린하우스", "비하이브", "리버", "코트야드", "저스트 라이트", "실로"],
    "trend_keyword": ["한 뼘 사치", "세계관 입장", "과정 소비", "시간의 구독", "고요 소비",
                      "눈높이 소비", "조망 소비", "초압축 여행", "낯섦 소비", "밤하늘 원정",
                      "손맛 소비", "느린 답장", "시간차 선물", "떠나기 전 소비", "성장 소비",
                      "내력 소비", "계절 확인 소비", "발견 소비", "안심 소비", "내부 소비",
                      "궂은날의 재발견", "돌봄 소비", "비수기 소비", "핑계 소비"],
    "chronicle_aphorism": ["스며듦의 기록", "종착역에 도착하지 않는다", "등대", "파도",
                           "물이 빠진 수영장", "비", "이끼", "오래된 숲", "자작나무", "궤도",
                           "개척지", "별빛", "필사", "소인", "지도", "밭", "벌집", "강",
                           "숨은 안뜰", "일상", "저장고"],
    "regen_character_job": ["헌책방 주인", "사진관 노부부", "여인숙 주인", "열대어 가게 주인",
                            "수영 강사", "우산 수리집 노인", "분재 노인", "벌목공",
                            "숯 굽던 노인", "망원경 가게 노인", "미장이", "천체투영관 기사",
                            "식자공", "집배원", "표구사 장인", "화원 노인", "양봉 노인",
                            "나룻배 사공", "삼층 할머니", "하역 노동자"],
}


def normalize(text):
    text = re.sub(r"[\s​]+", "", text)
    text = re.sub(r"[^\w가-힣]", "", text)
    return text.lower()


def stem(field, value):
    """트렌드 키워드는 상투 접미를 떼고 줄기만 비교한다."""
    norm = normalize(value)
    if field == "trend_keyword":
        for suf in KEYWORD_SUFFIXES:
            if norm.endswith(suf) and len(norm) > len(suf):
                return norm[: -len(suf)]
    return norm


def similarity(field, a, b):
    full = difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()
    sa, sb = stem(field, a), stem(field, b)
    score = full
    if sa and sb:
        score = max(full, difflib.SequenceMatcher(None, sa, sb).ratio())

    # 뜻 묶음이 겹치면 글자가 달라도 같은 발상으로 본다.
    shared = concept_of(a) & concept_of(b)
    if shared:
        same_suffix = suffix_of(a) and suffix_of(a) == suffix_of(b)
        score = max(score, DUP_THRESHOLD + 0.02 if same_suffix else NEAR_THRESHOLD + 0.12)
    return score


def load(path):
    if not os.path.exists(path):
        return {"version": 1, "entries": {k: [] for k in FIELDS}}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("entries", {})
    for k in FIELDS:
        data["entries"].setdefault(k, [])
    return data


def save(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def find_matches(data, field, value):
    dups, nears = [], []
    for e in data["entries"].get(field, []):
        score = similarity(field, value, e["value"])
        if score >= DUP_THRESHOLD:
            dups.append((score, e))
        elif score >= NEAR_THRESHOLD:
            nears.append((score, e))
    dups.sort(key=lambda x: -x[0])
    nears.sort(key=lambda x: -x[0])
    return dups, nears


def describe(entry):
    where = f"{entry['chapter']}장" if entry.get("chapter") else entry.get("source", "출처 미상")
    return f"{entry['value']}  ({where}, {entry.get('state', 'committed')})"


def cmd_init(args):
    if os.path.exists(args.ledger) and not args.force:
        print(f"이미 있다: {args.ledger}. 덮어쓰려면 --force.", file=sys.stderr)
        return 1
    data = {"version": 1, "entries": {k: [] for k in FIELDS}}
    if args.seed:
        for field, values in SEED.items():
            for v in values:
                data["entries"][field].append(
                    {"value": v, "chapter": None, "state": "committed", "source": "1권"})
    save(args.ledger, data)
    total = sum(len(v) for v in data["entries"].values())
    print(f"대장을 만들었다: {args.ledger} (등록 {total}건)")
    return 0


def cmd_check(args):
    data = load(args.ledger)
    if args.field not in FIELDS:
        print(f"모르는 항목: {args.field}. 목록은 fields 명령으로 본다.", file=sys.stderr)
        return 2
    dups, nears = find_matches(data, args.field, args.value)
    print(f"[{FIELDS[args.field]}] \"{args.value}\"")
    if dups:
        print("\n  중복이다. 쓰지 않는다.")
        for score, e in dups:
            print(f"    {score:.2f}  {describe(e)}")
    if nears:
        print("\n  발상이 겹칠 수 있다. 글자가 달라도 뜻이 같으면 중복이다.")
        for score, e in nears:
            print(f"    {score:.2f}  {describe(e)}")
    if not dups and not nears:
        print("\n  겹치는 것이 없다. 예약해도 좋다.")
    return 1 if dups else 0


def cmd_reserve(args):
    data = load(args.ledger)
    if args.field not in FIELDS:
        print(f"모르는 항목: {args.field}", file=sys.stderr)
        return 2
    dups, nears = find_matches(data, args.field, args.value)
    if dups and not args.force:
        print("중복이라 예약하지 않았다:", file=sys.stderr)
        for score, e in dups:
            print(f"  {score:.2f}  {describe(e)}", file=sys.stderr)
        return 1
    for e in list(data["entries"][args.field]):
        if e.get("chapter") == args.chapter and e.get("state") == "reserved":
            data["entries"][args.field].remove(e)
            print(f"기존 예약을 대체한다: {e['value']}")
    data["entries"][args.field].append(
        {"value": args.value, "chapter": args.chapter, "state": "reserved"})
    save(args.ledger, data)
    print(f"예약: {args.chapter}장 / {FIELDS[args.field]} / {args.value}")
    for score, e in nears:
        print(f"  참고 — 발상이 가깝다 {score:.2f}: {describe(e)}")
    return 0


def cmd_commit(args):
    data = load(args.ledger)
    moved = []
    for field, entries in data["entries"].items():
        for e in entries:
            if e.get("state") != "reserved":
                continue
            if args.chapter is not None and e.get("chapter") != args.chapter:
                continue
            if args.field and field != args.field:
                continue
            e["state"] = "committed"
            moved.append((field, e))
    if not moved:
        print("확정할 예약이 없다.")
        return 0
    save(args.ledger, data)
    print(f"확정 {len(moved)}건:")
    for field, e in moved:
        print(f"  {e['chapter']}장  {FIELDS[field]}  {e['value']}")
    return 0


def cmd_release(args):
    data = load(args.ledger)
    dropped = []
    for field, entries in data["entries"].items():
        for e in list(entries):
            if e.get("state") == "reserved" and e.get("chapter") == args.chapter:
                entries.remove(e)
                dropped.append((field, e))
    save(args.ledger, data)
    print(f"예약 해제 {len(dropped)}건.")
    for field, e in dropped:
        print(f"  {FIELDS[field]}  {e['value']}")
    return 0


def cmd_report(args):
    data = load(args.ledger)
    pending = []
    for field, entries in sorted(data["entries"].items()):
        rows = entries
        if args.chapter is not None:
            rows = [e for e in rows if e.get("chapter") == args.chapter]
        if args.field and field != args.field:
            continue
        if not rows:
            continue
        print(f"\n## {FIELDS[field]}  ({len(rows)}건)")
        for e in rows:
            flag = " ← 예약, 미확정" if e.get("state") == "reserved" else ""
            print(f"  {describe(e)}{flag}")
            if e.get("state") == "reserved":
                pending.append((field, e))
    if args.chapter is not None:
        missing = [f for f in FIELDS
                   if not any(e.get("chapter") == args.chapter
                              for e in data["entries"].get(f, []))]
        if missing:
            print(f"\n## {args.chapter}장에 아직 값이 없는 항목")
            for f in missing:
                print(f"  {FIELDS[f]}")
    if pending:
        print(f"\n예약만 되고 확정되지 않은 값이 {len(pending)}건 있다. "
              "확정하지 않으면 대장이 원고와 어긋난다.")
    return 0


def cmd_fields(_args):
    for k, v in FIELDS.items():
        print(f"{k:24} {v}")
    return 0


def cmd_rename_impact(args):
    hits = []
    for root, _dirs, files in os.walk(args.scan):
        for name in sorted(files):
            if not name.endswith((".md", ".txt", ".json")):
                continue
            path = os.path.join(root, name)
            try:
                with open(path, encoding="utf-8") as fh:
                    for lineno, line in enumerate(fh, 1):
                        if args.old in line:
                            hits.append((path, lineno, line.strip()[:90]))
            except (OSError, UnicodeDecodeError):
                continue
    print(f"'{args.old}' → '{args.new}' 교체의 영향 범위: {len(hits)}곳")
    for path, lineno, text in hits:
        print(f"  {path}:{lineno}  {text}")
    if hits:
        print("\n본문뿐 아니라 부 도입, 차례, 다른 장의 언급, 대장까지 함께 고친다.")
        print("옛 이름은 book-state.json의 retired_names에 남긴다. 지우지 않는다.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="연작 변주 대장")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="대장 만들기")
    p.add_argument("--seed", action="store_true", help="1권의 기존 값을 함께 넣는다")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("check", help="중복 조회")
    p.add_argument("field"); p.add_argument("value")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("reserve", help="값 예약")
    p.add_argument("field"); p.add_argument("value")
    p.add_argument("--chapter", type=int, required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_reserve)

    p = sub.add_parser("commit", help="예약을 확정")
    p.add_argument("--chapter", type=int); p.add_argument("--field")
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser("release", help="예약 해제")
    p.add_argument("--chapter", type=int, required=True)
    p.set_defaults(func=cmd_release)

    p = sub.add_parser("report", help="대장 조회")
    p.add_argument("--chapter", type=int); p.add_argument("--field")
    p.set_defaults(func=cmd_report)

    sub.add_parser("fields", help="항목 목록").set_defaults(func=cmd_fields)

    p = sub.add_parser("rename-impact", help="공간명 교체의 영향 범위")
    p.add_argument("--from", dest="old", required=True)
    p.add_argument("--to", dest="new", required=True)
    p.add_argument("--scan", default=".")
    p.set_defaults(func=cmd_rename_impact)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
