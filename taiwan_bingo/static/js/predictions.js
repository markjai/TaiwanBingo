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

// ─── Pick-N Analysis ─────────────────────────────────────────────────────────

let currentPickN = 3;

function setPickN(n) {
  currentPickN = n;
  [3, 4, 5].forEach(i => {
    const btn = document.getElementById(`pickTab${i}`);
    if (btn) btn.classList.toggle('active', i === n);
  });
  const predN = document.getElementById('dqnPredictN');
  if (predN) predN.textContent = n;
  document.getElementById('pickNResult').innerHTML =
    '<div class="text-center text-muted py-4 small">選擇分析類型以載入結果</div>';
}

async function trainDQN(pickCount) {
  const btn = document.getElementById(`dqnTrain${pickCount}Btn`);
  const resultEl = document.getElementById('dqnTrainResult');
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>訓練中...`;
  resultEl.innerHTML = '';
  try {
    const res = await fetch('/api/v1/ml/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_type: `dqn_${pickCount}`, pick_count: pickCount }),
    });
    const data = await res.json();
    if (res.ok) {
      resultEl.innerHTML = `<div class="alert alert-success py-1">${data.message}</div>`;
      loadModelsList();
    } else {
      resultEl.innerHTML = `<div class="alert alert-danger py-1">${data.detail || JSON.stringify(data)}</div>`;
    }
  } catch (e) {
    resultEl.innerHTML = `<div class="alert alert-danger py-1">${e.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="bi bi-play-fill me-1"></i>訓練 Pick-${pickCount} DQN`;
  }
}

async function getDQNPrediction() {
  const btn = document.getElementById('dqnPredictBtn');
  const resultEl = document.getElementById('dqnPredictResult');
  btn.disabled = true;
  resultEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>預測中...';
  try {
    const res = await fetch(`/api/v1/ml/dqn-predict?pick_count=${currentPickN}`);
    if (!res.ok) {
      const err = await res.json();
      resultEl.innerHTML = `<div class="alert alert-warning py-1">${err.detail || '請先訓練 DQN 模型'}</div>`;
      return;
    }
    const data = await res.json();
    resultEl.innerHTML = `
      <div class="d-flex flex-wrap gap-1 my-1">
        ${data.recommended_numbers.map((n, i) =>
          `<span class="num-ball ${sectorClass(n)}" title="Q=${data.q_values[i]?.toFixed(4)}">${n}</span>`
        ).join('')}
      </div>
      <div class="text-muted" style="font-size:0.75rem">理論全中率: ${(data.full_hit_probability_estimate * 100).toFixed(4)}%</div>
    `;
  } catch (e) {
    resultEl.innerHTML = `<div class="text-danger">${e.message}</div>`;
  } finally {
    btn.disabled = false;
  }
}

async function loadPickNHitAnalysis() {
  const el = document.getElementById('pickNResult');
  el.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm"></span> 載入中...</div>';
  try {
    const res = await fetch(`/api/v1/pick/${currentPickN}/hit-analysis?window=1000`);
    const data = await res.json();
    if (!res.ok) { el.innerHTML = `<div class="alert alert-danger">${data.detail}</div>`; return; }

    const distKeys = Object.keys(data.hit_distribution).sort((a, b) => +a - +b);
    const distVals = distKeys.map(k => data.hit_distribution[k]);
    const total = distVals.reduce((a, b) => a + b, 0);

    el.innerHTML = `
      <h6 class="fw-bold">Pick-${data.pick_count} 命中率分析（近 ${data.window} 期）</h6>
      <div class="row g-2 mb-3">
        <div class="col-sm-4 text-center">
          <div class="bg-light rounded p-2">
            <div class="h5 text-danger">${(data.theoretical_full_hit_rate*100).toFixed(4)}%</div>
            <small>理論全中率</small>
          </div>
        </div>
        <div class="col-sm-4 text-center">
          <div class="bg-light rounded p-2">
            <div class="h5 text-success">${(data.full_hit_rate*100).toFixed(4)}%</div>
            <small>熱門策略全中率</small>
          </div>
        </div>
        <div class="col-sm-4 text-center">
          <div class="bg-light rounded p-2">
            <div class="h5 text-primary">${data.full_hit_count}</div>
            <small>全中次數</small>
          </div>
        </div>
      </div>
      <div class="mb-2 small">使用熱門號碼: ${data.hot_numbers_used.map(n => `<span class="badge bg-warning text-dark">${n}</span>`).join(' ')}</div>
      <div class="table-responsive">
        <table class="table table-sm">
          <thead class="table-dark"><tr><th>命中數</th><th>次數</th><th>佔比</th></tr></thead>
          <tbody>
            ${distKeys.map(k => `<tr class="${k==data.pick_count?'table-success':''}">
              <td>${k} / ${data.pick_count}</td>
              <td>${data.hit_distribution[k]}</td>
              <td>${total ? (data.hit_distribution[k]/total*100).toFixed(2) : 0}%</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

async function loadPickNHotCombos() {
  const el = document.getElementById('pickNResult');
  el.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm"></span> 載入中...</div>';
  try {
    const res = await fetch(`/api/v1/pick/${currentPickN}/hot-combinations?window=500&top_n=20`);
    const data = await res.json();
    if (!res.ok) { el.innerHTML = `<div class="alert alert-danger">${data.detail}</div>`; return; }

    el.innerHTML = `
      <h6 class="fw-bold">Pick-${currentPickN} 熱門組合 Top-20</h6>
      <div class="table-responsive" style="max-height:320px;overflow-y:auto">
        <table class="table table-sm table-hover">
          <thead class="table-dark sticky-top"><tr><th>#</th><th>號碼組合</th><th>出現次數</th><th>頻率</th></tr></thead>
          <tbody>
            ${data.map((c, i) => `<tr>
              <td>${i+1}</td>
              <td>${c.numbers.map(n => `<span class="badge bg-secondary me-1">${n}</span>`).join('')}</td>
              <td>${c.count}</td>
              <td>${c.percentage}%</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

async function loadPickNRecommend() {
  const el = document.getElementById('pickNResult');
  el.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm"></span> 載入中...</div>';
  try {
    const res = await fetch(`/api/v1/pick/${currentPickN}/recommend?window=200`);
    const data = await res.json();
    if (!res.ok) { el.innerHTML = `<div class="alert alert-danger">${data.detail}</div>`; return; }

    el.innerHTML = `
      <h6 class="fw-bold">Pick-${data.pick_count} AI 推薦號碼</h6>
      <div class="d-flex flex-wrap gap-2 mb-3">
        ${data.recommended_numbers.map((n, i) =>
          `<div class="text-center">
            <span class="num-ball ${sectorClass(n)}">${n}</span>
            <div style="font-size:0.7rem;color:#666">${data.scores[i]?.toFixed(4)}</div>
          </div>`
        ).join('')}
      </div>
      <div class="alert alert-info py-2 small"><i class="bi bi-info-circle me-1"></i>${data.rationale}</div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

async function loadPickNEV() {
  const el = document.getElementById('pickNResult');
  el.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm"></span> 載入中...</div>';
  try {
    const res = await fetch(`/api/v1/pick/${currentPickN}/expected-value?window=1000`);
    const data = await res.json();
    if (!res.ok) { el.innerHTML = `<div class="alert alert-danger">${data.detail}</div>`; return; }

    el.innerHTML = `
      <h6 class="fw-bold">Pick-${data.pick_count} 期望值分析</h6>
      <div class="row g-3">
        <div class="col-sm-4 text-center">
          <div class="bg-light rounded p-3">
            <div class="h5 text-danger">${(data.theoretical_rate*100).toFixed(6)}%</div>
            <small>理論全中率</small>
          </div>
        </div>
        <div class="col-sm-4 text-center">
          <div class="bg-light rounded p-3">
            <div class="h5 text-success">${(data.observed_rate*100).toFixed(6)}%</div>
            <small>熱門策略全中率</small>
          </div>
        </div>
        <div class="col-sm-4 text-center">
          <div class="bg-light rounded p-3">
            <div class="h5 ${data.improvement_ratio >= 1 ? 'text-success' : 'text-warning'}">${data.improvement_ratio.toFixed(2)}x</div>
            <small>相對提升倍率</small>
          </div>
        </div>
      </div>
      <div class="mt-3 alert ${data.improvement_ratio >= 1 ? 'alert-success' : 'alert-warning'} py-2 small">
        ${data.improvement_ratio >= 1
          ? `熱門號碼策略比隨機選擇高出 <strong>${data.improvement_ratio.toFixed(2)}x</strong>`
          : `熱門號碼策略表現低於理論值（${data.improvement_ratio.toFixed(2)}x）`}
      </div>
    `;
  } catch (e) {
    el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}
