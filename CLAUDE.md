# CLAUDE.md — DiaStudio RPG

This file provides context for AI assistants (Claude Code, Copilot, etc.)
working with this repository.

---

## Project Overview

**DiaStudio RPG** is a browser-based turn-based RPG written in vanilla
HTML/CSS/JavaScript — no build tools, no frameworks, no dependencies.
Opening `index.html` directly in any modern browser runs the game.

### Feature Summary
- Character creation with a custom name
- Town hub (battle, shop, rest)
- Turn-based combat with attack, skill (1.8× damage, 3 uses/battle),
  potion, and flee actions
- 6 regular enemies + 1 final boss (마왕), gated by player level
- Level-up system with stat growth and full HP restore
- Permanent upgrades and consumables purchasable in the shop
- Game-over and victory screens

---

## File Structure

```
diastudio/
├── index.html   # All markup / screen definitions
├── style.css    # Dark-theme UI styles
├── game.js      # All game logic (data, state, events)
└── CLAUDE.md    # This file
```

There is intentionally **no build step**. Do not add bundlers (Webpack,
Vite, etc.) unless the user explicitly asks for it.

---

## Architecture & Key Conventions

### Single-file logic (`game.js`)
All game logic lives in `game.js`. The file is divided into clearly
commented sections:

| Section | Purpose |
|---|---|
| `Utility` | `rand`, `clamp`, `$` helpers |
| `Data` | `ENEMIES` and `SHOP_ITEMS` arrays |
| `Player Factory` | `createPlayer(name)` — returns a fresh player object |
| `Game State` | Module-level `player`, `enemy`, `battleLocked` vars |
| `Screen Helpers` | `showScreen(id)` — toggles `.active` class |
| `Logging` | `log(boxId, msg, cls)` / `clearLog(boxId)` |
| `Status Panel` | `renderTownStatus()` — rebuilds status HTML |
| `Battle Helpers` | `calcDmg`, `updateBattleUI`, `shakeDmg`, `setBattleLock` |
| `Enemy Turn` | `enemyTurn()` — 700 ms delayed auto-attack |
| `Battle End` | `endBattle(result)` — handles win/lose/flee |
| `Start Battle` | `startBattle()` / `startBossBattle()` |
| `Shop` | `renderShop()` — generates shop item DOM |
| `Event Wiring` | All `addEventListener` calls at the bottom |

### Screen system
Each game state maps to a `<div id="screen-*">` in `index.html`.
`showScreen(id)` removes `.active` from all screens and adds it to the
target. **Never manipulate `display` directly** — use `showScreen`.

### Logging classes
Log messages use CSS helper classes defined in `style.css`:

| Class | Use |
|---|---|
| `log-hit` | Damage dealt |
| `log-heal` | HP recovered |
| `log-skill` | Skill usage |
| `log-info` | Neutral info / misses |
| `log-reward` | EXP / gold gain, level-up |
| `log-system` | System / narrative messages |

### Combat flow
```
Player action → setBattleLock(true) → apply effect → updateBattleUI
  → if enemy dead → endBattle('win')
  → else → enemyTurn() [700ms delay] → setBattleLock(false)
                                     → if player dead → endBattle('lose')
```
`battleLocked` prevents double-clicks during animations. Always check it
at the top of every player action handler.

### Enemy & shop data
- Add enemies to the `ENEMIES` array in `game.js`. Required fields:
  `name`, `sprite` (emoji), `hp`, `atk`, `def`, `exp`, `gold`, `minLv`.
  Set `boss: true` for the final boss.
- Add shop items to `SHOP_ITEMS`. Set `once: true` for one-time purchases.
  The `action(player)` function mutates the player object directly.

---

## Development Workflow

### Running the game
```bash
# Option 1 – open directly
open index.html          # macOS
xdg-open index.html      # Linux
start index.html         # Windows

# Option 2 – simple HTTP server (avoids CORS for future assets)
python3 -m http.server 8080
# then open http://localhost:8080
```

### Making changes
1. Edit `game.js` / `style.css` / `index.html` directly.
2. Hard-refresh the browser (`Ctrl+Shift+R` / `Cmd+Shift+R`).
3. No compilation or hot-reload is needed.

### Git
- Branch: `claude/claude-md-mm459loqcerah3cb-6OOLi`
- Commit messages: use the imperative mood in Korean or English.
  Example: `feat: 새로운 보스 추가` or `fix: 레벨업 버그 수정`

---

## Adding Content — Quick Reference

### New enemy
```js
// In ENEMIES array (game.js)
{ name: '새 몬스터', sprite: '👻', hp: 60, atk: 12, def: 4, exp: 35, gold: 25, minLv: 3 },
```

### New shop item (consumable)
```js
// In SHOP_ITEMS array (game.js)
{ id: 'my_item', name: '새 아이템', emoji: '💡', desc: '설명', cost: 50,
  action: p => { /* mutate player */ } },
```

### New screen
1. Add `<div id="screen-new" class="screen">…</div>` to `index.html`.
2. Navigate with `showScreen('screen-new')`.
3. Add a back button that calls `showScreen('screen-town')`.

---

## Style Guide

- **Vanilla JS only** — no libraries unless the feature genuinely requires one.
- **Emoji as icons** — avoids sprite/asset management overhead.
- **Korean UI text** — all user-visible strings are in Korean.
- **Dark theme** — primary bg `#0d0d1a`, card bg `#1a1a2e`, accent `#f0c040`.
- CSS class names use BEM-lite kebab-case: `shop-item`, `hp-bar-wrap`, etc.
- Do not inline styles; add new classes to `style.css`.

---

## Known Limitations / Future Work

- No save/load system (state is in-memory only).
- No sound or music.
- Mobile layout is functional but not fully optimised for very small screens.
- Enemy AI always attacks (no special moves for enemies yet).
