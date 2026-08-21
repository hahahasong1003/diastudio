#!/usr/bin/env python3
"""원고 무결성 검사.

블록 대조, 한글 혼입, 깨진 글자, 코드 잔재, 옛 공간명 잔재를 확인한다.
한국어판과 영어판을 동일 구조로 유지하기 위한 기계 검사이며,
「최고의 경험, 최고의 카페」에서 실제로 유실과 잔재가 반복 발생했다.

    python3 manuscript_check.py --ko ko.md --en en.md --state book-state.json
    python3 manuscript_check.py --ko ko.md
    python3 manuscript_check.py --en en.md --hangul-only
"""

import argparse
import json
import os
import re
import sys

HANGUL = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣ]")
# U+FFFD 대체 문자와, UTF-8을 라틴1로 잘못 읽었을 때 나오는 전형적인 짝
MOJIBAKE = re.compile("�|[ÂÃâ][-¿]")
CODE_RESIDUE = re.compile(
    r"(<div|</div>|<span|</span>|\{\{|\}\}|&nbsp;|&lt;|&gt;|&amp;|\\u[0-9a-fA-F]{4}|<!--)")
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


class Report:
    def __init__(self):
        self.problems = []
        self.notes = []

    def fail(self, section, message, detail=""):
        self.problems.append((section, message, detail))

    def note(self, message):
        self.notes.append(message)

    def render(self):
        for msg in self.notes:
            print(msg)
        if not self.problems:
            print("\n검사를 모두 통과했다.")
            return 0
        print(f"\n통과하지 못한 항목 {len(self.problems)}건")
        for section, message, detail in self.problems:
            print(f"\n[{section}] {message}")
            if detail:
                lines = detail.splitlines()
                for line in lines[:20]:
                    print(f"    {line}")
                if len(lines) > 20:
                    print(f"    ... 그 밖에 {len(lines) - 20}줄")
        return 1


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def blocks(text):
    """빈 줄로 구분한 블록. 코드 펜스 안은 하나의 블록으로 본다."""
    out, buf, in_code = [], [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            buf.append(line)
            continue
        if not line.strip() and not in_code:
            if buf:
                out.append("\n".join(buf).strip())
                buf = []
            continue
        buf.append(line)
    if buf:
        out.append("\n".join(buf).strip())
    return [b for b in out if b]


def headings(text):
    out, in_code = [], False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING.match(line)
        if m:
            out.append((lineno, len(m.group(1)), m.group(2)))
    return out


def check_hangul(path, text, rep):
    hits, in_code = [], False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        found = HANGUL.findall(line)
        if found:
            sample = "".join(sorted(set(found)))[:20]
            hits.append(f"{path}:{lineno}  {sample}  |  {line.strip()[:70]}")
    if hits:
        rep.fail("한글 혼입", f"영어판에 한글 음절이 {len(hits)}줄 남아 있다.", "\n".join(hits))
    else:
        rep.note("한글 혼입 0건.")


def check_artifacts(path, text, rep):
    broken, residue = [], []
    for lineno, line in enumerate(text.splitlines(), 1):
        if MOJIBAKE.search(line):
            broken.append(f"{path}:{lineno}  {line.strip()[:70]}")
        m = CODE_RESIDUE.search(line)
        if m:
            residue.append(f"{path}:{lineno}  {m.group()}  |  {line.strip()[:60]}")
    if broken:
        rep.fail("깨진 글자", f"{path}에 깨진 글자가 {len(broken)}줄 있다.", "\n".join(broken))
    if residue:
        rep.fail("코드 잔재", f"{path}에 코드 잔재가 {len(residue)}줄 있다.", "\n".join(residue))
    if not broken and not residue:
        rep.note(f"{path}: 깨진 글자와 코드 잔재 없음.")


def check_legacy_names(path, text, names, rep):
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name in names:
            if name and name in line:
                hits.append(f"{path}:{lineno}  '{name}'  |  {line.strip()[:70]}")
    if hits:
        rep.fail("옛 공간명 잔재",
                 f"{path}에 교체된 공간명이 {len(hits)}곳 남아 있다.", "\n".join(hits))
    else:
        rep.note(f"{path}: 옛 공간명 잔재 없음.")


def check_parity(ko_path, ko, en_path, en, rep):
    kb, eb = blocks(ko), blocks(en)
    rep.note(f"블록 수 — 한국어판 {len(kb)}, 영어판 {len(eb)}.")
    if len(kb) != len(eb):
        rep.fail("블록 대조",
                 f"블록 수가 다르다. 한국어판 {len(kb)}, 영어판 {len(eb)} "
                 f"(차이 {abs(len(kb) - len(eb))}).",
                 "구조를 동일하게 유지한다. 문단을 합치거나 나눈 자리를 찾는다.")

    kh, eh = headings(ko), headings(en)
    rep.note(f"제목 수 — 한국어판 {len(kh)}, 영어판 {len(eh)}.")
    if len(kh) != len(eh):
        rep.fail("제목 대조", f"제목 수가 다르다. 한국어판 {len(kh)}, 영어판 {len(eh)}.", "")
        return
    mismatched = [
        f"{i + 1}번째 제목  한국어 {a[1]}단계 '{a[2][:30]}'  /  영어 {b[1]}단계 '{b[2][:30]}'"
        for i, (a, b) in enumerate(zip(kh, eh)) if a[1] != b[1]
    ]
    if mismatched:
        rep.fail("제목 단계 대조",
                 f"제목의 단계가 어긋난 자리가 {len(mismatched)}곳 있다.", "\n".join(mismatched))
    else:
        rep.note("제목 단계 일치.")


def check_state(state_path, rep):
    try:
        with open(state_path, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError) as exc:
        rep.fail("상태 파일", f"{state_path}를 읽을 수 없다: {exc}")
        return []

    backup = (state.get("backup") or {}).get("last")
    if not backup:
        rep.fail("백업", "book-state.json에 백업 기록이 없다.",
                 "작업 환경의 상태 회귀에 대비해 원고 백업본을 산출물과 함께 보관한다.")
    elif not os.path.exists(backup):
        rep.fail("백업", f"기록된 백업본이 실제로 없다: {backup}")
    else:
        rep.note(f"백업본 확인: {backup}")

    failed = [c.get("no") for c in state.get("chapters", [])
              if any(v == "failed" for v in (c.get("status") or {}).values())]
    if failed:
        rep.fail("게이트 상태", f"반려 상태인 장이 있다: {failed}",
                 "반려된 장을 처리하기 전에 다음 단계를 시작하지 않는다.")
    return state.get("retired_names", [])


def main():
    ap = argparse.ArgumentParser(description="원고 무결성 검사")
    ap.add_argument("--ko", help="한국어판 원고")
    ap.add_argument("--en", help="영어판 원고")
    ap.add_argument("--state", help="book-state.json")
    ap.add_argument("--legacy", help="옛 공간명을 쉼표로 구분해 직접 지정")
    ap.add_argument("--hangul-only", action="store_true", help="한글 혼입만 검사")
    args = ap.parse_args()

    if not args.ko and not args.en:
        ap.error("--ko 또는 --en 중 하나는 필요하다")

    rep = Report()
    retired = []
    if args.state:
        retired = check_state(args.state, rep)
    if args.legacy:
        retired = retired + [n.strip() for n in args.legacy.split(",") if n.strip()]

    ko = read(args.ko) if args.ko else None
    en = read(args.en) if args.en else None

    if en is not None:
        check_hangul(args.en, en, rep)
    if args.hangul_only:
        return rep.render()

    for path, text in ((args.ko, ko), (args.en, en)):
        if text is None:
            continue
        check_artifacts(path, text, rep)
        if retired:
            check_legacy_names(path, text, retired, rep)

    if ko is not None and en is not None:
        check_parity(args.ko, ko, args.en, en, rep)

    return rep.render()


if __name__ == "__main__":
    sys.exit(main())
