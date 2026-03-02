// History page JS
let currentPage = 1;

function sectorClass(n) {
  if (n <= 20) return 'sector-1';
  if (n <= 40) return 'sector-2';
  if (n <= 60) return 'sector-3';
  return 'sector-4';
}

async function loadHistory(page = 1) {
  currentPage = page;
  const pageSize = document.getElementById('pageSize').value;
  const dateFrom = document.getElementById('dateFrom').value;
  const dateTo = document.getElementById('dateTo').value;

  let url = `/api/v1/draws?page=${page}&page_size=${pageSize}`;
  if (dateFrom) url += `&date_from=${dateFrom}`;
  if (dateTo) url += `&date_to=${dateTo}`;

  const tbody = document.getElementById('historyBody');
  tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4"><div class="spinner-border spinner-border-sm me-2"></div>載入中...</td></tr>';

  try {
    const res = await fetch(url);
    const data = await res.json();

    document.getElementById('resultCount').textContent = `共 ${data.total.toLocaleString()} 筆`;

    tbody.innerHTML = data.items.map(d => `
      <tr>
        <td class="text-monospace small">${d.draw_term}</td>
        <td class="small">${new Date(d.draw_datetime).toLocaleString('zh-TW')}</td>
        <td><div class="d-flex flex-wrap gap-1">${d.numbers.map(n => `<span class="num-ball ${sectorClass(n)}" style="width:28px;height:28px;font-size:.75rem">${n}</span>`).join('')}</div></td>
        <td>${d.sum_total}</td>
        <td>${d.odd_count}/${d.even_count}</td>
        <td>${d.sector_1_count}</td>
        <td>${d.sector_2_count}</td>
        <td>${d.sector_3_count}</td>
        <td>${d.sector_4_count}</td>
      </tr>
    `).join('');

    renderPagination(data.page, data.total_pages);
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger py-4">載入失敗: ${e.message}</td></tr>`;
  }
}

function renderPagination(current, total) {
  const container = document.getElementById('pagination');
  if (total <= 1) { container.innerHTML = ''; return; }

  let html = '';
  const prev = current > 1;
  const next = current < total;
  html += `<button class="btn btn-sm btn-outline-secondary" onclick="loadHistory(${current-1})" ${prev?'':'disabled'}>&laquo;</button>`;
  const start = Math.max(1, current - 2);
  const end = Math.min(total, current + 2);
  for (let p = start; p <= end; p++) {
    html += `<button class="btn btn-sm ${p===current?'btn-primary':'btn-outline-secondary'}" onclick="loadHistory(${p})">${p}</button>`;
  }
  html += `<button class="btn btn-sm btn-outline-secondary" onclick="loadHistory(${current+1})" ${next?'':'disabled'}>&raquo;</button>`;
  container.innerHTML = html;
}

loadHistory(1);
