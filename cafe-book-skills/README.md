# 카페 책 집필 스킬 묶음

「최고의 경험, 최고의 카페」를 스물한 장·한국어판·영어판으로 집필하며 얻은 전문 역량을 일곱 개의 스킬로 나눈 것이다. 각 스킬은 혼자서도 쓸 수 있고, 함께 쓰면 한 권을 끝까지 끌고 가는 파이프라인이 된다.

## 무엇이 들어 있는가

| 스킬 | 하는 일 | 단계 |
|---|---|---|
| `cafe-book-conductor` | 파이프라인 지휘, 게이트 순서, 상태 관리, 인계 | 총괄 |
| `themed-space-concept-forge` | 콘셉트 발상과 4대 검증, 반려 판정 | 기획 |
| `chapter-movement-composer` | 19악장 설계와 집필, 인물 캐스팅 | 집필 |
| `literary-prose-voice` | 창작 문체, 금지 패턴 제거, 퇴고 | 문장 |
| `series-variation-ledger` | 변주 대장, 중복 차단, 전권 일관성 | 상태 |
| `literary-transcreation` | 영어판 재저작 | 이중언어 |
| `manuscript-integrity-ops` | 블록 대조, 혼입 검사, 백업, 빌드 | 산출 |

## 왜 하나가 아니라 일곱인가

「최고의 경험, 최고의 카페」의 집필 노하우는 원래 `cafe-book-author` 스킬 하나에 담겨 있었다. 그것은 **원칙의 정본**으로는 훌륭하지만 **실행**에는 부족했다. 원칙을 읽는 것과 게이트를 통과시키는 것은 다른 일이기 때문이다.

한 권을 끝까지 끌고 가며 실제로 무너진 지점은 세 곳이었다.

1. 장마다 같은 키워드를 다시 썼다 — 기억으로 관리할 수 있는 양이 아니었다.
2. 규범 교열이 의도한 문체를 뭉갰다 — 순서가 잘못되어 있었다.
3. 공간 이름을 바꾼 뒤 다른 장에 남은 옛 이름을 놓쳤다 — 사람의 주의력에 기대고 있었다.

셋 다 원칙을 몰라서 생긴 문제가 아니다. 구조가 없어서 생긴 문제다. 이 묶음은 그 셋을 각각 대장(`series-variation-ledger`), 게이트 순서(`cafe-book-conductor`), 기계 검사(`manuscript-integrity-ops`)로 막는다.

## 스킬 사이의 연계

```
[1] 콘셉트   themed-space-concept-forge   → 4대 검증 통과분만
[2] 예약     series-variation-ledger      → 장별 고유값 조회·예약
[3] 초고     chapter-movement-composer    → 19악장 집필
[4] 문체     literary-prose-voice         → 창작 문체 확정
[5] 확정     series-variation-ledger      → 예약분 commit
[6] 교열     korean-copyedit-proofreader  ← SH 공용 게이트
[7] 재저작   literary-transcreation       → 영어판
[8] 검수     ko-en-translation-review-editor ← SH 공용 게이트
[9] 무결성   manuscript-integrity-ops     → 대조·검사·백업
[10] 제작    book-publishing-editor-designer ← SH 공용 게이트
```

**[4]가 [6]보다 먼저인 것이 이 설계의 핵심이다.** `literary-prose-voice`는 창작 의도를 세우고 `korean-copyedit-proofreader`는 국립국어원 규범으로 잰다. 규범을 먼저 적용하면 의도적으로 짧게 끊은 호흡과 리듬을 만드는 반복이 교정 대상으로 걸린다. 문체를 먼저 확정하고 스타일시트로 넘기면 규범 검수는 오탈자와 표기만 건드린다.

같은 이유로 **[7]이 [8]보다 먼저다.** 영어판은 번역이 아니라 재저작이므로, 검수 스킬에 "문장 단위 역대조를 적용하지 말 것"을 명시해서 넘긴다. 이 단서 없이 넘기면 검수가 재저작을 오역으로 판정한다.

## 하네스와의 연계

세 개의 훅이 게이트를 사람의 기억에서 떼어 낸다.

| 훅 | 시점 | 하는 일 |
|---|---|---|
| `session_brief.py` | SessionStart | 어느 장이 어느 게이트에 걸려 있는지 보여 준다 |
| `lint_on_write.py` | PostToolUse (Write/Edit) | 원고를 고칠 때마다 문체 검사를 돌리고 오류가 있으면 그 자리에서 막는다 |
| `pending_reservations.py` | Stop | 예약만 되고 확정되지 않은 변주값이 남았는지 확인한다 |

세 스킬이 실행 가능한 스크립트를 함께 싣는다.

- `literary-prose-voice/scripts/prose_lint.py` — 금지 패턴 검사
- `series-variation-ledger/scripts/variation_ledger.py` — 조회·예약·확정·개명 영향
- `manuscript-integrity-ops/scripts/manuscript_check.py` — 블록 대조·혼입·잔재 검사
- `manuscript-integrity-ops/scripts/backup_manuscript.py` — 백업과 상태 기록

**여러 장을 동시에 쓸 때는 집필을 병렬로, 대장을 직렬로 다룬다.** 지휘하는 쪽이 값을 미리 예약해 나눠 주고, 집필이 끝난 뒤 한꺼번에 확정한다. 집필 중인 하위 작업이 대장을 직접 쓰게 하지 않는다.

## 설치

```
프로젝트/
├── .claude/
│   ├── skills/          ← 일곱 개 스킬 폴더를 그대로 넣는다
│   ├── hooks/           ← hooks/*.py를 넣는다
│   └── settings.json    ← settings.snippet.json의 내용을 병합한다
├── manuscript/
│   ├── ko.md
│   └── en.md
├── book-state.json
├── ledger.json
└── backup/
```

시작할 때 두 가지를 만든다.

```bash
python3 .claude/skills/series-variation-ledger/scripts/variation_ledger.py init --seed
# book-state.json은 cafe-book-conductor의 references/book-state-schema.md 형식으로 만든다
```

`--seed`는 1권의 값 여든여섯 개를 대장에 넣어 2권이 1권과 겹치지 않게 한다.

## 원칙의 정본

집필 원칙의 상위 정본은 `cafe-book-author` 스킬이다. 이 묶음은 그 정본을 단계별로 분해해 실행 가능한 형태로 만든 것이며, **원칙이 충돌하면 `cafe-book-author`를 따른다.**

## 카페 밖으로

`themed-space-concept-forge`, `chapter-movement-composer`, `literary-prose-voice`, `series-variation-ledger`, `literary-transcreation`은 카페에 매이지 않는다. 공간을 무대로 한 연작 에세이, 한국어 문학 산문, 이중언어 출간이라면 어디에나 쓴다. `cafe-book-conductor`만 이 책에 특화되어 있다.

다만 **대상은 카페로 한정한다**는 원칙은 「최고의 경험, 최고의 카페」 자체에는 그대로 남는다. 카페라는 단 하나의 대상에 스물한 번의 변주를 집중시키는 것이 그 책의 밀도를 만든다.
