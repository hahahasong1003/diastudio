# 배포 지형

SH 워크스페이스는 스킬 하나를 세 곳에 건다. 정본은 한 벌만 두고 나머지는 정본을 가리키는 어댑터다. 어댑터에 내용을 복제하지 않는다. 복제하면 두 벌이 어긋난다.

## 계층

| 위치 | 역할 | 정본까지의 상대 경로 |
|---|---|---|
| `SH/.claude/skills/<name>/` | **정본.** SKILL.md와 references와 scripts가 여기에만 있다 | — |
| `SH/.agents/skills/<name>/SKILL.md` | Codex 어댑터 | `../../../.claude/skills/<name>/SKILL.md` |
| `<프로젝트>/.claude/skills/<name>/SKILL.md` | 자식 프로젝트 어댑터 | `../../../../.claude/skills/<name>/SKILL.md` |
| `<프로젝트>/.agents/skills/<name>/SKILL.md` | 자식 프로젝트 Codex 어댑터 | `../../../../.claude/skills/<name>/SKILL.md` |

자식 프로젝트 어댑터는 프로젝트 고유 규칙을 공용 지침 **뒤에** 얹는다. 규칙 파일은 `<프로젝트>/.claude/rules/<주제>-integration.md`에 둔다.

## 어댑터 서식

**SH Codex 어댑터**

```markdown
---
name: <name>
description: <한 줄 영문 요약>, using the SH canonical workflow.
---

# SH adapter

Use the canonical instructions at `../../../.claude/skills/<name>/SKILL.md` and the relevant references there. Treat that file as authoritative.
```

**자식 프로젝트 어댑터** (`.claude`와 `.agents` 양쪽에 같은 내용)

```markdown
---
name: <name>
description: <한 줄 영문 요약>, using the shared SH capability and this project's <주제> rules.
---

# Child project adapter

Use the canonical instructions at `../../../../.claude/skills/<name>/SKILL.md` and the relevant references there. Apply this project's `.claude/rules/<주제>-integration.md` after the shared rules.
```

## 2026-08-21 배포분

여덟 개 스킬을 세 계층에 걸었다. 정본은 `SH/.claude/skills/`에 있고 이 저장소의 `cafe-book-skills/`와 `sh-skills/`가 그 원본이다.

| 스킬 | 규칙 파일 |
|---|---|
| cafe-book-conductor | `cafe-book-integration.md` |
| themed-space-concept-forge | `cafe-book-integration.md` |
| chapter-movement-composer | `cafe-book-integration.md` |
| literary-prose-voice | `cafe-book-integration.md` |
| series-variation-ledger | `cafe-book-integration.md` |
| literary-transcreation | `cafe-book-integration.md` |
| manuscript-integrity-ops | `cafe-book-integration.md` |
| english-instructor-reviewer | `english-instruction-integration.md` |

**자식 프로젝트는 D.I.A Studio 하나로 한정했다.** 배포 정책이 "필요한 지침, 어댑터 또는 승인된 사본만 배포한다"고 정하고 있고, 카페 책 집필과 영어 교육은 Claude Code_M365_song의 영역(M365·Copilot 변화관리)이 아니다. M365 쪽에서 이 역량이 필요해지면 그때 어댑터를 더한다.

## 레지스트리 병합 기록

`_SH_Knowledge_Hub/02_스킬_레지스트리/SKILL_REGISTRY.md`에 여덟 항목을 더하고 어댑터 지형 절을 넣었다. 기존 일곱 항목 중 `ko-en-translation-review-editor`와 `korean-copyedit-proofreader`에는 새 스킬로 넘기는 분기 조건을 덧붙였다.

연결 커넥터가 파일의 메타데이터만 고칠 수 있어 **새 파일로 만들고 원본을 휴지통으로 보내는** 방식을 썼다. 경로가 같아 `sh-knowledge-orchestrator`의 상대 참조는 그대로 작동한다.

- 병합 전 원본(6,959바이트)은 구글 드라이브 휴지통에 있다. 되돌려야 하면 거기서 복구한다.
- 병합 전에 원본을 복원해 바이트 수를 대조했다. 6,959바이트로 정확히 일치했으므로 보존 구간에 손실이 없다.
- 읽기 도구가 출력하는 역슬래시 이스케이프와 후행 공백은 렌더링 산물이며 파일에 저장된 내용이 아니다. 다음에 같은 작업을 할 때 이것을 실제 내용으로 착각해 옮겨 적지 않는다.
- 임시로 두었던 레지스트리 추가분 두 개와 배포 기록 하나는 병합 뒤 지웠다.

## 정본을 고칠 때

어댑터는 건드리지 않는다. `SH/.claude/skills/<name>/` 아래만 고치면 세 계층이 함께 따라온다.

**어댑터를 고쳐야 하는 경우는 셋뿐이다.** 스킬의 이름이 바뀔 때, 설명 한 줄이 실제 용도와 어긋나게 되었을 때, 프로젝트 규칙 파일의 이름이 바뀔 때.

## 스킬을 폐기할 때

세 계층의 어댑터를 먼저 지우고 정본을 마지막에 지운다. 반대 순서로 하면 정본이 없는 어댑터가 남아 조용히 실패한다. 레지스트리에서도 해당 항목을 뺀다.
