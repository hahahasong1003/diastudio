#!/usr/bin/env python3
"""한국어 화자의 전형적인 영작문 오류 검사기.

모국어 간섭에서 반복해서 나오는 오류만 담았다. 문법 검사기가 아니라
교사의 첨삭 보조 도구이므로, 각 지적에 교실에서 쓸 설명을 함께 낸다.

    python3 learner_error_lint.py essay.txt
    python3 learner_error_lint.py essays/ --format json
    python3 learner_error_lint.py essay.txt --code     # 간접 교정용 (답을 주지 않는다)

스크립트가 잡는 것은 전형적인 오류뿐이다. 논지와 구조와 어조는 사람이 본다.
"""

import argparse
import json
import os
import re
import sys

ERROR = "error"
WARN = "warn"

# (규칙 id, 오류 코드, 심각도, 정규식, 무엇이 문제인가, 교실에서 어떻게 말하는가)
RULES = [
    ("art-be-job", "ART", ERROR,
     r"\b(I|You|He|She|We|They)\s+(am|is|are|was|were)\s+"
     r"(student|teacher|doctor|nurse|engineer|lawyer|writer|singer|manager|"
     r"designer|programmer|researcher|artist|driver|cook|soldier)\b",
     "셀 수 있는 단수 명사 앞에 관사가 빠졌다.",
     "직업을 말할 때는 'a/an'을 붙인다. 한국어에는 관사가 없어서 가장 자주 빠지는 자리다."),

    ("art-generic-the", "ART", WARN,
     r"\bThe\s+(life|love|nature|society|history|music|art|science|education|"
     r"technology|happiness|freedom)\s+(is|was|has)\b",
     "부류 전체를 가리키는데 'the'가 붙었다.",
     "'Life is short.' 총칭은 무관사다. 특정한 하나를 가리킬 때만 the를 쓴다."),

    ("num-uncountable-plural", "NUM", ERROR,
     r"\b(informations|advices|equipments|furnitures|homeworks|knowledges|"
     r"luggages|baggages|evidences|feedbacks|softwares|hardwares|slangs)\b",
     "불가산 명사를 복수로 만들었다.",
     "세고 싶으면 'a piece of information'처럼 단위를 빌린다."),

    ("num-many-uncountable", "NUM", ERROR,
     r"\bmany\s+(information|advice|equipment|furniture|homework|knowledge|"
     r"luggage|money|research|evidence|feedback|software|progress|traffic)\b",
     "불가산 명사에 many를 썼다.",
     "much를 쓰거나 'a lot of'로 간다. a lot of는 양쪽에 다 쓸 수 있어 안전하다."),

    ("t-perfect-past", "T", ERROR,
     r"\b(have|has|haven't|hasn't)\s+(been|gone|finished|done|seen|visited|met|"
     r"come|made|taken|given|written|read|eaten|bought|sent|told|said|got|gotten|"
     r"started|studied|worked|lived|played|watched|learned|learnt|graduated|"
     r"moved|joined|left)\b[^.!?]{0,50}?\b(yesterday|last\s+\w+|"
     r"\d+\s+(?:days?|weeks?|months?|years?)\s+ago|\bago)\b",
     "현재완료에 시점 부사가 붙었다.",
     "언제인지를 말하면 단순과거다. 현재완료는 '지금 어떤 상태인가'를 말할 때 쓴다."),

    ("t-stative-progressive", "T", WARN,
     r"\b(am|is|are|was|were)\s+(knowing|believing|wanting|needing|liking|"
     r"loving|hating|owning|belonging|understanding|preferring)\b",
     "상태동사를 진행형으로 썼다.",
     "know, want, like 같은 상태동사는 진행형을 쓰지 않는다."),

    ("prep-discuss-about", "PREP", ERROR,
     r"\bdiscuss(es|ed|ing)?\s+about\b",
     "discuss는 전치사를 삼킨 동사다.",
     "discuss the issue. 한국어 '~에 대해'를 about으로 옮기면 안 되는 동사군이 있다."),

    ("prep-swallowed", "PREP", ERROR,
     r"\b(marry|married|marrying)\s+with\b|\bmention(s|ed|ing)?\s+about\b|"
     r"\bcontact(s|ed|ing)?\s+(to|with)\s+(him|her|me|us|them|you)\b|"
     r"\benter(s|ed|ing)?\s+into\s+the\s+(room|building|house|office|classroom)\b|"
     r"\banswer(s|ed|ing)?\s+to\s+the\s+questions?\b|"
     r"\battend(s|ed|ing)?\s+to\s+the\s+(meeting|class|conference|lecture|ceremony)\b|"
     r"\bjoin(s|ed|ing)?\s+to\s+the\b|\bapproach(es|ed|ing)?\s+to\s+the\b|"
     r"\bcall(s|ed|ing)?\s+to\s+(you|him|her|me|us|them)\b",
     "전치사를 삼킨 동사에 전치사를 붙였다.",
     "marry, mention, contact, enter, answer, attend, join, approach, call은 "
     "목적어를 바로 받는다."),

    ("prep-explain-me", "PREP", ERROR,
     r"\b(explain|suggest|describe|announce|propose|introduce)\s+"
     r"(me|him|her|us|them)\b",
     "이 동사들은 사람을 바로 받지 못한다.",
     "explain the rule TO me. give/send와 달리 4형식을 쓰지 못하는 동사군이다."),

    ("sv-third-person", "SV", ERROR,
     r"\b(He|She|It|he|she|it)\s+(go|have|do|say|make|take|come|know|want|need|"
     r"like|think|work|live|study|play|watch|seem|look|feel|give|get|find|tell)\b",
     "3인칭 단수 주어에 동사원형이 왔다.",
     "he goes, she has. 한국어에는 주어에 따른 동사 변화가 없어 놓치기 쉽다."),

    ("wo-indirect-question", "WO", ERROR,
     r"\b(know|wonder|ask|asked|tell|understand|remember|forget)\s+"
     r"(what|where|when|why|who|how)\s+(is|are|was|were|do|does|did)\b",
     "간접의문문의 어순이 의문문 그대로다.",
     "I know what this is. 문장 안에 들어가면 평서문 어순으로 돌아온다."),

    ("ro-comma-splice", "RO", WARN,
     r"\w+,\s+(however|therefore|moreover|thus|furthermore|nevertheless|"
     r"consequently|otherwise|besides|hence)\s*,?\s+[a-z]",
     "접속부사를 접속사처럼 썼다.",
     "however는 부사다. 앞에 마침표나 세미콜론이 온다. 접속사는 and, but, so, "
     "because, although뿐이다."),

    ("double-subject", "WW", ERROR,
     r"\b(My|His|Her|Their|Our|The)\s+(friend|father|mother|brother|sister|"
     r"teacher|boss|son|daughter|professor|colleague|neighbor|neighbour)\s+"
     r"(he|she|they)\s+(is|are|was|were|has|have|does|do)\b",
     "주어가 두 번 나왔다.",
     "영어 문장에는 주어가 하나 있고 하나만 있다. 한국어의 이중 주어 구조가 옮겨 온 것이다."),

    ("konglish", "WW", ERROR,
     r"\bhand\s?phone\b|\bskinship\b|\beye\s+shopping\b|\bafter\s+service\b|"
     r"\bremocon\b|\bsel\s?ca\b|\bback\s+number\b|\bopen\s+car\b|\bSNS\b|"
     r"\bofficetel\b|\bone\s?shot\b",
     "콩글리시다.",
     "이건 한국어 단어다. 틀린 한국어가 아니라 영어가 아닐 뿐이라고 말해 준다."),

    ("konglish-fighting", "WW", WARN,
     r"\bFighting[!.]|\bfighting!",
     "응원의 'Fighting!'은 영어가 아니다.",
     "You can do it! / Good luck! / Go for it!"),

    ("awk-according-to-me", "AWK", ERROR,
     r"\bAccording to me\b|\baccording to me\b",
     "'According to'는 자기 자신에게 쓰지 않는다.",
     "In my opinion / In my view / I would argue."),

    ("rep-opinion-doubled", "REP", WARN,
     r"\bIn my opinion,?\s+I think\b",
     "의견 표시가 겹쳤다.",
     "둘 중 하나만 남긴다."),

    ("sp-common", "SP", ERROR,
     r"\b(recieve[ds]?|seperate[ds]?|definately|occured|embarass(ed|ing)?|"
     r"accomodate[ds]?|neccessary|begining|writting|untill|alot|becuase|"
     r"thier|arguement|enviroment|goverment|independant|occassion|priviledge|"
     r"publically|recomend(ed|s)?|refered|succesful|tommorow|wierd|"
     r"grammer|responsability|oppurtunity)\b",
     "철자 오류다.",
     "학습자가 반복해서 틀리는 철자는 따로 목록을 만들어 단어장에 넣는다."),

    ("punc-space-before", "PUNC", WARN,
     r"\s+[,.!?;:](\s|$)",
     "문장부호 앞에 공백이 있다.",
     "영어는 문장부호를 앞 단어에 붙이고 뒤에 공백을 둔다."),

    ("cap-i", "PUNC", ERROR,
     r"(?<![A-Za-z'])i(?=[\s,.!?;:'])",
     "1인칭 'I'를 소문자로 썼다.",
     "영어에서 I는 언제나 대문자다."),
]

