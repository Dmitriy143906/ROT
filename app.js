const menu = document.querySelector('.menu');
const navLinks = document.querySelector('.nav-links');
menu?.addEventListener('click', () => navLinks.classList.toggle('open'));
document.querySelectorAll('.nav-links a').forEach(a => a.addEventListener('click', () => navLinks.classList.remove('open')));

const form = document.getElementById('applicationForm');
const statusEl = document.getElementById('formStatus');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusEl.className = 'form-status';
  statusEl.textContent = 'Отправляем заявку…';

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  payload.age = Number(payload.age);
  payload.rust_hours = Number(payload.rust_hours);

  try {
    const response = await fetch('/api/applications', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Не удалось отправить заявку');

    form.reset();
    statusEl.className = 'form-status success';
    statusEl.textContent = `✓ Заявка #${data.id} отправлена. Командование RØT свяжется с тобой.`;
  } catch (error) {
    statusEl.className = 'form-status error';
    statusEl.textContent = 'Ошибка отправки. Проверь, что сервер сайта запущен, и попробуй снова.';
  }
});
