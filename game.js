/* ========================================================
   DiaStudio RPG – game.js
   Single-file game logic (no dependencies)
   ======================================================== */

'use strict';

// ── Utility ──────────────────────────────────────────────
const rand   = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const clamp  = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const $      = id => document.getElementById(id);

// ── Data ─────────────────────────────────────────────────

const ENEMIES = [
  { name: '슬라임',     sprite: '🟢', hp: 20,  atk: 4,  def: 1,  exp: 10, gold: 8,  minLv: 1 },
  { name: '고블린',     sprite: '👺', hp: 35,  atk: 7,  def: 2,  exp: 18, gold: 14, minLv: 1 },
  { name: '스켈레톤',   sprite: '💀', hp: 50,  atk: 10, def: 3,  exp: 28, gold: 22, minLv: 2 },
  { name: '오크',       sprite: '👾', hp: 70,  atk: 14, def: 5,  exp: 40, gold: 30, minLv: 3 },
  { name: '트롤',       sprite: '🧌', hp: 100, atk: 18, def: 8,  exp: 60, gold: 45, minLv: 4 },
  { name: '드래곤',     sprite: '🐉', hp: 150, atk: 25, def: 12, exp: 100,gold: 80, minLv: 5 },
  { name: '🌑 마왕',   sprite: '😈', hp: 250, atk: 35, def: 18, exp: 300,gold: 200,minLv: 7, boss: true },
];

const SHOP_ITEMS = [
  { id: 'potion',     name: '포션',         emoji: '🧪', desc: 'HP 40 회복',        cost: 30,  action: p => { p.hp = clamp(p.hp + 40, 0, p.maxHp); } },
  { id: 'hi_potion',  name: '하이 포션',    emoji: '💊', desc: 'HP 완전 회복',       cost: 80,  action: p => { p.hp = p.maxHp; } },
  { id: 'sword',      name: '강화 검',      emoji: '🗡️',  desc: '공격력 +5 (영구)',   cost: 100, action: p => { p.atk += 5; }, once: true },
  { id: 'shield',     name: '강화 방패',    emoji: '🛡️',  desc: '방어력 +3 (영구)',   cost: 80,  action: p => { p.def += 3; }, once: true },
  { id: 'hp_up',      name: 'HP 강화약',    emoji: '❤️',  desc: '최대 HP +20 (영구)', cost: 90,  action: p => { p.maxHp += 20; p.hp = clamp(p.hp + 20, 0, p.maxHp); }, once: true },
];

// ── Player Factory ────────────────────────────────────────
function createPlayer(name) {
  return {
    name,
    level:   1,
    hp:      80,
    maxHp:   80,
    atk:     12,
    def:     4,
    exp:     0,
    expNext: 30,
    gold:    50,
    potions: 2,
    skillMp: 3,          // skill uses per battle
    bought:  new Set(),
  };
}

// ── Game State ────────────────────────────────────────────
let player  = null;
let enemy   = null;
let battleLocked = false;

// ── Screen Helpers ────────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  $(id).classList.add('active');
}

// ── Logging ───────────────────────────────────────────────
function log(boxId, msg, cls = '') {
  const box = $(boxId);
  const p = document.createElement('p');
  if (cls) p.className = cls;
  p.innerHTML = msg;
  box.appendChild(p);
  box.scrollTop = box.scrollHeight;
}
function clearLog(boxId) { $(boxId).innerHTML = ''; }