COMPILED = [(rid, code, sev, re.compile(pat), what, how)
            for rid, code, sev, pat, what, how in RULES]

# 3인칭 단수 규칙에서 앞에 조동사가 오면 동사원형이 정상이므로 건너뛴다
SV_SKIP_BEFORE = {
    "does", "doesn't", "did", "didn't", "do", "don't", "to", "will", "won't",
    "can", "can't", "cannot", "could", "should", "shouldn't", "would", "must",
    "may", "might", "let", "make", "makes", "made", "help", "helps", "and", "or",
}

# 문서 전체를 보고 세는 규칙: (id, 코드, 정규식, 한계, 무엇이, 교실에서)
COUNT_RULES = [
    ("rep-i-think", "REP", re.compile(r"\bI think\b", re.I), 3,
     "'I think'가 너무 자주 나온다.",
     "학습자에게 직접 세게 한 뒤 하나만 남기고 지우게 한다. 문장이 단호해지는 것을 "
     "스스로 본다."),
    ("rep-very", "REP", re.compile(r"\bvery\b", re.I), 5,
     "'very'가 너무 자주 나온다.",
     "very + 약한 형용사를 강한 형용사 하나로 바꾼다. very big → huge."),
    ("rep-there-is", "REP", re.compile(r"\bthere (is|are|was|were)\b", re.I), 4,
     "'There is/are'가 너무 자주 나온다.",
     "실제 주어를 문장 앞으로 끌어낸다."),
    ("rep-nowadays", "REP", re.compile(r"\bnowadays\b", re.I), 2,
     "'Nowadays'가 너무 자주 나온다.",
     "Today, In recent years로 바꾸거나 그냥 지운다."),
    ("rep-and-so-on", "REP", re.compile(r"\b(and so on|etc\.)", re.I), 2,
     "'and so on / etc.'가 너무 자주 나온다.",
     "구체적으로 나열하거나 지운다. 영어 논설문에서 약하게 읽힌다."),
]


