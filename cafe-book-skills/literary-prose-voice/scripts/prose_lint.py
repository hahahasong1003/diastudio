#!/usr/bin/env python3
"""문학 산문 금지 패턴 검사기.

「최고의 경험, 최고의 카페」의 문체 규범을 기계로 검사한다. 사람의 눈이
반복해서 놓친 패턴만 담았다. 규범 맞춤법 검사가 아니다 — 그것은
korean-copyedit-proofreader가 맡는다.

    python3 prose_lint.py 원고.md
    python3 prose_lint.py manuscript/ --format json
    python3 prose_lint.py 원고.md --only error
"""

import argparse
import json
import os
import re
import sys

ERROR = "error"
WARN = "warn"

# (규칙 id, 심각도, 정규식, 설명, 고치는 방향)
RULES = [
    # 수동태
    ("passive-double", ERROR,
     r"(보여|불려|쓰여|잊혀|놓여|모여|나뉘어|짜여|닫혀|읽혀|되어|뒤덮혀)(지|진|져|졌|질|짐)",
     "이중 피동이다. 한국어에 수동태를 쓰지 않는다.",
     "능동으로 바꾼다. '보여진다' → '보인다'."),
    ("passive-jyeo", WARN,
     r"[가-힣]져\s*있(다|었|는)",
     "피동 표현이다. 능동으로 바꿀 수 있는지 확인한다.",
     "'높여져 있다' → '높였다'."),
    ("passive-by", WARN,
     r"에\s*의(해|하여)\s",
     "번역투 피동 구문이다.",
     "행위자를 주어로 세운다."),

    # 방어적 사족 (가장 자주 재발하는 오류)
    ("defensive-mullon", WARN,
     r"(^|[.!?」』\s])물론\s",
     "방어적 사족일 수 있다. 지적을 의식한 대비 구문인지 확인한다.",
     "독자가 '이게 왜 갑자기 나왔지?' 하면 지운다."),
    ("defensive-contrast", ERROR,
     r"(그렇다고\s*해서|그 어느 곳도|다시 말하지만|앞서 말했듯|오해가 없도록|굳이 말하자면|말할 것도 없이)",
     "방어적 사족이다. 교정의 흔적을 원고에 남기지 않는다.",
     "문장째 지운다. 대비로 방어하지 않는다."),
    ("defensive-negation", WARN,
     r"[^.!?\n]{0,30}것은\s*아니다",
     "부정으로 방어하는 구문일 수 있다.",
     "긍정으로 말할 수 있으면 긍정으로 쓴다."),

    # 과잉 강조 · 과잉 조심
    ("overclaim-experience", ERROR,
     r"경험해\s*(보지|본\s*적)\s*(못|없)|상상도\s*(못|하지)|단언컨대|두말할\s*나위",
     "'당신은 이걸 경험해 보지 못했을 것' 류의 반복 강조다.",
     "강조하지 말고 장면으로 보여 준다."),
    ("hedge-feeling", WARN,
     r"(듯한\s*느낌|것\s*같은\s*느낌|느낌이\s*드는\s*듯)",
     "과잉 조심의 표시다.",
     "단정하거나 장면으로 대체한다."),
    ("weak-intensifier", WARN,
     r"(매우|굉장히|무척|참으로|대단히|몹시|너무나|정말이지)\s",
     "부사가 동사를 약하게 한다.",
     "동사를 강한 것으로 바꾸고 부사를 지운다."),

    # 허구 노출
    ("fiction-exposure", ERROR,
     r"(가상의|상상의\s*공간|실재하지\s*않|실제로\s*존재하지\s*않|지어낸|검색해도)",
     "허구임을 알리는 표현이다. 공간들은 브랜드로서 실재하듯 서술한다.",
     "문장째 지운다."),

    # 복장 언급
    ("uniform-mention", ERROR,
     r"(제복|유니폼|앞치마|옷차림|복장)",
     "직원의 복장을 언급하지 않는다. '제복은 없다'는 부정형도 위반이다.",
     "지운다. 목례 하나로 환대를 완성한다."),

    # 현학적 · 사장된 어휘
    ("archaic-lexicon", ERROR,
     r"(유백색|등롱|법랑|선구점|벽감|시보(?![가-힣])|스크립토리움|카토그라피아)",
     "현학적이거나 사장된 어휘다.",
     "우윳빛, 초롱, 머그잔처럼 일상어로 푼다."),
    ("loanword-transliteration", ERROR,
     r"(캐빈|오버헤드\s*빈|컨셉(?!트))",
     "불필요한 외래어 음차다.",
     "기내, 짐칸, 콘셉트로 쓴다."),
    ("boxy-space", WARN,
     r"(네모난\s*방|상자\s*같|상자처럼|상자\s*모양)",
     "일상적이지 않은 공간 표현이다.",
     "그 공간에 맞는 실제 형태로 묘사한다."),
]

