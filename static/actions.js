'use strict';

/* --------------------------------------------------------------- requests */
async function sendAction(action) {
  if (S.busy) return;
  S.busy = true;
  try {
    await api('/api/action', { token: S.token, action });
    S.modal = null;
    S.selection = [];
    render();
  } catch (err) {
    toast(err.message);
  } finally {
    S.busy = false;
  }
}

async function post(path) {
  if (S.busy) return;
  S.busy = true;
  try {
    await api(path, { token: S.token });
    S.modal = null;
    render();
  } catch (err) {
    toast(err.message);
  } finally {
    S.busy = false;
  }
}

async function stopServer() {
  try {
    await api('/api/shutdown', { token: S.token });
  } catch (err) {
    /* the server may close the connection before responding */
  }
  S.serverStopped = true;
  S.data = null;
  S.modal = null;
  disconnect();
  render();
}

/* ---------------------------------------------------------------- helpers */
function toggleColor(color) {
  const i = S.selection.indexOf(color);
  if (i >= 0) {
    S.selection.splice(i, 1);
  } else if (S.selection.length < 3) {
    S.selection.push(color);
  } else {
    toast('You can select at most 3 colors.');
  }
  render();
}

function openCard(cardId, source) {
  const g = S.data.game;
  let card = null;
  if (source === 'reserved') {
    card = g.you.reserved.find((c) => c.id === cardId);
  } else {
    for (const tier of ['1', '2', '3']) {
      card = (g.board[tier] || []).find((c) => c && c.id === cardId);
      if (card) break;
    }
  }
  if (!card) return;
  S.modal = { type: 'card', card, source };
  render();
}

async function copyLink() {
  const url = S.config.lanUrl || location.origin;
  try {
    await navigator.clipboard.writeText(url);
    toast('Link copied. Share it with your group.');
  } catch (err) {
    const input = document.createElement('input');
    input.value = url;
    document.body.appendChild(input);
    input.select();
    try {
      document.execCommand('copy');
      toast('Link copied.');
    } catch (e) {
      toast(url);
    }
    document.body.removeChild(input);
  }
}

async function leaveGame() {
  try {
    await api('/api/leave', { token: S.token });
  } catch (err) {
    /* ignore */
  }
  localStorage.removeItem('splendor.token');
  S.token = '';
  S.data = null;
  S.modal = null;
  disconnect();
  render();
}

/* ---------------------------------------------------------------- events */
document.addEventListener('submit', (e) => {
  if (e.target.id === 'join-form') {
    e.preventDefault();
    doJoin($('#name-input').value);
  }
});

document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-action]');
  if (!el) return;
  const action = el.dataset.action;
  if (S.busy && action !== 'close-modal' && action !== 'toggle-sound') return;

  // Only ignore a backdrop click that lands inside the modal body.
  if (action === 'close-modal' && el.classList.contains('modal-backdrop')
      && e.target.closest('[data-stop]')) return;

  switch (action) {
    case 'copy-link':
      copyLink();
      break;
    case 'start':
      post('/api/start');
      break;
    case 'leave':
      leaveGame();
      break;
    case 'take-gems':
      S.selection = [];
      S.modal = { type: 'gems' };
      render();
      break;
    case 'toggle-color':
      toggleColor(el.dataset.color);
      break;
    case 'take2':
      sendAction({ type: 'take2', color: el.dataset.color });
      break;
    case 'pass':
      sendAction({ type: 'pass' });
      break;
    case 'confirm-take3':
      if (S.selection.length >= 1) {
        sendAction({ type: 'take3', colors: [...S.selection] });
      }
      break;
    case 'open-card':
      openCard(Number(el.dataset.card), el.dataset.source);
      break;
    case 'buy':
      sendAction({ type: 'buy', card: Number(el.dataset.card) });
      break;
    case 'reserve':
      sendAction({ type: 'reserve', card: Number(el.dataset.card) });
      break;
    case 'reserve-blind':
      S.modal = { type: 'reserve-blind', tier: Number(el.dataset.tier) };
      render();
      break;
    case 'confirm-reserve-blind':
      sendAction({ type: 'reserve', tier: Number(el.dataset.tier) });
      break;
    case 'choose-noble':
      sendAction({ type: 'choose_noble', noble: Number(el.dataset.noble) });
      break;
    case 'skip':
      post('/api/skip');
      break;
    case 'stop-server':
      S.modal = { type: 'stop-server' };
      render();
      break;
    case 'confirm-stop-server':
      stopServer();
      break;
    case 'toggle-sound':
      S.soundOn = !S.soundOn;
      localStorage.setItem('splendor.sound', S.soundOn ? 'on' : 'off');
      if (S.soundOn) playChime();
      render();
      break;
    case 'toggle-notify':
      S.notifyOn = !S.notifyOn;
      localStorage.setItem('splendor.notify', S.notifyOn ? 'on' : 'off');
      if (S.notifyOn) {
        requestNotifyPermission().then((ok) => {
          if (!ok) toast('Notifications are blocked in your browser settings.');
        });
      }
      render();
      break;
    case 'play-again':
      post('/api/play-again');
      break;
    case 'open-lobby':
      post('/api/open-lobby');
      break;
    case 'close-modal':
      S.modal = null;
      S.selection = [];
      render();
      break;
    default:
      break;
  }
});