// ── Status Panel ──────────────────────────────────────────
function renderTownStatus() {
  const p = player;
  const expPct = Math.floor(p.exp / p.expNext * 100);
  $('town-status').innerHTML = `
    <div class="stat-row"><span class="stat-label">용사</span>  <span class="stat-value highlight">${p.name}</span></div>
    <div class="stat-row"><span class="stat-label">레벨</span>  <span class="stat-value highlight">Lv.${p.level}</span></div>
    <div class="stat-row"><span class="stat-label">HP</span>    <span class="stat-value">${p.hp} / ${p.maxHp}</span></div>
    <div class="stat-row"><span class="stat-label">공격</span>  <span class="stat-value">${p.atk}</span></div>
    <div class="stat-row"><span class="stat-label">방어</span>  <span class="stat-value">${p.def}</span></div>
    <div class="stat-row"><span class="stat-label">경험치</span><span class="stat-value">${p.exp} / ${p.expNext} (${expPct}%)</span></div>
    <div class="stat-row"><span class="stat-label">골드</span>  <span class="stat-value highlight">${p.gold}G</span></div>
    <div class="stat-row"><span class="stat-label">포션</span>  <span class="stat-value">${p.potions}개</span></div>
  `;
}

// ── Battle Helpers ────────────────────────────────────────
function calcDmg(atkVal, defVal) {
  const base = Math.max(1, atkVal - defVal);
  return rand(Math.floor(base * 0.8), Math.ceil(base * 1.3));
}

function updateBattleUI() {
  const p = player;
  const e = enemy;
  $('player-battle-name').textContent = `${p.name} (Lv.${p.level})`;
  $('player-battle-hp').textContent   = `${p.hp} / ${p.maxHp}`;
  $('player-hp-fill').style.width     = `${clamp(p.hp / p.maxHp * 100, 0, 100)}%`;

  $('enemy-battle-name').textContent = e.name;
  $('enemy-battle-hp').textContent   = `${e.hp} / ${e.maxHp}`;
  $('enemy-hp-fill').style.width     = `${clamp(e.hp / e.maxHp * 100, 0, 100)}%`;
  $('enemy-sprite').textContent      = e.sprite;
}

function shakeDmg(who) {
  const el = $(who === 'player' ? 'player-sprite' : 'enemy-sprite');
  el.classList.remove('shake');
  void el.offsetWidth; // reflow
  el.classList.add('shake');
}

function setBattleLock(locked) {
  battleLocked = locked;
  ['btn-attack','btn-skill','btn-item','btn-flee'].forEach(id => {
    $(id).disabled = locked;
  });
}

// ── Enemy Turn ────────────────────────────────────────────
function enemyTurn() {
  setTimeout(() => {
    if (!enemy || enemy.hp <= 0) return;

    const dmg = calcDmg(enemy.atk, player.def);
    player.hp = clamp(player.hp - dmg, 0, player.maxHp);
    shakeDmg('player');
    log('battle-log', `${enemy.name}의 공격! <b>${dmg}</b> 데미지!`, 'log-hit');
    updateBattleUI();

    if (player.hp <= 0) {
      endBattle('lose');
    } else {
      setBattleLock(false);
    }
  }, 700);
}

// ── Battle End ────────────────────────────────────────────
function endBattle(result) {
  setBattleLock(true);

  if (result === 'win') {
    const expGain  = enemy.exp;
    const goldGain = rand(Math.floor(enemy.gold * 0.8), Math.ceil(enemy.gold * 1.2));
    player.gold += goldGain;
    player.exp  += expGain;
    log('battle-log', `🏆 승리! 경험치 +${expGain}, 골드 +${goldGain}G`, 'log-reward');

    // Level up
    let leveled = false;
    while (player.exp >= player.expNext) {
      player.exp     -= player.expNext;
      player.level   += 1;
      player.expNext  = Math.floor(player.expNext * 1.6);
      player.maxHp   += 15;
      player.hp       = player.maxHp;        // full heal on level up
      player.atk     += 3;
      player.def     += 1;
      leveled = true;
      log('battle-log', `✨ 레벨 업! → Lv.${player.level}  (HP 완전 회복!)`, 'log-reward');
    }

    if (enemy.boss) {
      setTimeout(() => {
        $('victory-msg').textContent =
          `${player.name}은(는) 마왕을 물리치고 세계를 구했다! (최종 레벨: ${player.level})`;
        showScreen('screen-victory');
      }, 1200);
      return;
    }

    setTimeout(() => {
      showScreen('screen-town');
      renderTownStatus();
      clearLog('town-log');
      log('town-log', `전투 승리! 경험치 +${expGain}, 골드 +${goldGain}G`, 'log-reward');
      if (leveled) log('town-log', `레벨 업! 현재 Lv.${player.level}`, 'log-system');
    }, 1000);

  } else if (result === 'flee') {
    log('battle-log', '도망쳤다!', 'log-info');
    setTimeout(() => {
      showScreen('screen-town');
      renderTownStatus();
    }, 800);

  } else { // lose
    log('battle-log', '💀 쓰러졌다...', 'log-hit');
    setTimeout(() => {
      $('gameover-msg').textContent =
        `${player.name}은(는) ${enemy.name}에게 쓰러졌다. (도달 레벨: ${player.level})`;
      showScreen('screen-gameover');
    }, 1200);
  }
}