COMPILED = [(rid, sev, re.compile(pat), msg, fix) for rid, sev, pat, msg, fix in RULES]

# 문장이 서술어로 맺었는지 판정할 때 허용하는 마지막 음절
SENTENCE_ENDINGS = set("다라까요오자지죠네군걸야니세소마련")
SKIP_LINE = re.compile(r"^\s*(\||```|<!--|---\s*$|#{1,6}\s)")
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
PREFIXED_HEADING = re.compile(r"^#{1,6}\s+[^:：\n]{1,14}[:：]\s*\S")
SENTENCE_SPLIT = re.compile(r"[^.!?…]*[.!?…]+[\"'」』)\]]*")


def check_incomplete_sentences(line):
    """명사로 끊긴 미완결 문장을 찾는다."""
    hits = []
    for m in SENTENCE_SPLIT.finditer(line):
        sent = m.group().strip()
        if not sent or len(sent) < 4:
            continue
        if sent.endswith(("!", "?", "…")) or "?" in sent[-3:] or "!" in sent[-3:]:
            continue
        body = sent.rstrip("\"'」』)]").rstrip()
        if not body.endswith("."):
            continue
        last = body[:-1].rstrip()
        if not last:
            continue
        ch = last[-1]
        if not ("가" <= ch <= "힣"):
            continue  # 숫자·로마자·약물로 끝나면 판정하지 않는다
        if ch not in SENTENCE_ENDINGS:
            hits.append((m.start() + 1, sent[-24:]))
    return hits


def lint_text(path, text):
    findings = []
    in_code = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        if PREFIXED_HEADING.match(line):
            findings.append(dict(
                path=path, line=lineno, col=1, severity=WARN, rule="heading-prefix",
                text=line.strip()[:60],
                message="'○○○: ○○○' 형태의 접두부 소제목이다.",
                fix="접두부를 떼고 장면을 예고하는 본제만 단다."))

        for rid, sev, rx, msg, fix in COMPILED:
            for m in rx.finditer(line):
                findings.append(dict(
                    path=path, line=lineno, col=m.start() + 1, severity=sev, rule=rid,
                    text=m.group().strip(), message=msg, fix=fix))

        if not SKIP_LINE.match(line):
            for col, snippet in check_incomplete_sentences(line):
                findings.append(dict(
                    path=path, line=lineno, col=col, severity=WARN, rule="incomplete-sentence",
                    text=snippet,
                    message="명사로 끊긴 미완결 문장일 수 있다.",
                    fix="서술어로 맺는다. '이 집의 법도.' → '이 집의 법도다.'"))
    return findings


def collect(target):
    if os.path.isfile(target):
        return [target]
    out = []
    for root, _dirs, files in os.walk(target):
        for f in sorted(files):
            if f.endswith((".md", ".txt")):
                out.append(os.path.join(root, f))
    return out


def main():
    ap = argparse.ArgumentParser(description="문학 산문 금지 패턴 검사")
    ap.add_argument("targets", nargs="+", help="파일 또는 디렉터리")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--only", choices=["error", "warn", "all"], default="all")
    args = ap.parse_args()

    findings = []
    for target in args.targets:
        for path in collect(target):
            try:
                with open(path, encoding="utf-8") as fh:
                    findings.extend(lint_text(path, fh.read()))
            except (OSError, UnicodeDecodeError) as exc:
                print(f"읽을 수 없음: {path} ({exc})", file=sys.stderr)

    if args.only == "error":
        findings = [f for f in findings if f["severity"] == ERROR]
    elif args.only == "warn":
        findings = [f for f in findings if f["severity"] == WARN]

    findings.sort(key=lambda f: (f["path"], f["line"], f["col"]))
    errors = sum(1 for f in findings if f["severity"] == ERROR)
    warns = len(findings) - errors

    if args.format == "json":
        print(json.dumps({"errors": errors, "warnings": warns, "findings": findings},
                         ensure_ascii=False, indent=2))
    else:
        for f in findings:
            mark = "오류" if f["severity"] == ERROR else "경고"
            print(f"{f['path']}:{f['line']}:{f['col']}  [{mark}] {f['rule']}")
            print(f"    걸린 것: {f['text']}")
            print(f"    이유: {f['message']}")
            print(f"    방향: {f['fix']}")
        print(f"\n오류 {errors}건, 경고 {warns}건.")
        if errors:
            print("오류가 남아 있으면 문체 게이트를 통과시키지 않는다.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
