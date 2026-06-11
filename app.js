/* ═══════════════════════════════════════════
   app.js  –  News Reader
   ═══════════════════════════════════════════ */

// ── State ────────────────────────────────────
let allArticles = [];
let savedIds    = JSON.parse(localStorage.getItem('saved') || '[]');
let catFilter   = 'All';

const CATS = ['All', 'Technology', 'Business', 'Sports', 'Science'];

// ── Tab switching ────────────────────────────
function switchTab(id) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tabbar button').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  const idx = ['home','category','saved','settings'].indexOf(id);
  document.querySelectorAll('.tabbar button')[idx]?.classList.add('active');

  if (id === 'saved')    renderSaved();
  if (id === 'settings') renderSettings();
}

// ── Helpers ──────────────────────────────────
function fmtTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false,
    timeZone: 'Asia/Tokyo'
  });
}

function articleId(a) {
  return btoa(encodeURIComponent(a.url || a.title)).slice(0, 20);
}

function isSaved(a) {
  return savedIds.includes(articleId(a));
}

function toggleSave(a) {
  const id = articleId(a);
  if (savedIds.includes(id)) {
    savedIds = savedIds.filter(x => x !== id);
  } else {
    savedIds.push(id);
  }
  localStorage.setItem('saved', JSON.stringify(savedIds));
}

// ── Card HTML ────────────────────────────────
function cardHTML(a, i) {
  const id    = articleId(a);
  const saved = savedIds.includes(id);
  const delay = Math.min(i * 0.05, 0.35);
  return `
    <div class="card" style="animation-delay:${delay}s" data-id="${id}">
      <div class="card-meta">
        <span class="cat-dot ${a.category}"></span>
        <span class="cat-label">${a.category || ''}</span>
        <span class="card-source">${a.source || ''}</span>
        <button class="card-save" onclick="onSave(event,'${id}')" aria-label="save">
          ${saved ? '⭐' : '☆'}
        </button>
      </div>
      <div class="card-title" onclick="window.open('${a.url}','_blank')">${a.title}</div>
      ${a.description ? `<div class="card-desc">${a.description}</div>` : ''}
      <div class="card-footer">
        <span class="card-time">${fmtTime(a.publishedAt)}</span>
        <a class="read-link" href="${a.url}" target="_blank">Read →</a>
      </div>
    </div>`;
}

// ── Save button handler ──────────────────────
function onSave(e, id) {
  e.stopPropagation();
  const article = allArticles.find(a => articleId(a) === id);
  if (!article) return;
  toggleSave(article);
  // Update star in current card without full re-render
  e.currentTarget.textContent = isSaved(article) ? '⭐' : '☆';
}

// ── Home tab ─────────────────────────────────
function renderHome() {
  const el = document.getElementById('home');
  if (!allArticles.length) return;

  // group by category, preserve order
  const groups = {};
  CATS.slice(1).forEach(c => { groups[c] = []; });
  allArticles.forEach(a => {
    if (groups[a.category]) groups[a.category].push(a);
  });

  let html = '';
  let i = 0;
  for (const [cat, items] of Object.entries(groups)) {
    if (!items.length) continue;
    html += `<div class="section-label">${cat}</div>`;
    items.slice(0, 5).forEach(a => { html += cardHTML(a, i++); });
  }
  el.innerHTML = html;
}

// ── Category tab ─────────────────────────────
function renderCategory() {
  const el = document.getElementById('category');

  // chips
  const chipsHTML = CATS.map(c =>
    `<button class="chip${c === catFilter ? ' active' : ''}" data-cat="${c}" onclick="setCat('${c}')">${c}</button>`
  ).join('');

  const filtered = catFilter === 'All'
    ? allArticles
    : allArticles.filter(a => a.category === catFilter);

  let cardsHTML = '';
  filtered.forEach((a, i) => { cardsHTML += cardHTML(a, i); });

  el.innerHTML = `
    <div class="chips">${chipsHTML}</div>
    ${cardsHTML || '<div class="state-msg">No articles.</div>'}`;
}

function setCat(cat) {
  catFilter = cat;
  renderCategory();
}

// ── Saved tab ────────────────────────────────
function renderSaved() {
  const el = document.getElementById('saved');
  const items = allArticles.filter(a => savedIds.includes(articleId(a)));
  if (!items.length) {
    el.innerHTML = `
      <div class="saved-empty">
        <span class="icon">☆</span>
        Saved articles appear here.<br/>Tap ☆ on any article to save it.
      </div>`;
    return;
  }
  let html = `<div class="section-label">${items.length} saved</div>`;
  items.forEach((a, i) => { html += cardHTML(a, i); });
  el.innerHTML = html;
}

// ── Settings tab ─────────────────────────────
function renderSettings() {
  const el = document.getElementById('settings');
  const darkOn = localStorage.getItem('darkMode') !== 'false';

  el.innerHTML = `
    <p class="settings-label">Display</p>
    <ul class="settings-list">
      <li class="settings-item">
        Dark mode
        <label class="toggle">
          <input type="checkbox" ${darkOn ? 'checked' : ''} onchange="toggleDark(this.checked)"/>
          <span class="toggle-track"></span>
          <span class="toggle-thumb"></span>
        </label>
      </li>
    </ul>
    <p class="settings-label">Info</p>
    <ul class="settings-list">
      <li class="settings-item">
        Last updated
        <span style="color:var(--muted);font-size:0.8rem" id="settingsUpdated">—</span>
      </li>
      <li class="settings-item">
        Articles loaded
        <span style="color:var(--muted);font-size:0.8rem">${allArticles.length}</span>
      </li>
    </ul>`;
}

function toggleDark(on) {
  localStorage.setItem('darkMode', on);
  // extend later if you add a light theme
}

// ── Load news.json ────────────────────────────
async function loadNews() {
  document.getElementById('home').innerHTML = `
    <div class="state-msg"><div class="spinner"></div>Loading news…</div>`;

  try {
    const res = await fetch(`news.json?v=${Date.now()}`);
    if (!res.ok) throw new Error('not found');
    const data = await res.json();
    allArticles = data.articles || [];

    // Header timestamp
    if (data.updatedAt) {
      const t = new Date(data.updatedAt).toLocaleString('en-US', {
        month:'short', day:'numeric',
        hour:'2-digit', minute:'2-digit', hour12:false,
        timeZone:'Asia/Tokyo'
      });
      document.querySelector('.header-right').textContent = `Updated ${t} JST`;
      // Settings panel (if open)
      const el = document.getElementById('settingsUpdated');
      if (el) el.textContent = t;
    }

    renderHome();
    renderCategory();
  } catch {
    document.getElementById('home').innerHTML = `
      <div class="state-msg">
        Could not load news.json.<br/>
        Run the GitHub Action once to generate it.
      </div>`;
  }
}

// ── Init ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Mark first tab button active
  document.querySelectorAll('.tabbar button')[0]?.classList.add('active');

  // Add label text under icons
  const labels = ['Home', 'Browse', 'Saved', 'Settings'];
  document.querySelectorAll('.tabbar button').forEach((btn, i) => {
    btn.innerHTML += `<span>${labels[i]}</span>`;
  });

  // Add header right slot
  const h = document.querySelector('.header');
  h.insertAdjacentHTML('beforeend', '<div class="header-right"></div>');

  loadNews();
});
