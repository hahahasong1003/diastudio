---
name: manuscript-integrity-ops
description: 한국어판과 영어판을 동일 구조로 유지하고 원고의 무결성을 기계로 확인하며 유실을 막을 때 사용한다. 블록 수와 제목 단계 대조, 영어판의 한글 음절 혼입 검사, 깨진 글자와 코드 잔재 검사, 교체된 옛 공간명의 잔재 추적, 백업 규율, 공간명 교체 시의 전파 절차, 그리고 docx·pdf 산출물 빌드를 다룬다. 사용자가 "빌드해 줘", "검증해 줘", "블록 수 맞나", "한글 섞였는지 봐 줘", "옛 이름 남았나", "백업해 줘", "워드로 뽑아 줘", "출간 파일 만들어 줘"라고 하거나, 원고 작업 회차를 마치려 하거나, 이중언어판을 대조해야 하면 반드시 이 스킬을 쓴다. 작업 환경의 상태 회귀로 원고가 여러 차례 유실된 적이 있으므로 이 단계를 생략하지 않는다.
---

# 원고 무결성

문장을 잘 쓰는 일과 원고를 잃지 않는 일은 다른 능력이다. 「최고의 경험, 최고의 카페」에서는 **작업 환경의 상태 회귀로 원고가 여러 차례 유실되었고**, 공간명을 교체한 뒤 다른 장에 남은 옛 이름을 반복해서 놓쳤다.

이 스킬은 그것을 기계로 막는다. 사람의 주의력에 기대지 않는다.

## 매 회차 검사

작업 회차를 마칠 때마다 돌린다. 마감 직전에 한 번 돌리는 것이 아니다.

```bash
python3 scripts/manuscript_check.py --ko manuscript/ko.md --en manuscript/en.md --state book-state.json
```

한 번에 다섯 가지를 확인한다.

| 검사 | 무엇을 잡는가 |
|---|---|
| 블록 대조 | 한국어판과 영어판의 문단 수가 어긋난 것 |
| 제목 대조 | 제목의 수와 단계가 어긋난 것 |
| 한글 혼입 | 영어판에 남은 한글 음절 |
| 깨진 글자·코드 잔재 | 인코딩 사고와 마크업 찌꺼기 |
| 옛 공간명 잔재 | 교체한 이름이 남은 자리 |
| 상태 점검 | 백업 기록의 실재, 반려 상태인 장 |

종료 코드가 1이면 통과하지 못한 것이다. 통과하지 못한 채로 제작 단계에 넘기지 않는다.

부분 검사도 된다.

```bash
python3 scripts/manuscript_check.py --en manuscript/en.md --hangul-only
python3 scripts/manuscript_check.py --ko manuscript/ko.md --legacy "카브,타이드,캐노피"
```

## 블록이 어긋났을 때

블록 수의 차이는 대개 재저작 과정에서 문단을 합치거나 나눈 자리에서 생긴다. **영어판을 한국어판에 맞추는 것이 원칙이지만, 나눈 것이 옳은 경우가 있다.** 영어 산문의 호흡상 한 문단이 둘로 갈라져야 했다면 한국어판을 나눈다.

어느 쪽을 고칠지는 내용으로 판단한다. 숫자를 맞추기 위해 문단을 억지로 붙이지 않는다. 다만 **차이를 발견하고도 그냥 두지 않는다.** 구조가 어긋난 채로 조판에 들어가면 한국어판과 영어판의 쪽수 대응이 무너진다.

## 백업 규율

**원고 스크립트 백업본을 산출물과 함께 보관한다.** 실제로 여러 차례 유실이 발생했다.

```bash
python3 scripts/backup_manuscript.py --state book-state.json
```

- 회차마다 새 백업을 만들고 옛 백업을 지우지 않는다.
- 백업 경로를 `book-state.json`의 `backup.last`에 기록한다. 기록하지 않으면 검사가 백업의 부재를 잡아내지 못한다.
- 원고뿐 아니라 `ledger.json`과 `book-state.json`도 함께 백업한다. 대장을 잃으면 스물한 장의 변주 이력을 잃는다.
- 대화 맥락이 아니라 파일로 남긴다. 상태 회귀는 예고 없이 온다.

상세는 `references/loss-prevention.md`를 읽는다.

## 공간명을 바꿀 때

이름 하나를 바꾸면 최소 다섯 곳을 고쳐야 한다. 본문, 다른 장의 언급, 부 도입, 차례, 대장.

```bash
# 1. 영향 범위를 먼저 조회한다
python3 ../series-variation-ledger/scripts/variation_ledger.py rename-impact --from 카브 --to 풀 --scan manuscript/

# 2. 고친다

# 3. 옛 이름을 book-state.json의 retired_names에 넣는다

# 4. 잔재가 남지 않았는지 확인한다
python3 scripts/manuscript_check.py --ko manuscript/ko.md --en manuscript/en.md --state book-state.json
```

**옛 이름을 `retired_names`에서 지우지 않는다.** 지우는 순간 잔재를 찾을 방법이 사라진다. 목록은 계속 자란다.

## 산출물 빌드

문법 검증과 문서 검증을 거친 뒤에만 빌드한다.

- **워드 원고** — `docx` 스킬을 쓴다. 제목 단계, 각주, 편집 상태를 보존한다.
- **검토용 PDF** — `pdf` 스킬을 쓴다. 렌더된 쪽을 눈으로 확인한다.
- **판형·조판·표지·EPUB·메타데이터** — `book-publishing-editor-designer` 스킬로 인계한다. 정본 원고 하나에서 인쇄판과 전자책판을 파생시키고, **인쇄 PDF를 전자책 원본으로 쓰지 않는다.**

빌드 후에도 검사를 다시 돌린다. 변환 과정에서 깨진 글자가 생긴다.

상세는 `references/build-and-verify.md`를 읽는다.

## 참조 파일

- `references/build-and-verify.md` — 검사 항목별 판정과 조치, 빌드 절차.
- `references/loss-prevention.md` — 유실의 실제 경로와 백업 규율.
- `scripts/manuscript_check.py` — 무결성 검사.
- `scripts/backup_manuscript.py` — 백업과 상태 기록.
