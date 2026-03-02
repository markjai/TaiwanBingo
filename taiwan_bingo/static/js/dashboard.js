// Dashboard page JS
let sectorChart = null;

async function loadDashboard() {
  try {
    const [latestRes, hotColdRes, modelsRes] = await Promise.all([
      fetch('/api/v1/draws/latest').catch(() => null),
      fetch('/api/v1/stats/hot-cold?window=100&top_n=1').catch(() => null),
      fetch('/api/v1/ml/models').catch(() => null),
    ]);

    if (latestRes && latestRes.ok) {
      const d = await latestRes.json();
      document.getElementById('latestTerm').textContent = `期別：${d.draw_term}`;
      document.getElementById('statSum').textContent = d.sum_total;
      document.getElementById('statOdd').textContent = d.odd_count;
      document.getElementById('statEven').textContent = d.even_count;
      document.getElementById('statSpan').textContent = d.span;

      const container = document.getElementById('latestNumbers');
      container.innerHTML = d.numbers.map(n => `<span class="num-ball ${sectorClass(n)}">${n}</span>`).join('');

      renderSectorChart(d);
    }

    if (hotColdRes && hotColdRes.ok) {
      const hc = await hotColdRes.json();
      document.getElementById('hotNum').textContent = hc.hot_numbers[0]?.number ?? '-';
      document.getElementById('coldNum').textContent = hc.cold_numbers[0]?.number ?? '-';
    }

    if (modelsRes && modelsRes.ok) {
      const models = await modelsRes.json();
      document.getElementById('mlStatus').textContent = `${models.length} 個`;
    }

    // Total draws
    const drRes = await fetch('/api/v1/draws?page=1&page_size=1');
    if (drRes.ok) {
      const dr = await drRes.json();
      document.getElementById('totalDraws').textContent = dr.total.toLocaleString();
    }
  } catch (e) {
    console.error('Dashboard load error:', e);
  }
}

function sectorClass(n) {
  if (n <= 20) return 'sector-1';
  if (n <= 40) return 'sector-2';
  if (n <= 60) return 'sector-3';
  return 'sector-4';
}

function renderSectorChart(d) {
  const ctx = document.getElementById('sectorChart').getContext('2d');
  if (sectorChart) sectorChart.destroy();
  sectorChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['1-20', '21-40', '41-60', '61-80'],
      datasets: [{
        data: [d.sector_1_count, d.sector_2_count, d.sector_3_count, d.sector_4_count],
        backgroundColor: ['#0d6efd', '#198754', '#dc3545', '#6f42c1'],
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } }
    }
  });
}

async function triggerScrape() {
  const res = await fetch('/api/v1/scraper/run', { method: 'POST' });
  const data = await res.json();
  const body = res.ok
    ? `狀態: ${data.status}，新增 ${data.records_inserted} 筆`
    : `錯誤: ${data.detail || JSON.stringify(data)}`;
  document.getElementById('scrapeToastBody').textContent = body;
  bootstrap.Toast.getOrCreateInstance(document.getElementById('scrapeToast')).show();
  if (res.ok) setTimeout(loadDashboard, 1500);
}

loadDashboard();
