const loginView = document.querySelector('#loginView');
const dashboardView = document.querySelector('#dashboardView');
const loginForm = document.querySelector('#loginForm');
const loginStatus = document.querySelector('#loginStatus');
const applicationsEl = document.querySelector('#applications');
const listStatus = document.querySelector('#listStatus');
const statsEl = document.querySelector('#stats');
const adminUser = document.querySelector('#adminUser');
const searchInput = document.querySelector('#searchInput');
const refreshButton = document.querySelector('#refreshButton');
const logoutButton = document.querySelector('#logoutButton');
const detailDialog = document.querySelector('#detailDialog');
const detailContent = document.querySelector('#detailContent');
const closeDialog = document.querySelector('#closeDialog');

let currentFilter = 'all';
let currentItems = [];
let searchTimer;

const labels = {
  new: 'Новая',
  accepted: 'Принята',
  rejected: 'Отклонена',
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString('ru-RU');
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  let data = {};
  try { data = await response.json(); } catch (_) {}

  if (!response.ok) {
    const error = new Error(data.detail || 'Ошибка запроса');
    error.status = response.status;
    throw error;
  }
  return data;
}

async function checkSession() {
  try {
    const me = await api('/api/admin/me');
    adminUser.textContent = me.username;
    showDashboard();
    await Promise.all([loadStats(), loadApplications()]);
  } catch (_) {
    showLogin();
  }
}

function showLogin() {
  loginView.classList.remove('hidden');
  dashboardView.classList.add('hidden');
}

function showDashboard() {
  loginView.classList.add('hidden');
  dashboardView.classList.remove('hidden');
}

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  loginStatus.textContent = 'Проверяем доступ...';
  const fd = new FormData(loginForm);

  try {
    const result = await api('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({
        username: fd.get('username'),
        password: fd.get('password'),
      }),
    });
    adminUser.textContent = result.username;
    loginStatus.textContent = '';
    loginForm.reset();
    showDashboard();
    await Promise.all([loadStats(), loadApplications()]);
  } catch (error) {
    loginStatus.textContent = error.message;
  }
});

logoutButton.addEventListener('click', async () => {
  try { await api('/api/admin/logout', { method: 'POST' }); } catch (_) {}
  showLogin();
});

async function loadStats() {
  const s = await api('/api/admin/stats');
  statsEl.innerHTML = `
    <article><span>ВСЕГО</span><b>${s.total}</b></article>
    <article><span>НОВЫЕ</span><b>${s.new}</b></article>
    <article><span>ПРИНЯТЫЕ</span><b>${s.accepted}</b></article>
    <article><span>ОТКЛОНЁННЫЕ</span><b>${s.rejected}</b></article>
  `;
}

async function loadApplications() {
  listStatus.textContent = 'Загрузка заявок...';
  applicationsEl.innerHTML = '';

  const params = new URLSearchParams({ status: currentFilter });
  const q = searchInput.value.trim();
  if (q) params.set('q', q);

  try {
    const data = await api(`/api/admin/applications?${params}`);
    currentItems = data.items;
    renderApplications();
    listStatus.textContent = currentItems.length ? '' : 'Заявок по этому фильтру нет.';
  } catch (error) {
    if (error.status === 401) return showLogin();
    listStatus.textContent = error.message;
  }
}

function renderApplications() {
  applicationsEl.innerHTML = currentItems.map((item) => `
    <article class="application-card" data-id="${item.id}">
      <div class="card-head">
        <div>
          <span class="id">#${item.id}</span>
          <h2>${escapeHtml(item.discord)}</h2>
        </div>
        <span class="badge ${item.status}">${labels[item.status] || item.status}</span>
      </div>
      <div class="meta">
        <span>${escapeHtml(item.role)}</span>
        <span>${item.rust_hours} ч.</span>
        <span>${item.age} лет</span>
        <span>${escapeHtml(item.timezone)}</span>
      </div>
      <p>${escapeHtml(item.about).slice(0, 180)}${item.about.length > 180 ? '…' : ''}</p>
      <div class="card-foot">
        <time>${formatDate(item.created_at)}</time>
        <button class="open-button" data-open="${item.id}">Открыть</button>
      </div>
    </article>
  `).join('');

  document.querySelectorAll('[data-open]').forEach((button) => {
    button.addEventListener('click', () => openDetail(Number(button.dataset.open)));
  });
}

function openDetail(id) {
  const item = currentItems.find((x) => x.id === id);
  if (!item) return;

  detailContent.innerHTML = `
    <div class="detail-head">
      <div>
        <div class="kicker">ЗАЯВКА #${item.id}</div>
        <h2>${escapeHtml(item.discord)}</h2>
      </div>
      <span class="badge ${item.status}">${labels[item.status] || item.status}</span>
    </div>
    <div class="detail-grid">
      <div><small>Возраст</small><b>${item.age}</b></div>
      <div><small>Часы Rust</small><b>${item.rust_hours}</b></div>
      <div><small>Роль</small><b>${escapeHtml(item.role)}</b></div>
      <div><small>Часовой пояс</small><b>${escapeHtml(item.timezone)}</b></div>
      <div class="wide"><small>Онлайн</small><b>${escapeHtml(item.online)}</b></div>
      <div class="wide"><small>Steam</small><a href="${escapeHtml(item.steam)}" target="_blank" rel="noreferrer">${escapeHtml(item.steam)}</a></div>
    </div>
    <div class="about-box"><small>О себе</small><p>${escapeHtml(item.about)}</p></div>
    <div class="dates">Создана: ${formatDate(item.created_at)}${item.updated_at ? ` • Обновлена: ${formatDate(item.updated_at)}` : ''}</div>
    <div class="actions">
      <button class="accept" data-status="accepted">✓ Принять</button>
      <button class="reset" data-status="new">↺ Вернуть в новые</button>
      <button class="reject" data-status="rejected">✕ Отклонить</button>
      <button class="delete" id="deleteApplication">Удалить</button>
    </div>
  `;

  detailContent.querySelectorAll('[data-status]').forEach((button) => {
    button.addEventListener('click', async () => {
      await changeStatus(item.id, button.dataset.status);
      detailDialog.close();
    });
  });

  detailContent.querySelector('#deleteApplication').addEventListener('click', async () => {
    if (!confirm(`Удалить заявку #${item.id}? Это действие нельзя отменить.`)) return;
    await deleteApplication(item.id);
    detailDialog.close();
  });

  detailDialog.showModal();
}

async function changeStatus(id, status) {
  await api(`/api/admin/applications/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
  await Promise.all([loadStats(), loadApplications()]);
}

async function deleteApplication(id) {
  await api(`/api/admin/applications/${id}`, { method: 'DELETE' });
  await Promise.all([loadStats(), loadApplications()]);
}

document.querySelectorAll('.nav-button').forEach((button) => {
  button.addEventListener('click', async () => {
    document.querySelectorAll('.nav-button').forEach((x) => x.classList.remove('active'));
    button.classList.add('active');
    currentFilter = button.dataset.filter;
    await loadApplications();
  });
});

searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadApplications, 250);
});

refreshButton.addEventListener('click', async () => {
  await Promise.all([loadStats(), loadApplications()]);
});

closeDialog.addEventListener('click', () => detailDialog.close());

detailDialog.addEventListener('click', (event) => {
  if (event.target === detailDialog) detailDialog.close();
});

checkSession();
