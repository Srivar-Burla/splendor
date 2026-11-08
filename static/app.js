'use strict';

/* ------------------------------------------------------------------ state */
const GEMS = ['diamond', 'sapphire', 'emerald', 'ruby', 'onyx'];
const GEM_LABEL = {
  diamond: 'Diamond',
  sapphire: 'Sapphire',
  emerald: 'Emerald',
  ruby: 'Ruby',
  onyx: 'Onyx',
  gold: 'Gold',
};

const S = {
  token: localStorage.getItem('splendor.token') || '',
  name: localStorage.getItem('splendor.name') || '',
  data: null,
  config: { lanUrl: location.origin },
  es: null,
  selection: [],
  modal: null,
  toastTimer: null,
  joinError: '',
  lockedOut: false,
  soundOn: localStorage.getItem('splendor.sound') !== 'off',
  notifyOn: localStorage.getItem('splendor.notify') !== 'off',
  lastTurn: null,
  busy: false,
  serverStopped: false,
};

/* ---------------------------------------------------------------- helpers */
const $ = (sel, root = document) => root.querySelector(sel);

function esc(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[ch]));
}

function toast(message) {
  const el = $('#toast');
  if (!el) return;
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(S.toastTimer);
  S.toastTimer = setTimeout(() => el.classList.remove('show'), 3400);
}

let audioCtx = null;

function initAudio() {
  if (audioCtx) return;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (Ctx) audioCtx = new Ctx();
  } catch (err) {
    audioCtx = null;
  }
}

function playChime() {
  if (!S.soundOn) return;
  initAudio();
  if (!audioCtx) return;
  try {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const now = audioCtx.currentTime;
    [660, 880].forEach((freq, i) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.value = freq;
      const start = now + i * 0.12;
      gain.gain.setValueAtTime(0.0001, start);
      gain.gain.exponentialRampToValueAtTime(0.12, start + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.28);
      osc.connect(gain).connect(audioCtx.destination);
      osc.start(start);
      osc.stop(start + 0.32);
    });
  } catch (err) {
    /* audio is best-effort */
  }
}

function notifyTurn() {
  toast('Your turn — choose an action.');
  playChime();
  showTurnNotification();
}

async function requestNotifyPermission() {
  if (!('Notification' in window)) return false;
  if (Notification.permission === 'granted') return true;
  if (Notification.permission === 'denied') return false;
  try {
    const result = await Notification.requestPermission();
    return result === 'granted';
  } catch (err) {
    return false;
  }
}

function showTurnNotification() {
  if (!S.notifyOn) return;
  if (!('Notification' in window) || Notification.permission !== 'granted') return;
  try {
    const n = new Notification('Splendor — your turn', {
      body: 'Choose an action.',
      tag: 'splendor-turn',
      renotify: true,
    });
    n.onclick = () => {
      window.focus();
      n.close();
    };
  } catch (err) {
    /* notifications are best-effort */
  }
}

async function refreshState() {
  if (!S.token) return;
  try {
    const r = await api('/api/state?token=' + encodeURIComponent(S.token));
    S.data = r.state;
    render();
  } catch (err) {
    /* ignore; SSE will recover */
  }
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  let json = {};
  try {
    json = await res.json();
  } catch (err) {
    /* non-JSON response */
  }
  if (!res.ok) throw new Error(json.error || `Request failed (${res.status})`);
  return json;
}

/* ------------------------------------------------------------------- boot */
async function init() {
  try {
    S.config = await api('/api/config');
  } catch (err) {
    /* keep default */
  }

  if (S.token) {
    try {
      const r = await api('/api/join', { token: S.token, name: S.name });
      S.token = r.token;
      localStorage.setItem('splendor.token', S.token);
      S.data = r.state;
      connect();
      render();
      return;
    } catch (err) {
      S.joinError = err.message;
      if (/already started/i.test(err.message)) S.lockedOut = true;
      localStorage.removeItem('splendor.token');
      S.token = '';
    }
  }
  render();
}

async function doJoin(name) {
  name = (name || '').trim();
  if (!name) {
    toast('Enter your name first.');
    return;
  }
  try {
    const r = await api('/api/join', { name });
    S.token = r.token;
    S.name = name;
    localStorage.setItem('splendor.token', S.token);
    localStorage.setItem('splendor.name', S.name);
    S.data = r.state;
    S.joinError = '';
    S.lockedOut = false;
    connect();
    render();
  } catch (err) {
    S.joinError = err.message;
    if (/already started/i.test(err.message)) S.lockedOut = true;
    render();
    toast(err.message);
  }
}

/* --------------------------------------------------------------- realtime */
function connect() {
  disconnect();
  if (!S.token) return;
  const es = new EventSource('/api/events?token=' + encodeURIComponent(S.token));
  S.es = es;

  es.onopen = () => document.body.classList.remove('reconnecting');

  es.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'state') {
        const prevTurn = S.lastTurn;
        S.data = msg.state;
        const g = msg.state.game;
        if (g && msg.state.phase === 'playing') {
          const myIndex = g.players.findIndex((p) => p.isYou);
          S.lastTurn = g.turn;
          if (g.turn === myIndex && prevTurn !== myIndex) notifyTurn();
        } else {
          S.lastTurn = null;
        }
        render();
      }
    } catch (err) {
      /* ignore malformed frame */
    }
  };

  es.onerror = () => {
    document.body.classList.add('reconnecting');
    // EventSource reconnects on its own.
  };
}

function disconnect() {
  if (S.es) {
    S.es.close();
    S.es = null;
  }
}

document.addEventListener('DOMContentLoaded', init);

document.addEventListener('click', () => {
  initAudio();
  if (S.notifyOn) requestNotifyPermission();
}, { once: true });

document.addEventListener('visibilitychange', () => {
  if (!document.hidden && S.token) {
    refreshState();
    if (!S.es || S.es.readyState === EventSource.CLOSED) connect();
  }
});

setInterval(() => {
  if (!document.hidden && S.token) refreshState();
}, 30000);
