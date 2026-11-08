'use strict';

/* --------------------------------------------------------------- helpers */
function roman(n) {
  return ['', 'I', 'II', 'III'][n] || String(n);
}

function sealHTML(label = 'S') {
  return `<span class="seal" aria-hidden="true"><span>${label}</span></span>`;
}

function icon(name) {
  const paths = {
    crown: '<path d="M3 8l4 3 5-6 5 6 4-3-2 10H5L3 8z"/><path d="M5 18h14"/>',
    copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    gem: '<path d="M6 3h12l3 6-9 12L3 9l3-6z"/><path d="M3 9h18M9 3l3 18M15 3l-3 18"/>',
    take3: '<circle cx="7" cy="12" r="2.4"/><circle cx="12" cy="12" r="2.4"/><circle cx="17" cy="12" r="2.4"/>',
    take2: '<circle cx="9" cy="12" r="3"/><circle cx="15" cy="12" r="3"/>',
    reserve: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 3v6l3-2 3 2V3"/>',
    buy: '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><circle cx="12" cy="14" r="2"/>',
    sound: '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16 9a4 4 0 0 1 0 6"/>',
    mute: '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M17 9l4 6M21 9l-4 6"/>',
    bell: '<path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    'bell-off': '<path d="M6 9a6 6 0 0 1 9.3-5"/><path d="M18 9c0 5 2 6 2 6H8"/><path d="M10 20a2 2 0 0 0 4 0"/><path d="M3 3l18 18"/>',
  };
  return `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true">${paths[name] || ''}</svg>`;
}

/* --------------------------------------------------------------- dispatch */
function render() {
  const app = $('#app');
  if (S.serverStopped) {
    app.innerHTML = `<div class="join-wrap">
      <div class="calling-card paper">
        ${sealHTML('S')}
        <h1>Server stopped</h1>
        <p class="sub">You can close this tab. Run start.bat to play again.</p>
      </div>
    </div>`;
    return;
  }
  if (!S.data) {
    app.innerHTML = joinScreen();
    return;
  }
  if (S.data.phase === 'lobby') {
    app.innerHTML = lobbyScreen();
    return;
  }
  const g = S.data.game;
  if (g && g.pendingNoble && g.players[g.pendingNoble.player]
      && g.players[g.pendingNoble.player].isYou) {
    if (!S.modal || S.modal.type !== 'noble') {
      S.modal = { type: 'noble', options: g.pendingNoble.options };
    }
  }
  app.innerHTML = gameScreen();
  if (S.data.game && S.data.game.finished) {
    app.insertAdjacentHTML('beforeend', gameOverHTML(S.data.game));
  }
  if (S.modal) {
    app.insertAdjacentHTML('beforeend', modalHTML());
  }
}

/* ------------------------------------------------------------ join screen */
function joinScreen() {
  if (S.lockedOut) {
    return `<div class="join-wrap">
      <div class="calling-card paper">
        ${sealHTML('S')}
        <p class="eyebrow">The guild is in session</p>
        <h1>Splendor</h1>
        <p class="sub">This game is already in progress.</p>
        <p class="error">${esc(S.joinError)}</p>
        <p class="hint">Ask the host to reopen the lobby when the current game ends.</p>
      </div>
    </div>`;
  }
  return `<div class="join-wrap">
    <div class="calling-card paper">
      ${sealHTML('S')}
      <p class="eyebrow">A game of gems &amp; influence</p>
      <h1>Splendor</h1>
      <p class="sub">Take a seat at the merchant&rsquo;s table.</p>
      <form class="join-form" id="join-form">
        <label class="field">
          <span>Your name</span>
          <input id="name-input" name="name" maxlength="20" placeholder="e.g. Lorenzo&hellip;"
            autocomplete="off" value="${esc(S.name)}" />
        </label>
        <button type="submit" class="btn">Take a seat</button>
      </form>
      <p class="error">${esc(S.joinError)}</p>
      <p class="hint">Everyone must be on the same Wi-Fi as the host laptop.</p>
    </div>
  </div>`;
}

