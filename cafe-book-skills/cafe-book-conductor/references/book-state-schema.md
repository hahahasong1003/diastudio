# book-state.json

전권 작업의 단일 진실 공급원이다. 지휘 스킬만 쓰고, 전문 스킬은 읽기만 한다. 원고 파일과 같은 디렉터리에 둔다.

## 스키마

```json
{
  "book": {
    "title_ko": "최고의 경험, 최고의 카페 2권",
    "title_en": "",
    "chapter_count": 21,
    "stage": "drafting",
    "manuscript_ko": "manuscript/ko.md",
    "manuscript_en": "manuscript/en.md",
    "ledger": "ledger.json"
  },
  "parts": [
    { "no": 1, "title_ko": "떠나지 않고 떠나는 곳", "chapters": [1, 2, 3] }
  ],
  "chapters": [
    {
      "no": 1,
      "space_ko": "알티튜드",
      "space_en": "Altitude",
      "question": "우리는 언제 하늘을 올려다보지 않게 되었나",
      "absolution": "떠나지 못한 채로도 떠날 수 있다",
      "status": {
        "concept": "approved",
        "ledger_reserved": true,
        "draft": "done",
        "voice": "passed",
        "ledger_committed": true,
        "copyedit": "pending",
        "transcreation": "none",
        "en_review": "none",
        "integrity": "none"
      }
    }
  ],
  "handoffs": {
    "korean_copyedit": { "state": "pending", "stylesheet": "handoff/stylesheet-ko.md" },
    "ko_en_review": { "state": "none", "brief": "handoff/en-review-brief.md" },
    "publishing": { "state": "none" }
  },
  "retired_names": ["카브", "타이드", "캐노피", "미스트"],
  "backup": { "last": "backup/ko-2026-08-21.md", "policy": "매 회차 산출물과 함께" }
}
```

## 필드 규약

**`status`의 값** — `none`(아직 아님), `pending`(진행 중), `passed`/`done`(통과), `failed`(반려, 되돌아감). `failed`인 장이 하나라도 있으면 다음 단계 전체를 시작하지 않는다.

**`question`과 `absolution`** — 이 두 줄이 비어 있으면 그 장은 콘셉트 게이트를 통과하지 못한다. 집필 중 방향이 바뀌면 여기를 먼저 고치고 본문을 고친다. 반대 순서로 하면 장의 중심이 흔들린다.

**`retired_names`** — 교체하거나 반려한 공간명을 모두 남긴다. 지우지 않는다. 무결성 검사가 이 목록으로 원고에 남은 잔재를 찾는다. 목록에서 지우는 순간 잔재를 찾을 방법이 사라진다.

**`stage`** — `concept` / `drafting` / `revising` / `bilingual` / `production` / `released`.

## 갱신 규약

- 단계를 마칠 때마다 즉시 갱신한다. 여러 단계를 몰아서 갱신하지 않는다.
- 병렬 하위 작업은 이 파일을 쓰지 않는다. 결과를 지휘자에게 반환하고 지휘자가 쓴다.
- 공간명을 바꿀 때는 `space_ko`를 고치고 옛 이름을 `retired_names`에 넣는 두 작업을 한 번에 한다.
- 파일이 없으면 만들되, 이미 원고가 있는 상태에서 만들 때는 원고를 읽어 현재 상태를 역산해서 채운다. 빈 값으로 만들어 두면 게이트가 무력해진다.
