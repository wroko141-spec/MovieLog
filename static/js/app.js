// MovieLog - клиентская часть. Данные выводятся через textContent (защита от XSS).
(function () {
  'use strict';

  // CSRF-токен из cookie для запросов к API
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '=([^;]+)');
    return m ? decodeURIComponent(m[2]) : '';
  }

  async function api(url, method, data) {
    const res = await fetch(url, {
      method: method || 'GET',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      credentials: 'same-origin',
      body: data ? JSON.stringify(data) : undefined,
    });
    if (res.status === 204) return null;
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = json.detail || Object.values(json).flat().join(' ') || 'Ошибка ' + res.status;
      throw new Error(msg);
    }
    return json;
  }

  const toastEl = document.querySelector('[data-toast]');
  function toast(text, isError) {
    if (!toastEl) return;
    toastEl.textContent = text;
    toastEl.classList.toggle('is-error', !!isError);
    toastEl.hidden = false;
    clearTimeout(toast.t);
    toast.t = setTimeout(() => { toastEl.hidden = true; }, 3000);
  }

  // Меню на телефоне
  const burger = document.querySelector('[data-burger]');
  const nav = document.querySelector('[data-nav]');
  if (burger && nav) burger.addEventListener('click', () => nav.classList.toggle('is-open'));

  // Форма фильма: добавить / изменить запись дневника
  const form = document.querySelector('[data-entry-form]');
  if (form) {
    const syncStatus = () => form.classList.toggle('is-want', form.status.value === 'want');
    form.querySelectorAll('input[name=status]').forEach((r) => r.addEventListener('change', syncStatus));
    syncStatus();

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const status = form.status.value;
      const data = { status: status, review: '', rating: null, watched_at: null };
      if (status === 'watched') {
        data.rating = form.rating.value ? Number(form.rating.value) : null;
        data.watched_at = form.watched_at.value || null;
        data.review = form.review.value.trim();
      }
      const id = form.dataset.entry;
      try {
        if (id) {
          await api('/api/diary/' + id + '/', 'PATCH', data);
          toast('Сохранено');
        } else {
          data.movie_id = Number(form.dataset.movie);
          const created = await api('/api/diary/', 'POST', data);
          form.dataset.entry = created.id;
          toast('Фильм добавлен в дневник');
          setTimeout(() => location.reload(), 600);
        }
      } catch (err) { toast(err.message, true); }
    });

    const del = form.querySelector('[data-delete]');
    if (del) del.addEventListener('click', async () => {
      if (!confirm('Убрать фильм из дневника?')) return;
      try { await api('/api/diary/' + form.dataset.entry + '/', 'DELETE'); location.reload(); }
      catch (err) { toast(err.message, true); }
    });
  }

  // Дневник: отметить просмотренным и удалить
  document.querySelectorAll('[data-mark-watched]').forEach((btn) => btn.addEventListener('click', async () => {
    const today = new Date().toISOString().slice(0, 10);
    try { await api('/api/diary/' + btn.dataset.markWatched + '/', 'PATCH', { status: 'watched', watched_at: today }); location.reload(); }
    catch (err) { toast(err.message, true); }
  }));
  document.querySelectorAll('[data-remove]').forEach((btn) => btn.addEventListener('click', async () => {
    if (!confirm('Удалить запись из дневника?')) return;
    try {
      await api('/api/diary/' + btn.dataset.remove + '/', 'DELETE');
      btn.closest('[data-entry-row]').remove();
      toast('Запись удалена');
    } catch (err) { toast(err.message, true); }
  }));

  // Подбор ИИ
  const aiForm = document.querySelector('[data-ai-form]');
  if (aiForm) {
    const result = document.querySelector('[data-ai-result]');
    const history = document.querySelector('[data-ai-history]');
    document.querySelectorAll('[data-mood]').forEach((chip) => chip.addEventListener('click', () => {
      aiForm.mood.value = chip.dataset.mood;
      aiForm.requestSubmit();
    }));
    aiForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const mood = aiForm.mood.value.trim();
      if (mood.length < 2) { toast('Опишите настроение подробнее', true); return; }
      const btn = aiForm.querySelector('button');
      btn.disabled = true;
      result.hidden = false;
      result.textContent = '';
      const spin = document.createElement('span');
      spin.className = 'loader';
      result.append(spin, 'ИИ подбирает фильмы...');
      try {
        const rec = await api('/api/recommendations/new/', 'POST', { mood: mood });
        result.textContent = rec.response_text;
        const empty = document.querySelector('[data-ai-empty]');
        if (empty) empty.remove();
        const card = document.createElement('div');
        card.className = 'card history';
        const meta = document.createElement('div');
        meta.className = 'muted';
        meta.textContent = 'только что · «' + rec.mood + '»';
        const pre = document.createElement('pre');
        pre.textContent = rec.response_text;
        card.append(meta, pre);
        history.prepend(card);
      } catch (err) {
        result.textContent = 'Не получилось: ' + err.message;
      } finally { btn.disabled = false; }
    });
  }
})();