/* ----------------------------------------------------------- lobby screen */
function lobbyScreen() {
  const d = S.data;
  const url = S.config.lanUrl || location.origin;
  const players = d.players.map((p) => `
    <li>
      <span class="dot ${p.connected ? '' : 'off'}"></span>
      <span class="pl-name">${esc(p.name)}</span>
      ${p.isHost ? `<span class="crown" title="Host">${icon('crown')}</span>` : ''}
      ${p.id === d.you.id ? '<span class="you">you</span>' : ''}
    </li>`).join('');

  return `<div class="lobby">
    <div class="ledger-sheet paper">
      ${sealHTML('S')}
      <p class="eyebrow">The merchant&rsquo;s table</p>
      <h1>Splendor</h1>
      <p class="sub">Gather your guild. The game begins when the host says so.</p>

      <div class="share">
        <div class="share-label">Share this link</div>
        <div class="share-row">
          <div class="share-url" id="share-url">${esc(url)}</div>
          <button class="btn ghost" data-action="copy-link" aria-label="Copy invite link">
            ${icon('copy')}<span>Copy</span>
          </button>
        </div>
      </div>

      <div class="players-box">
        <h2>At the table <span class="count">${d.players.length}/4</span></h2>
        <ul class="player-list">${players}</ul>
      </div>

      <div class="lobby-actions">
        ${d.canStart
          ? '<button class="btn" data-action="start">Start game</button>'
          : `<span class="waiting">${d.you.isHost
              ? 'Waiting for at least one more player&hellip;'
              : 'Waiting for the host to start&hellip;'}</span>`}
        <button class="btn ghost" data-action="leave">Leave</button>
        ${d.you.isHost ? '<button class="btn ghost" data-action="stop-server">Stop server</button>' : ''}
      </div>
      <p class="hint">Once the game starts, new players can no longer join.</p>
    </div>

    <div class="rules-sheet paper">
      <div class="rules-head">
        <h2>How to play</h2>
        <span class="rules-goal">First to 15 prestige wins</span>
      </div>
      <p class="rules-intro">On your turn, do one of these four things:</p>
      <div class="rules-grid">
        <div class="rule">
          <span class="rule-icon">${icon('take3')}</span>
          <div>
            <h3>Take 3 gems</h3>
            <p>Three tokens of different colors.</p>
          </div>
        </div>
        <div class="rule">
          <span class="rule-icon">${icon('take2')}</span>
          <div>
            <h3>Take 2 gems</h3>
            <p>Two of the same color, only if the bank has 4 or more.</p>
          </div>
        </div>
        <div class="rule">
          <span class="rule-icon">${icon('reserve')}</span>
          <div>
            <h3>Reserve a card</h3>
            <p>Take a face-up card or blind from a deck, plus 1 gold. Max 3.</p>
          </div>
        </div>
        <div class="rule">
          <span class="rule-icon">${icon('buy')}</span>
          <div>
            <h3>Buy a card</h3>
            <p>Pay its cost with tokens and your permanent bonuses.</p>
          </div>
        </div>
      </div>
      <div class="rules-notes">
        <h3>Good to know</h3>
        <ul>
          <li>Cards give a permanent gem bonus and sometimes prestige.</li>
          <li>Gold is wild and can replace any gem.</li>
          <li>Nobles are worth 3 prestige and visit when your bonuses qualify.</li>
          <li>You can hold at most 10 tokens.</li>
          <li>At 15 prestige the round finishes, then the highest score wins.</li>
        </ul>
      </div>
    </div>
  </div>`;
}

