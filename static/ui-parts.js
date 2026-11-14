'use strict';

/* ---------------------------------------------------------------- pieces */
function gemIcon(color) {
  const paths = {
    diamond: '<path d="M12 3l7 6-7 12L5 9l7-6z"/><path d="M5 9h14M12 3v18"/>',
    sapphire: '<path d="M3 15c3-3 6-3 9 0s6 3 9 0"/><path d="M3 19c3-3 6-3 9 0s6 3 9 0"/>',
    emerald: '<path d="M12 21c-5-3-7-7-7-11a7 7 0 0 1 14 0c0 4-2 8-7 11z"/><path d="M12 21V8"/>',
    ruby: '<path d="M12 3c3 4 5 6 5 9a5 5 0 0 1-10 0c0-3 2-5 5-9z"/>',
    onyx: '<path d="M6 21V9l6-6 6 6v12"/><path d="M10 21v-6h4v6"/>',
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true">${paths[color] || ''}</svg>`;
}

function cardHTML(card, opts = {}) {
  if (!card) return '<div class="card empty" aria-hidden="true"></div>';
  const cost = GEMS.filter((c) => card.cost[c] > 0)
    .map((c) => `<span class="cost gem-${c}">${card.cost[c]}</span>`)
    .join('');
  const cls = ['card', `tier-${card.tier}`, `tint-${card.bonus}`, opts.mini ? 'mini' : ''].join(' ');
  return `<button class="${cls}" data-action="open-card" data-card="${card.id}"
    data-source="${opts.source || 'board'}" ${opts.disabled ? 'disabled' : ''}
    aria-label="${GEM_LABEL[card.bonus]} card, ${card.points} prestige">
    <span class="card-top">
      <span class="card-icon" aria-hidden="true">${gemIcon(card.bonus)}</span>
      <span class="card-tier">${roman(card.tier)}</span>
    </span>
    <span class="card-middle">
      <span class="card-points">${card.points || ''}</span>
      <span class="card-bonus gem-${card.bonus}" aria-hidden="true"></span>
    </span>
    <span class="card-bottom">
      <span class="card-cost">${cost}</span>
      <span class="card-no">${String(card.id + 1).padStart(2, '0')}</span>
    </span>
  </button>`;
}

function nobleHTML(n) {
  const req = GEMS.filter((c) => n.requirement[c] > 0)
    .map((c) => `<span class="req gem-${c}">${n.requirement[c]}</span>`)
    .join('');
  return `<div class="noble" title="${esc(n.name)}">
    <span class="noble-seal" aria-hidden="true">${icon('crown')}</span>
    <span class="noble-pts">3</span>
    <span class="noble-name">${esc(n.name)}</span>
    <span class="noble-req">${req}</span>
  </div>`;
}

function playerChip(p, g, d) {
  const active = g.players[g.turn] && g.players[g.turn].id === p.id;
  const pub = d.players.find((x) => x.id === p.id);
  const tokens = GEMS.filter((c) => p.tokens[c] > 0)
    .map((c) => `<span class="token-dot gem-${c}">${p.tokens[c]}</span>`)
    .join('');
  const gold = p.tokens.gold > 0
    ? `<span class="token-dot gem-gold">${p.tokens.gold}</span>`
    : '';
  const bonuses = GEMS.filter((c) => p.bonuses[c] > 0)
    .map((c) => `<span class="bonus-dot counted gem-${c}" title="${GEM_LABEL[c]} bonus">${p.bonuses[c]}</span>`)
    .join('');
  const coinRow = (tokens || gold) ? `${tokens}${gold}` : '<span class="pc-none">none</span>';
  const power = GEMS.map((c) => {
    const total = p.tokens[c] + p.bonuses[c];
    return `<span class="bonus-dot counted gem-${c}" title="${GEM_LABEL[c]}: ${p.tokens[c]} gems + ${p.bonuses[c]} bonuses">${total}</span>`;
  }).join('');
  return `<div class="player-chip ${active ? 'active' : ''}">
    <div class="pc-top">
      <span class="pc-name">${esc(p.name)}</span>
      ${pub && pub.isHost ? `<span class="pc-host" title="Host">${icon('crown')}</span>` : ''}
      <span class="pc-points">${p.points}</span>
    </div>
    <div class="pc-power">
      <span class="pc-label">Buying power</span>
      <div class="pc-row">${power}</div>
    </div>
    <div class="pc-detail">
      <span class="pc-label">Coins</span>
      <div class="pc-row">${coinRow}</div>
    </div>
    <div class="pc-detail">
      <span class="pc-label">Bonuses</span>
      <div class="pc-row">${bonuses || '<span class="pc-none">none</span>'}</div>
    </div>
    <div class="pc-meta">${p.cardCount} cards &middot; ${p.reservedCount} reserved &middot; ${p.nobles.length} nobles</div>
  </div>`;
}

function mePanel(g, myTurn, pendingMe) {
  const me = g.you;
  const mePlayer = g.players.find((p) => p.isYou);
  const tokens = GEMS.map((c) => tokenPill(c, me.tokens[c])).join('')
    + tokenPill('gold', me.tokens.gold);
  const bonuses = GEMS.map((c) => bonusPill(c, me.bonuses[c])).join('');
  const buyingPower = GEMS.map((c) => buyingPowerPill(c, me.tokens[c] + me.bonuses[c])).join('');
  const reserved = me.reserved.length
    ? me.reserved.map((c) => cardHTML(c, {
        source: 'reserved', mini: true, disabled: !myTurn || pendingMe,
      })).join('')
    : '<span class="empty-note">None</span>';
  const cards = me.cards.length
    ? me.cards.map((c) => cardHTML(c, { source: 'owned', mini: true, disabled: true })).join('')
    : '<span class="empty-note">None yet</span>';

  return `<div class="me-panel paper">
    <div class="me-head">
      <span class="me-name">${esc(mePlayer.name)}</span>
      <span class="me-points">${me.points}<span class="pts-label">pts</span></span>
    </div>
    <div class="me-section">
      <h3>Tokens <span class="count">${tokenCount(me.tokens)}/10</span></h3>
      <div class="token-row">${tokens}</div>
    </div>
    <div class="me-section">
      <h3>Bonuses</h3>
      <div class="bonus-row">${bonuses}</div>
    </div>
    <div class="me-section">
      <h3>Buying power</h3>
      <div class="bonus-row">${buyingPower}</div>
      <p class="power-note">Gems + card bonuses. Gold can substitute for any color.</p>
    </div>
    <div class="me-actions">
      <button class="btn" data-action="take-gems"
        ${!myTurn || pendingMe ? 'disabled' : ''}>Take gems</button>
      ${myTurn && !pendingMe && me.canPass
        ? '<button class="btn ghost" data-action="pass">Pass</button>'
        : ''}
    </div>
    <div class="me-section">
      <h3>Reserved <span class="count">${me.reserved.length}/3</span></h3>
      <div class="mini-cards">${reserved}</div>
    </div>
    <div class="me-section">
      <h3>Your cards <span class="count">${me.cards.length}</span></h3>
      <div class="mini-cards">${cards}</div>
    </div>
  </div>`;
}

function logPanel(g) {
  const items = [...g.log].reverse().map((line) => `<li>${esc(line)}</li>`).join('');
  return `<div class="log-panel paper">
    <h3>Daybook</h3>
    <ul class="log-list">${items || '<li>No moves yet.</li>'}</ul>
  </div>`;
}

function tokenCount(tokens) {
  return Object.values(tokens).reduce((a, b) => a + b, 0);
}

function tokenPill(color, count) {
  return `<span class="token-pill">
    <span class="token-dot gem-${color}">${count}</span>
    <span>${GEM_LABEL[color]}</span>
  </span>`;
}

function bonusPill(color, count) {
  return `<span class="bonus-pill">
    <span class="bonus-dot gem-${color}"></span>
    <span>${count}</span>
  </span>`;
}

function buyingPowerPill(color, total) {
  return `<span class="bonus-pill power-pill" title="${GEM_LABEL[color]}: gems + bonuses">
    <span class="bonus-dot gem-${color}"></span>
    <span>${total}</span>
  </span>`;
}

/* -------------------------------------------------------------- game over */
function gameOverHTML(g) {
  const rows = (g.scores || []).map((s) => {
    const win = g.winner && g.winner.ids.includes(s.id);
    return `<tr class="${win ? 'win' : ''}">
      <td>${esc(s.name)}</td>
      <td class="num">${s.points}</td>
      <td class="num">${s.cards}</td>
      <td class="num">${s.nobles}</td>
    </tr>`;
  }).join('');
  const names = g.winner ? g.winner.names.join(' & ') : '';
  return `<div class="overlay">
    <div class="overlay-card paper">
      ${sealHTML('S')}
      <p class="eyebrow">The ledger is closed</p>
      <h2>Game over</h2>
      <div class="winner">${esc(names)} wins</div>
      <table class="score-table">
        <thead><tr>
          <th>Player</th><th class="num">Pts</th><th class="num">Cards</th><th class="num">Nobles</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div class="modal-actions">
        ${S.data.you.isHost ? '<button class="btn" data-action="play-again">Play again</button>' : ''}
        ${S.data.you.isHost ? '<button class="btn ghost" data-action="open-lobby">Back to lobby</button>' : ''}
      </div>
    </div>
  </div>`;
}

/* ----------------------------------------------------------------- modals */
function modalHTML() {
  const m = S.modal;
  if (!m) return '';
  if (m.type === 'gems') return gemsModal();
  if (m.type === 'noble') return nobleModal(m);
  if (m.type === 'card') return cardModal(m);
  if (m.type === 'reserve-blind') return reserveBlindModal(m);
  if (m.type === 'stop-server') return stopServerModal();
  return '';
}

function gemsModal() {
  const g = S.data.game;
  const rows = GEMS.map((c) => {
    const count = g.bank[c];
    const selected = S.selection.includes(c);
    return `<div class="gem-choice ${selected ? 'selected' : ''}">
      <span class="gem-dot gem-${c}" aria-hidden="true"></span>
      <span class="gc-name">${GEM_LABEL[c]}</span>
      <span class="gc-count">${count} left</span>
      <button class="gc-btn ${selected ? 'on' : ''}" data-action="toggle-color"
        data-color="${c}" ${count === 0 ? 'disabled' : ''}>${selected ? 'Selected' : 'Select'}</button>
      <button class="gc-btn" data-action="take2" data-color="${c}"
        ${count < 4 ? 'disabled' : ''}>Take 2</button>
    </div>`;
  }).join('');

  const n = S.selection.length;
  return `<div class="modal-backdrop gem-backdrop" data-action="close-modal">
    <div class="modal paper gem-modal" data-stop="1">
      <div class="modal-head">
        <h2>Take gems</h2>
        <button class="icon-btn" data-action="close-modal" aria-label="Close">${icon('close')}</button>
      </div>
      <p class="modal-sub">Select up to 3 different colors, or take 2 of one color.</p>
      <div class="gem-grid">${rows}</div>
      <div class="modal-actions">
        <button class="btn" data-action="confirm-take3" ${n < 1 || n > 3 ? 'disabled' : ''}>
          Take ${n || 0} different
        </button>
        <button class="btn ghost" data-action="close-modal">Cancel</button>
      </div>
    </div>
  </div>`;
}

function nobleModal(m) {
  const options = m.options.map((n) => `
    <div class="gem-choice">
      <div class="noble-choice">${nobleHTML(n)}</div>
      <button class="gc-btn on" data-action="choose-noble" data-noble="${n.id}">Choose</button>
    </div>`).join('');
  return `<div class="modal-backdrop">
    <div class="modal paper" data-stop="1">
      <h2>Choose a noble</h2>
      <p class="modal-sub">You qualify for more than one. Pick one visitor.</p>
      <div class="gem-grid">${options}</div>
    </div>
  </div>`;
}

function cardModal(m) {
  const g = S.data.game;
  const card = m.card;
  const me = g.you;
  const myTurn = g.players[g.turn] && g.players[g.turn].isYou;
  const affordable = canAfford(card, me);
  const canReserve = m.source === 'board' && me.reserved.length < 3;
  const costText = GEMS.filter((c) => card.cost[c] > 0)
    .map((c) => `${card.cost[c]} ${GEM_LABEL[c]}`)
    .join(', ') || 'free';
  const pay = paymentPreview(card, me);
  const payPills = GEMS.filter((c) => pay.tokens[c] > 0)
    .map((c) => `<span class="cost gem-${c}">${pay.tokens[c]}</span>`)
    .join('');
  const goldPill = pay.gold > 0
    ? `<span class="cost gem-gold">${pay.gold}</span>`
    : '';
  const goldNote = pay.gold > 0
    ? (me.tokens.gold >= pay.gold
        ? '<p class="pay-note">Gold covers the shortfall.</p>'
        : `<p class="pay-note">You need ${pay.gold - me.tokens.gold} more gold.</p>`)
    : '';

  return `<div class="modal-backdrop" data-action="close-modal">
    <div class="modal paper" data-stop="1">
      <div class="modal-head">
        <h2>${GEM_LABEL[card.bonus]} card</h2>
        <button class="icon-btn" data-action="close-modal" aria-label="Close">${icon('close')}</button>
      </div>
      <p class="modal-sub">Tier ${roman(card.tier)} &middot; ${card.points} prestige &middot; costs ${esc(costText)}</p>
      <div class="modal-card-wrap">${cardHTML(card, { disabled: true })}</div>
      <div class="pay-preview">
        <h3>You pay</h3>
        <div class="pay-row">
          ${payPills}${goldPill}
          ${pay.total === 0 ? '<span class="empty-note">Nothing — your bonuses cover it.</span>' : ''}
        </div>
        ${pay.gold > 0 ? goldNote : ''}
      </div>
      <div class="modal-actions">
        <button class="btn" data-action="buy" data-card="${card.id}"
          ${!myTurn || !affordable ? 'disabled' : ''}>Buy</button>
        ${m.source === 'board'
          ? `<button class="btn ghost" data-action="reserve" data-card="${card.id}"
              ${!myTurn || !canReserve ? 'disabled' : ''}>Reserve <span class="mini-coin gem-gold">+1</span></button>`
          : ''}
        <button class="btn ghost" data-action="close-modal">Cancel</button>
      </div>
      ${!affordable ? '<p class="hint">You do not have enough gems for this card yet.</p>' : ''}
    </div>
  </div>`;
}

function paymentPreview(card, me) {
  const tokens = {};
  let gold = 0;
  let total = 0;
  for (const c of GEMS) {
    const need = Math.max(0, card.cost[c] - me.bonuses[c]);
    const use = Math.min(need, me.tokens[c]);
    tokens[c] = use;
    gold += need - use;
    total += use;
  }
  return { tokens, gold, total: total + gold };
}

function reserveBlindModal(m) {
  const g = S.data.game;
  const deck = g.decks[String(m.tier)] || 0;
  return `<div class="modal-backdrop" data-action="close-modal">
    <div class="modal paper" data-stop="1">
      <div class="modal-head">
        <h2>Reserve blind?</h2>
        <button class="icon-btn" data-action="close-modal" aria-label="Close">${icon('close')}</button>
      </div>
      <p class="modal-sub">Take the top card of the Tier ${roman(m.tier)} deck without seeing it. You also take 1 gold, if available.</p>
      <p class="hint">${deck} card${deck === 1 ? '' : 's'} left in this deck.</p>
      <div class="modal-actions">
        <button class="btn" data-action="confirm-reserve-blind" data-tier="${m.tier}">Reserve blind</button>
        <button class="btn ghost" data-action="close-modal">Cancel</button>
      </div>
    </div>
  </div>`;
}

function stopServerModal() {
  return `<div class="modal-backdrop" data-action="close-modal">
    <div class="modal paper" data-stop="1">
      <div class="modal-head">
        <h2>Stop the server?</h2>
        <button class="icon-btn" data-action="close-modal" aria-label="Close">${icon('close')}</button>
      </div>
      <p class="modal-sub">Everyone will be disconnected and the current game will end. You'll need to run start.bat again to restart.</p>
      <div class="modal-actions">
        <button class="btn" data-action="confirm-stop-server">Stop server</button>
        <button class="btn ghost" data-action="close-modal">Cancel</button>
      </div>
    </div>
  </div>`;
}

function canAfford(card, me) {
  let gold = me.tokens.gold;
  for (const c of GEMS) {
    const need = Math.max(0, card.cost[c] - me.bonuses[c]);
    if (me.tokens[c] < need) gold -= need - me.tokens[c];
  }
  return gold >= 0;
}