// ── Start Battle ──────────────────────────────────────────
function startBattle() {
  // Pick a valid enemy for player level
  const pool = ENEMIES.filter(e => !e.boss && e.minLv <= player.level);
  // Weighted toward higher-level enemies as player levels up
  const e    = pool[rand(Math.max(0, pool.length - 3), pool.length - 1)];

  enemy = { ...e, hp: e.hp, maxHp: e.hp };
  // Give skill uses back each battle
  player.skillMp = 3;

  clearLog('battle-log');
  log('battle-log', `${enemy.sprite} ${enemy.name}이(가) 나타났다!`, 'log-system');

  $('player-sprite').textContent = '🧙';
  updateBattleUI();
  setBattleLock(false);
  showScreen('screen-battle');
}

function startBossBattle() {
  const boss = ENEMIES.find(e => e.boss);
  enemy = { ...boss, hp: boss.hp, maxHp: boss.hp };
  player.skillMp = 3;

  clearLog('battle-log');
  log('battle-log', `⚠️ 마왕 ${boss.name}이(가) 나타났다!`, 'log-system');

  $('player-sprite').textContent = '🧙';
  updateBattleUI();
  setBattleLock(false);
  showScreen('screen-battle');
}

// ── Shop ──────────────────────────────────────────────────
function renderShop() {
  $('shop-gold').textContent = `보유 골드: ${player.gold}G`;
  const container = $('shop-items');
  container.innerHTML = '';

  SHOP_ITEMS.forEach(item => {
    if (item.once && player.bought.has(item.id)) return; // already purchased

    const div = document.createElement('div');
    div.className = 'shop-item';
    div.innerHTML = `
      <div class="shop-item-info">
        <h4>${item.emoji} ${item.name}</h4>
        <p>${item.desc}</p>
      </div>
      <span class="shop-item-price">${item.cost}G</span>
    `;

    const btn = document.createElement('button');
    btn.className = 'btn btn-primary';
    btn.textContent = '구매';
    btn.disabled = player.gold < item.cost;
    btn.addEventListener('click', () => {
      if (player.gold < item.cost) return;
      player.gold -= item.cost;
      item.action(player);
      if (item.once) player.bought.add(item.id);
      renderShop();
      clearLog('town-log');
      log('town-log', `${item.emoji} ${item.name}을(를) 구매했다!`, 'log-heal');
    });

    div.appendChild(btn);
    container.appendChild(div);
  });

  if (container.children.length === 0) {
    container.innerHTML = '<p style="text-align:center;color:#aaa;">더 이상 구매할 수 있는 물건이 없습니다.</p>';
  }
}

// ── Event Wiring ──────────────────────────────────────────
$('start-btn').addEventListener('click', () => {
  const name = $('player-name-input').value.trim() || '용사';
  player = createPlayer(name);
  clearLog('town-log');
  log('town-log', `어서오세요, ${player.name}! 마왕을 물리치러 출발하세요.`, 'log-system');
  renderTownStatus();
  showScreen('screen-town');
});