/* ------------------------------------------------------------ game screen */
function gameScreen() {
  const d = S.data;
  const g = d.game;
  const myIndex = g.players.findIndex((p) => p.isYou);
  const myTurn = g.turn === myIndex;
  const current = g.players[g.turn];
  const pendingMe = g.pendingNoble && g.pendingNoble.player === myIndex;

  let turnText;
  if (g.finished) turnText = 'Game over';
  else if (pendingMe) turnText = 'Choose a noble';
  else if (myTurn) turnText = 'Your turn';
  else turnText = `Waiting for ${current.name}`;

  const opponents = g.players
    .filter((p) => !p.isYou)
    .map((p) => playerChip(p, g, d))
    .join('');

  return `<div class="game">
    <div class="reconnect-bar">Reconnecting&hellip;</div>
    <header class="topbar">
      <span class="brand">${sealHTML('S')}<span class="brand-word">Splendor</span></span>
      <span class="turn-pill ${myTurn && !g.finished ? 'mine' : ''}">${esc(turnText)}</span>
      ${g.finalRound && !g.finished ? '<span class="final-pill">Final round</span>' : ''}
      <span class="spacer"></span>
      ${d.you.isHost ? '<button class="btn ghost" data-action="stop-server">Stop server</button>' : ''}
      <button class="icon-btn topbar-icon" data-action="toggle-sound"
        aria-label="${S.soundOn ? 'Mute turn sound' : 'Enable turn sound'}">
        ${icon(S.soundOn ? 'sound' : 'mute')}
      </button>
      <button class="icon-btn topbar-icon" data-action="toggle-notify"
        aria-label="${S.notifyOn ? 'Disable turn notifications' : 'Enable turn notifications'}">
        ${icon(S.notifyOn ? 'bell' : 'bell-off')}
      </button>
      ${skipButton(d, g)}
    </header>
    <div class="opponents">${opponents || '<span class="empty-note">No opponents.</span>'}</div>
    <div class="layout">
      <main class="table" id="main">
        ${noblesRow(g)}
        ${cardRows(g, myTurn && !g.finished && !pendingMe)}
        ${bankRow(g)}
      </main>
      <aside class="side">
        ${mePanel(g, myTurn, pendingMe)}
        ${logPanel(g)}
      </aside>
    </div>
  </div>`;
}

function skipButton(d, g) {
  if (g.finished) return '';
  const current = g.players[g.turn];
  const pub = d.players.find((p) => p.id === current.id);
  if (!d.you.isHost || !pub || pub.connected) return '';
  return `<button class="btn ghost" data-action="skip">Skip ${esc(current.name)}&rsquo;s turn</button>`;
}

/* --------------------------------------------------------------- sections */
function noblesRow(g) {
  return `<section class="nobles">
    <div class="section-head">
      <h2>Noble patrons</h2>
      <span class="section-note">3 prestige each</span>
    </div>
    <div class="noble-row">
      ${g.nobles.map(nobleHTML).join('') || '<span class="empty-note">All nobles have been claimed.</span>'}
    </div>
  </section>`;
}

function cardRows(g, canAct) {
  return `<section class="rows">
    ${[3, 2, 1].map((tier) => {
      const cards = g.board[String(tier)] || [];
      const deck = g.decks[String(tier)] || 0;
      return `<div class="row">
        <div class="row-label"><span class="tier-mark">${roman(tier)}</span><span class="tier-word">Tier</span></div>
        <div class="shelf">
          ${cards.map((c) => cardHTML(c, { source: 'board', disabled: !canAct })).join('')}
          <button class="deck-btn" data-action="reserve-blind" data-tier="${tier}"
            ${!canAct || deck === 0 ? 'disabled' : ''}
            aria-label="Reserve a card blind from tier ${tier}">
            <span class="deck-stack" aria-hidden="true"></span>
            <span class="deck-count">${deck}</span>
            <span class="deck-label">Reserve blind</span>
          </button>
        </div>
      </div>`;
    }).join('')}
  </section>`;
}

function bankRow(g) {
  return `<section class="bank">
    <div class="section-head">
      <h2>The bank</h2>
      <span class="section-note">Gold is wild</span>
    </div>
    <div class="coin-row">
      ${GEMS.map((c) => bankToken(c, g.bank[c])).join('')}
      ${bankToken('gold', g.bank.gold)}
    </div>
  </section>`;
}

function bankToken(color, count) {
  return `<div class="bank-token ${count === 0 ? 'empty' : ''}">
    <span class="coin gem-${color}"><span class="bt-count">${count}</span></span>
    <span class="bt-label">${GEM_LABEL[color]}</span>
  </div>`;
}