def preceding_word(line, start):
    before = line[:start].rstrip()
    if not before:
        return ""
    return re.split(r"[^\w']+", before)[-1].lower()


def lint_text(path, text):
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for rid, code, sev, rx, what, how in COMPILED:
            for m in rx.finditer(line):
                if rid == "sv-third-person" and preceding_word(line, m.start()) in SV_SKIP_BEFORE:
                    continue
                findings.append(dict(
                    path=path, line=lineno, col=m.start() + 1, rule=rid, code=code,
                    severity=sev, text=m.group().strip(), what=what, how=how))

    for rid, code, rx, limit, what, how in COUNT_RULES:
        hits = list(rx.finditer(text))
        if len(hits) <= limit:
            continue
        upto = text[: hits[limit].start()]
        findings.append(dict(
            path=path, line=upto.count("\n") + 1, col=1, rule=rid, code=code,
            severity=WARN, text=f"{hits[0].group()} ... 총 {len(hits)}회",
            what=what, how=how))

    findings.sort(key=lambda f: (f["line"], f["col"]))
    return findings


def collect(target):
    if os.path.isfile(target):
        return [target]
    out = []
    for root, _dirs, files in os.walk(target):
        for f in sorted(files):
            if f.endswith((".txt", ".md")):
                out.append(os.path.join(root, f))
    return out