$('player-name-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') $('start-btn').click();
});

// Town buttons
$('btn-battle').addEventListener('click', () => {
  if (player.level >= 7) {
    // Offer boss fight
    if (confirm('레벨 7 이상! 마왕에게 도전하시겠습니까?')) {
      startBossBattle();
    } else {
      startBattle();
    }
  } else {
    startBattle();
  }
});

$('btn-shop').addEventListener('click', () => {
  renderShop();
  showScreen('screen-shop');
});

$('btn-rest').addEventListener('click', () => {
  if (player.gold < 30) {
    clearLog('town-log');
    log('town-log', '골드가 부족합니다! (30G 필요)', 'log-hit');
    return;
  }
  if (player.hp === player.maxHp) {
    clearLog('town-log');
    log('town-log', 'HP가 이미 가득 찼습니다.', 'log-info');
    return;
  }
  player.gold -= 30;
  player.hp    = player.maxHp;
  clearLog('town-log');
  log('town-log', '🛌 푹 쉬었다. HP가 완전히 회복되었다!', 'log-heal');
  renderTownStatus();
});

// Battle buttons
$('btn-attack').addEventListener('click', () => {
  if (battleLocked) return;
  setBattleLock(true);

  const dmg = calcDmg(player.atk, enemy.def);
  enemy.hp  = clamp(enemy.hp - dmg, 0, enemy.maxHp);
  shakeDmg('enemy');
  log('battle-log', `⚔️ 공격! ${enemy.name}에게 <b>${dmg}</b> 데미지!`, 'log-hit');
  updateBattleUI();

  if (enemy.hp <= 0) { endBattle('win'); return; }
  enemyTurn();
});

$('btn-skill').addEventListener('click', () => {
  if (battleLocked) return;
  if (player.skillMp <= 0) {
    log('battle-log', '스킬을 더 이상 사용할 수 없습니다!', 'log-info');
    return;
  }
  setBattleLock(true);
  player.skillMp -= 1;

  const dmg = calcDmg(player.atk * 1.8, enemy.def);  // 1.8× multiplier
  enemy.hp  = clamp(enemy.hp - dmg, 0, enemy.maxHp);
  shakeDmg('enemy');
  log('battle-log', `✨ 강타! ${enemy.name}에게 <b>${dmg}</b> 데미지! (남은 스킬: ${player.skillMp})`, 'log-skill');
  updateBattleUI();

  if (enemy.hp <= 0) { endBattle('win'); return; }
  enemyTurn();
});

$('btn-item').addEventListener('click', () => {
  if (battleLocked) return;
  if (player.potions <= 0) {
    log('battle-log', '포션이 없습니다!', 'log-info');
    return;
  }
  setBattleLock(true);
  player.potions -= 1;
  const heal = 40;
  player.hp = clamp(player.hp + heal, 0, player.maxHp);
  log('battle-log', `🧪 포션 사용! HP +${heal} 회복 (남은 포션: ${player.potions})`, 'log-heal');
  updateBattleUI();
  // Using item doesn't end turn – enemy still attacks
  enemyTurn();
});

$('btn-flee').addEventListener('click', () => {
  if (battleLocked) return;
  const success = Math.random() < 0.55;
  if (success) {
    endBattle('flee');
  } else {
    setBattleLock(true);
    log('battle-log', '도망에 실패했다!', 'log-info');
    enemyTurn();
  }
});

// Shop back
$('btn-shop-back').addEventListener('click', () => {
  renderTownStatus();
  showScreen('screen-town');
});

// Game Over / Victory
$('btn-retry').addEventListener('click', () => {
  player = null;
  enemy  = null;
  $('player-name-input').value = '';
  showScreen('screen-title');
});

$('btn-play-again').addEventListener('click', () => {
  player = null;
  enemy  = null;
  $('player-name-input').value = '';
  showScreen('screen-title');
});
