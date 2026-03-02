// Analysis page JS
let charts = {};

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

function sectorColor(i) {
  return ['#0d6efd','#198754','#dc3545','#6f42c1'][i] || '#6c757d';
}

async function loadAllStats() {
  const w = document.getElementById('window').value;
  await Promise.all([
    loadFrequency(w),
    loadHotCold(w),
    loadSectors(w),
    loadBias(w),
    loadGaps(w),
  ]);
}

async function loadFrequency(w) {
  const res = await fetch(`/api/v1/stats/frequency?window=${w}`);
  if (!res.ok) return;
  const data = await res.json();
  const sorted = [...data].sort((a,b) => a.number - b.number);

  destroyChart('freqChart');
  const ctx = document.getElementById('freqChart').getContext('2d');
  charts['freqChart'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(d => d.number),
      datasets: [{
        label: '出現次數',
        data: sorted.map(d => d.count),
        backgroundColor: sorted.map(d => {
          if (d.number <= 20) return '#0d6efd88';
          if (d.number <= 40) return '#19875488';
          if (d.number <= 60) return '#dc354588';
          return '#6f42c188';
        }),
        borderColor: sorted.map(d => {
          if (d.number <= 20) return '#0d6efd';
          if (d.number <= 40) return '#198754';
          if (d.number <= 60) return '#dc3545';
          return '#6f42c1';
        }),
        borderWidth: 1,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { maxRotation: 0, font: { size: 9 } } } }
    }
  });
}

async function loadHotCold(w) {
  const res = await fetch(`/api/v1/stats/hot-cold?window=${w}&top_n=10`);
  if (!res.ok) return;
  const { hot_numbers, cold_numbers } = await res.json();

  document.getElementById('hotNumbers').innerHTML = hot_numbers.map(h =>
    `<span class="num-ball hot" title="${h.count}次">${h.number}</span>`
  ).join('');
  document.getElementById('coldNumbers').innerHTML = cold_numbers.map(c =>
    `<span class="num-ball cold" title="${c.count}次">${c.number}</span>`
  ).join('');
}

async function loadSectors(w) {
  const res = await fetch(`/api/v1/stats/sectors?window=${w}`);
  if (!res.ok) return;
  const { sectors } = await res.json();

  destroyChart('sectorBarChart');
  const ctx = document.getElementById('sectorBarChart').getContext('2d');
  charts['sectorBarChart'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sectors.map(s => `${s.range_start}-${s.range_end}`),
      datasets: [{
        label: '平均個數',
        data: sectors.map(s => s.avg_count),
        backgroundColor: sectors.map((_, i) => sectorColor(i) + '99'),
        borderColor: sectors.map((_, i) => sectorColor(i)),
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, suggestedMax: 8 } }
    }
  });
}

async function loadBias(w) {
  const res = await fetch(`/api/v1/stats/bias?window=${w}`);
  if (!res.ok) return;
  const b = await res.json();
  const el = document.getElementById('biasReport');
  const badge = b.is_biased ? '<span class="badge bg-danger ms-2">有偏差</span>' : '<span class="badge bg-success ms-2">無顯著偏差</span>';
  el.innerHTML = `
    <dl class="row mb-0">
      <dt class="col-5">卡方統計值</dt><dd class="col-7">${b.chi_square}</dd>
      <dt class="col-5">p 值</dt><dd class="col-7">${b.p_value} ${badge}</dd>
      <dt class="col-5">期望頻率</dt><dd class="col-7">${b.expected_frequency}</dd>
      <dt class="col-5">偏差號碼</dt>
      <dd class="col-7">${b.biased_numbers.length ? b.biased_numbers.join(', ') : '無'}</dd>
    </dl>
  `;
}

async function loadGaps(w) {
  const res = await fetch(`/api/v1/stats/gaps?window=${w}`);
  if (!res.ok) return;
  const { gaps } = await res.json();
  const top20 = [...gaps].sort((a,b) => b.current_gap - a.current_gap).slice(0, 20);

  destroyChart('gapChart');
  const ctx = document.getElementById('gapChart').getContext('2d');
  charts['gapChart'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top20.map(g => g.number),
      datasets: [{
        label: '當前遺漏',
        data: top20.map(g => g.current_gap),
        backgroundColor: '#6c757d88',
        borderColor: '#6c757d',
        borderWidth: 1,
      }, {
        label: '平均遺漏',
        data: top20.map(g => g.avg_gap),
        type: 'line',
        borderColor: '#fd7e14',
        fill: false,
        tension: 0.3,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
    }
  });
}

loadAllStats();