def render_code_sheet(path, text, findings):
    """간접 교정용. 오류의 위치와 종류만 표시하고 답은 주지 않는다."""
    by_line = {}
    for f in findings:
        by_line.setdefault(f["line"], []).append(f)

    print(f"=== {path} ===")
    print("아래 표시된 자리를 스스로 고쳐 보세요. 코드의 뜻은 오류 코드표를 봅니다.\n")
    for lineno, line in enumerate(text.splitlines(), 1):
        print(f"{lineno:4d} | {line}")
        hits = by_line.get(lineno)
        if not hits:
            continue
        # 각 코드를 제 자리 아래에 놓는다. 겹치면 줄을 하나 더 쓴다.
        pending = sorted(hits, key=lambda h: h["col"])
        while pending:
            row, leftover, cursor = [], [], 0
            for h in pending:
                start = h["col"] - 1
                label = f"^{h['code']}"
                if start < cursor:
                    leftover.append(h)
                    continue
                row.append(" " * (start - cursor) + label)
                cursor = start + len(label) + 1
            print(f"     | {''.join(row)}")
            pending = leftover

    counts = {}
    for f in findings:
        counts[f["code"]] = counts.get(f["code"], 0) + 1
    if counts:
        summary = ", ".join(f"{c} {n}건" for c, n in sorted(counts.items()))
        print(f"\n표시된 오류: {summary}")
        print("고친 뒤 다시 검사해 보세요.")
    else:
        print("\n표시된 오류가 없습니다.")


def main():
    ap = argparse.ArgumentParser(description="한국어 화자의 영작문 오류 검사")
    ap.add_argument("targets", nargs="+", help="파일 또는 디렉터리")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--code", action="store_true",
                    help="간접 교정용. 오류 코드만 표시하고 답을 주지 않는다")
    ap.add_argument("--only", choices=["error", "warn", "all"], default="all")
    args = ap.parse_args()

    all_findings, errors = [], 0
    for target in args.targets:
        for path in collect(target):
            try:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError) as exc:
                print(f"읽을 수 없음: {path} ({exc})", file=sys.stderr)
                continue

            findings = lint_text(path, text)
            if args.only == "error":
                findings = [f for f in findings if f["severity"] == ERROR]
            elif args.only == "warn":
                findings = [f for f in findings if f["severity"] == WARN]

            if args.code:
                render_code_sheet(path, text, findings)
                print()
            all_findings.extend(findings)

    errors = sum(1 for f in all_findings if f["severity"] == ERROR)
    warns = len(all_findings) - errors

    if args.format == "json":
        print(json.dumps({"errors": errors, "warnings": warns,
                          "findings": all_findings}, ensure_ascii=False, indent=2))
    elif not args.code:
        for f in all_findings:
            mark = "오류" if f["severity"] == ERROR else "점검"
            print(f"{f['path']}:{f['line']}:{f['col']}  [{mark}] {f['code']}  ({f['rule']})")
            print(f"    걸린 것: {f['text']}")
            print(f"    무엇이: {f['what']}")
            print(f"    교실에서: {f['how']}")
        print(f"\n오류 {errors}건, 점검 {warns}건.")
        if all_findings:
            print("한 번에 세 가지까지만 지적한다. 이해를 막는 것, 반복되는 것, "
                  "목표에 직결되는 것 순으로 고른다.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
