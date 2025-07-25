// static/js/main.js
;(function () {
  // ─── API endpoints ──────────────────────────────────────────
  const API = {
    login:        '/api/login',
    register:     '/api/register',
    semifinals:   n => `/api/semi-finals/${n}`,
    final:        '/api/grand-final',    // для загрузки списка гран-финалистов
    vote:         '/api/vote',           // для полуфиналов
    grandVote:    '/api/grand-vote',     // новый эндпоинт для гран-финала
    results:      '/api/results',        // результаты полу/финалов
    resultsFinal: '/api/results-final',  // результаты гран-финала
    adminToggle:  id => `/api/admin/final/${id}`,
    adminOrder:   id => `/api/admin/final/order/${id}`,
  };

  const TOKEN_KEY   = 'jwt';
  const getToken    = () => localStorage.getItem(TOKEN_KEY);
  const saveToken   = t  => localStorage.setItem(TOKEN_KEY, t);
  const clearToken  = () => localStorage.removeItem(TOKEN_KEY);
  const authHeaders = () => ({
    'Content-Type': 'application/json',
    Authorization:  `Bearer ${getToken()}`,
  });

  // ─── DOM ready ──────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    // Logout
    document.querySelector('#logout-link')?.addEventListener('click', e => {
      e.preventDefault();
      clearToken();
      window.location.href = '/';
    });
    // Back
    document.querySelector('#back-button')?.addEventListener('click', e => {
      e.preventDefault();
      window.history.back();
    });

    // Login
    document.querySelector('#login-form')?.addEventListener('submit', async e => {
      e.preventDefault();
      const body = {
        login:    e.target.login.value.trim(),
        password: e.target.password.value,
      };
      const r = await fetch(API.login, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
      });
      if (r.ok) {
        saveToken((await r.json()).access_token);
        window.location.href = '/dashboard';
      } else {
        document.querySelector('#login-msg').textContent =
          'Неверный логин/пароль';
      }
    });

    // Register
    document.querySelector('#register-form')?.addEventListener('submit', async e => {
      e.preventDefault();
      const body = {
        login:    e.target.login.value.trim(),
        password: e.target.password.value,
      };
      const r = await fetch(API.register, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
      });
      if (r.status === 201) {
        alert('Регистрация успешна! Теперь войдите.');
        window.location.href = '/';
      } else if (r.status === 409) {
        document.querySelector('#reg-msg').textContent =
          'Пользователь уже существует';
      } else {
        document.querySelector('#reg-msg').textContent = 'Ошибка регистрации';
      }
    });

    // Dashboard menu
    document.querySelector('#main-menu')?.addEventListener('click', e => {
      const btn = e.target.closest('button[data-target]');
      if (!btn) return;
      switch (btn.dataset.target) {
        case 'semi1':         window.location.href = '/semi-final/1'; break;
        case 'semi2':         window.location.href = '/semi-final/2'; break;
        case 'final':         window.location.href = '/final-page'; break;
        case 'results':       window.location.href = '/results-page'; break;
        case 'results-final': window.location.href = '/grand-results-page'; break;
      }
    });

    // Load artists on semi/final pages
    const tbl = document.querySelector('#artists-table');
    if (tbl) loadArtists(tbl);

    // Load results (полуфиналы и основной финал)
    const resBody = document.querySelector('#results-body');
    if (resBody) {
      fetch(API.results, { headers: authHeaders() })
        .then(r => r.json())
        .then(rows => {
          resBody.innerHTML = '';
          rows.forEach(rw => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${rw.name}</td>
              <td>${rw.avg ?? '—'}</td>
              <td>${rw.final_votes}</td>
              <td>${rw.voters.join(', ')}</td>
            `;
            resBody.appendChild(tr);
          });
        });
    }

    // Load results (гран-финал)
    const resFinalBody = document.querySelector('#results-final-body');
    if (resFinalBody) {
      fetch(API.resultsFinal, { headers: authHeaders() })
        .then(r => r.json())
        .then(rows => {
          resFinalBody.innerHTML = '';
          rows.forEach(rw => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${rw.name}</td>
              <td>${rw.avg ?? '—'}</td>
              <td>${rw.final_votes}</td>
              <td>${rw.voters.join(', ')}</td>
            `;
            resFinalBody.appendChild(tr);
          });
        });
    }
  });


  // ─── Загрузка артистов ──────────────────────────────────────
  async function loadArtists(table) {
    const semi        = Number(table.dataset.semi);       // 0 → гран-финал
    const url         = semi ? API.semifinals(semi) : API.final;
    const isGrand     = semi === 0;

    const resp = await fetch(url, { headers: authHeaders() });
    if (!resp.ok) return;
    const { admin, artists } = await resp.json();

    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';

    // отрисуем всех
    artists.forEach((a, i) => {
      const options = Array.from({ length: 13 }, (_, n) =>
        `<option${a.score === n ? ' selected' : ''}>${n}</option>`
      ).join('');

      const tr = document.createElement('tr');
      tr.className = 'artist-row';
      tr.innerHTML = `
        <td class="ord">${isGrand ? i + 1 : a.order}</td>
        <td class="name">${a.name}</td>
        <td>
          <select data-id="${a.id}" class="score-select">
            <option value="">–</option>${options}
          </select>
        </td>
        <td>
          <button class="vote-btn${a.final ? ' active' : ''}" data-id="${a.id}">
            ${isGrand
              ? (a.final ? 'WINNER' : 'Select winner')
              : (a.final ? 'FINAL'  : 'Pass to final')}
          </button>
        </td>
        ${ admin
          ? `<td>
               <button class="toggle-official${a.official ? ' active' : ''}" data-id="${a.id}">
                 ${a.official ? 'Remove' : 'Add'}
               </button>
             </td>`
          : '<td></td>'
        }
        ${ admin && isGrand && a.official
          ? `<td>
               <button class="move" data-id="${a.id}" data-dir="up">▲</button>
               <button class="move" data-id="${a.id}" data-dir="down">▼</button>
             </td>`
          : '<td></td>'
        }
      `;
      tbody.appendChild(tr);
    });

    // слушаем изменения рейтинга
    tbody.addEventListener('change', async e => {
      if (!e.target.matches('.score-select')) return;
      const id = e.target.dataset.id;
      const val = e.target.value === '' ? null : +e.target.value;
      await fetch(isGrand ? API.grandVote : API.vote, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ artist_id: id, score: val })
      });
    });

    // слушаем клики на кнопки
    tbody.addEventListener('click', async e => {
      // 1) выбор в финал / победителя
      if (e.target.matches('.vote-btn')) {
        const btn   = e.target;
        const id    = btn.dataset.id;
        const makeOn= !btn.classList.contains('active');

        // для гран-финала — только один WINNER
        if (isGrand && makeOn) {
          tbody.querySelectorAll('.vote-btn.active').forEach(b => {
            b.classList.remove('active');
            b.textContent = 'Select winner';
            fetch(API.grandVote, {
              method: 'POST',
              headers: authHeaders(),
              body: JSON.stringify({ artist_id: b.dataset.id, final: false })
            });
          });
        }

        // переключаем текущую
        btn.classList.toggle('active');
        btn.textContent = isGrand
          ? (btn.classList.contains('active') ? 'WINNER' : 'Select winner')
          : (btn.classList.contains('active') ? 'FINAL' : 'Pass to final');

        // сохраняем
        await fetch(isGrand ? API.grandVote : API.vote, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({
            artist_id: id,
            final:     btn.classList.contains('active')
          })
        });

        enforceLimit(tbody, isGrand ? 1 : 10);
      }

      // 2) админ-переключатель
      else if (e.target.matches('.toggle-official')) {
        const id = e.target.dataset.id;
        await fetch(API.adminToggle(id), {
          method: 'POST',
          headers: authHeaders(),
        });
        await loadArtists(table);
      }

      // 3) порядок (admin)
      else if (e.target.matches('.move')) {
        const id  = e.target.dataset.id;
        const dir = e.target.dataset.dir;
        await fetch(API.adminOrder(id), {
          method: 'PUT',
          headers: authHeaders(),
          body: JSON.stringify({ direction: dir }),
        });
        await loadArtists(table);
      }
    });

    // применяем лимит сразу
    enforceLimit(tbody, isGrand ? 1 : 10);
  }

  // ─── Ограничение количества активных кнопок ────────────────
  function enforceLimit(tbody, limit = 10) {
    const activeCount = tbody.querySelectorAll('.vote-btn.active').length;
    tbody.querySelectorAll('.vote-btn').forEach(b => {
      b.disabled = !b.classList.contains('active') && activeCount >= limit;
    });
  }
})();
