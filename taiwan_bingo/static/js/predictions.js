// Predictions page JS
let confChart = null;

async function trainModel() {
  const btn = document.getElementById('trainBtn');
  const modelType = document.getElementById('trainModelType').value;
  const pickCount = document.getElementById('trainPickCount').value;
  const resultEl = document.getElementById('trainResult');

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>訓練中...';
  resultEl.innerHTML = '';

  try {
    const res = await fetch('/api/v1/ml/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_type: modelType, pick_count: parseInt(pickCount) }),
    });
    const data = await res.json();
    if (res.ok) {
      resultEl.innerHTML = `<div class="alert alert-success py-2 small">${data.message}</div>`;
      loadModelsList();
    } else {
      resultEl.innerHTML = `<div class="alert alert-danger py-2 small">${data.detail || JSON.stringify(data)}</div>`;
    }
  } catch (e) {
    resultEl.innerHTML = `<div class="alert alert-danger py-2 small">${e.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-play-fill me-1"></i>開始訓練';
  }
}

async function loadModelsList() {
  const container = document.getElementById('modelsList');
  try {
    const res = await fetch('/api/v1/ml/models');
    const models = await res.json();
    if (!models.length) {
      container.innerHTML = '<div class="text-center text-muted py-3 small">尚無已訓練模型</div>';
      return;
    }
    container.innerHTML = models.map(m => `
      <div class="px-3 py-2 border-bottom small d-flex justify-content-between align-items-center">
        <div>
          <span class="fw-bold">${m.model_type}</span>
          <span class="badge ${m.is_active ? 'bg-success' : 'bg-secondary'} ms-1">${m.is_active ? '使用中' : '已停用'}</span>
        </div>
        <div class="text-muted">${new Date(m.trained_at).toLocaleDateString('zh-TW')}</div>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<div class="text-danger small p-3">${e.message}</div>`;
  }
}

function sectorClass(n) {
  if (n <= 20) return 'sector-1';
  if (n <= 40) return 'sector-2';
  if (n <= 60) return 'sector-3';
  return 'sector-4';
}

async function getPrediction() {
  const modelType = document.getElementById('predictModelType').value;
  const pickCount = document.getElementById('predictPickCount').value;
  const resultEl = document.getElementById('predictionResult');
  const cardEl = document.getElementById('confidenceCard');

  resultEl.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm me-2"></span>預測中...</div>';
  cardEl.style.display = 'none';

  try {
    const res = await fetch(`/api/v1/ml/predict?model_type=${modelType}&pick_count=${pickCount}`);
    if (!res.ok) {
      const err = await res.json();
      resultEl.innerHTML = `<div class="alert alert-warning">${err.detail || '預測失敗，請先訓練模型'}</div>`;
      return;
    }
    const data = await res.json();

    resultEl.innerHTML = `
      <div class="mb-3 d-flex flex-wrap gap-2">
        ${data.predicted_numbers.map(n => `<span class="num-ball ${sectorClass(n)}">${n}</span>`).join('')}
      </div>
      <div class="small text-muted">
        模型: <strong>${data.model_type}</strong> ｜
        預測號碼數: <strong>${data.pick_count}</strong> ｜
        隨機期望命中: <strong>${data.expected_random_hit}</strong>
      </div>
    `;

    // Confidence chart
    const details = data.confidence_details.sort((a, b) => a.number - b.number);
    renderConfidenceChart(details);
    cardEl.style.display = '';
  } catch (e) {
    resultEl.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

function renderConfidenceChart(details) {
  const ctx = document.getElementById('confidenceChart').getContext('2d');
  if (confChart) confChart.destroy();
  confChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: details.map(d => d.number),
      datasets: [{
        label: '信心分數',
        data: details.map(d => d.probability),
        backgroundColor: '#0d6efd88',
        borderColor: '#0d6efd',
        borderWidth: 1,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
    }
  });
}

async function runBacktest() {
  const body = {
    model_type: document.getElementById('btModelType').value,
    test_size: parseInt(document.getElementById('btTestSize').value),
    pick_count: parseInt(document.getElementById('btPickCount').value),
    win_threshold: parseInt(document.getElementById('btWinThreshold').value),
  };
  const el = document.getElementById('backtestResult');
  el.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm me-2"></span>回測中，請稍候...</div>';

  try {
    const res = await fetch('/api/v1/ml/backtest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      el.innerHTML = `<div class="alert alert-danger">${data.detail || '回測失敗'}</div>`;
      return;
    }

    el.innerHTML = `
      <div class="row g-3 mb-3">
        <div class="col-sm-3 text-center"><div class="bg-light rounded p-3"><div class="h4 text-primary">${(data.win_rate*100).toFixed(1)}%</div><small>勝率</small></div></div>
        <div class="col-sm-3 text-center"><div class="bg-light rounded p-3"><div class="h4 text-success">${data.avg_hits}</div><small>平均命中</small></div></div>
        <div class="col-sm-3 text-center"><div class="bg-light rounded p-3"><div class="h4 text-info">${data.test_size}</div><small>測試期數</small></div></div>
        <div class="col-sm-3 text-center"><div class="bg-light rounded p-3"><div class="h4 text-warning">${data.win_threshold}</div><small>中獎門檻</small></div></div>
      </div>
      <div class="table-responsive" style="max-height:300px;overflow-y:auto">
        <table class="table table-sm table-hover">
          <thead class="table-dark sticky-top"><tr><th>期次</th><th>命中</th><th>是否中獎</th></tr></thead>
          <tbody>
            ${data.results.map(r => `<tr class="${r.win?'table-success':''}">
              <td>${r.period}</td>
              <td>${r.hits}</td>
              <td>${r.win?'<span class="badge bg-success">中獎</span>':'<span class="badge bg-secondary">未中</span>'}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

// Init
loadModelsList();
