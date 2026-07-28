/* ==========================================================================
   AXIOM QUANT — MARKOWITZ OPTIMIZER ENGINE (SPECTRAL EQUILIBRIUM)
   ========================================================================== */

// PRESET UNIVERSES DATA
const UNIVERSES = {
  bigtech : {
    name : "Big Tech",
    assets : [
      {ticker : "AAPL", ret : 0.165, vol : 0.22},
      {ticker : "MSFT", ret : 0.180, vol : 0.20},
      {ticker : "GOOGL", ret : 0.150, vol : 0.24},
      {ticker : "AMZN", ret : 0.172, vol : 0.26},
      {ticker : "TSLA", ret : 0.240, vol : 0.45}
    ],
    correlations : [
      [ 1.00, 0.65, 0.58, 0.62, 0.42 ],
      [ 0.65, 1.00, 0.62, 0.60, 0.38 ],
      [ 0.58, 0.62, 1.00, 0.64, 0.40 ],
      [ 0.62, 0.60, 0.64, 1.00, 0.45 ],
      [ 0.42, 0.38, 0.40, 0.45, 1.00 ]
    ]
  },
  finance : {
    name : "Finance",
    assets : [
      {ticker : "JPM", ret : 0.135, vol : 0.19},
      {ticker : "BAC", ret : 0.120, vol : 0.23},
      {ticker : "GS", ret : 0.148, vol : 0.24},
      {ticker : "MS", ret : 0.142, vol : 0.25},
      {ticker : "C", ret : 0.110, vol : 0.26}
    ],
    correlations : [
      [ 1.00, 0.78, 0.72, 0.70, 0.75 ],
      [ 0.78, 1.00, 0.68, 0.66, 0.82 ],
      [ 0.72, 0.68, 1.00, 0.85, 0.70 ],
      [ 0.70, 0.66, 0.85, 1.00, 0.68 ],
      [ 0.75, 0.82, 0.70, 0.68, 1.00 ]
    ]
  },
  energy : {
    name : "Energy",
    assets : [
      {ticker : "XOM", ret : 0.125, vol : 0.21},
      {ticker : "CVX", ret : 0.118, vol : 0.20},
      {ticker : "COP", ret : 0.140, vol : 0.27},
      {ticker : "SLB", ret : 0.155, vol : 0.32},
      {ticker : "EOG", ret : 0.132, vol : 0.28}
    ],
    correlations : [
      [ 1.00, 0.82, 0.75, 0.68, 0.72 ],
      [ 0.82, 1.00, 0.74, 0.65, 0.70 ],
      [ 0.75, 0.74, 1.00, 0.78, 0.80 ],
      [ 0.68, 0.65, 0.78, 1.00, 0.75 ],
      [ 0.72, 0.70, 0.80, 0.75, 1.00 ]
    ]
  },
  crypto : {
    name : "Crypto",
    assets : [
      {ticker : "BTC", ret : 0.350, vol : 0.55},
      {ticker : "ETH", ret : 0.420, vol : 0.68},
      {ticker : "SOL", ret : 0.580, vol : 0.92},
      {ticker : "BNB", ret : 0.300, vol : 0.50},
      {ticker : "AVAX", ret : 0.480, vol : 0.85}
    ],
    correlations : [
      [ 1.00, 0.75, 0.62, 0.65, 0.58 ],
      [ 0.75, 1.00, 0.72, 0.68, 0.66 ],
      [ 0.62, 0.72, 1.00, 0.55, 0.74 ],
      [ 0.65, 0.68, 0.55, 1.00, 0.58 ],
      [ 0.58, 0.66, 0.74, 0.58, 1.00 ]
    ]
  },
  etfs : {
    name : "ETFs",
    assets : [
      {ticker : "SPY", ret : 0.105, vol : 0.15},
      {ticker : "QQQ", ret : 0.150, vol : 0.19},
      {ticker : "IWM", ret : 0.098, vol : 0.21},
      {ticker : "TLT", ret : 0.042, vol : 0.13},
      {ticker : "GLD", ret : 0.075, vol : 0.14}
    ],
    correlations : [
      [ 1.00, 0.88, 0.82, -0.32, 0.12 ],
      [ 0.88, 1.00, 0.78, -0.38, 0.08 ],
      [ 0.82, 0.78, 1.00, -0.28, 0.15 ],
      [ -0.32, -0.38, -0.28, 1.00, 0.25 ],
      [ 0.12, 0.08, 0.15, 0.25, 1.00 ]
    ]
  }
};

let currentUniverseKey = 'bigtech';
let currentUniverse = UNIVERSES.bigtech;
let sampledPortfolios = [];
let minVarPortfolio = null;
let maxSharpePortfolio = null;
let canvas, ctx;

document.addEventListener('DOMContentLoaded', () => {
  initBackgroundCanvas();
  initPresetButtons();
  initFrontierCanvas();
  runOptimization();
});

// BACKGROUND CANVAS
function initBackgroundCanvas() {
  const bgCanvas = document.getElementById('backgroundGridCanvas');
  if (!bgCanvas)
    return;
  const bgCtx = bgCanvas.getContext('2d');

  function resize() {
    bgCanvas.width = window.innerWidth;
    bgCanvas.height = window.innerHeight;
    drawGrid();
  }

  function drawGrid() {
    bgCtx.fillStyle = '#06070B';
    bgCtx.fillRect(0, 0, bgCanvas.width, bgCanvas.height);
    bgCtx.strokeStyle = 'rgba(30, 41, 59, 0.15)';
    bgCtx.lineWidth = 0.5;

    for (let x = 0; x < bgCanvas.width; x += 50) {
      bgCtx.beginPath();
      bgCtx.moveTo(x, 0);
      bgCtx.lineTo(x, bgCanvas.height);
      bgCtx.stroke();
    }
    for (let y = 0; y < bgCanvas.height; y += 50) {
      bgCtx.beginPath();
      bgCtx.moveTo(0, y);
      bgCtx.lineTo(bgCanvas.width, y);
      bgCtx.stroke();
    }
  }

  window.addEventListener('resize', resize);
  resize();
}

// PRESET BUTTONS
function initPresetButtons() {
  const buttons = document.querySelectorAll('.preset-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentUniverseKey = btn.getAttribute('data-universe');
      currentUniverse = UNIVERSES[currentUniverseKey];
      runOptimization();
    });
  });
}

// FRONTIER CANVAS INIT
function initFrontierCanvas() {
  canvas = document.getElementById('frontierCanvas');
  if (!canvas)
    return;
  ctx = canvas.getContext('2d');

  window.addEventListener('resize', resizeFrontierCanvas);
  resizeFrontierCanvas();

  // Hover Tooltip
  canvas.addEventListener('mousemove', handleCanvasHover);
  canvas.addEventListener('mouseleave', () => {
    const tooltip = document.getElementById('chartTooltip');
    if (tooltip)
      tooltip.style.display = 'none';
  });
}

function resizeFrontierCanvas() {
  if (!canvas)
    return;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  renderFrontierChart();
}

// MATHEMATICAL OPTIMIZATION ENGINE
function runOptimization() {
  const rfRate =
      (parseFloat(document.getElementById('rfRate')?.value) || 4.5) / 100.0;
  const numSamples =
      parseInt(document.getElementById('simPortfolios')?.value) || 3000;
  const assets = currentUniverse.assets;
  const n = assets.length;

  // Calculate covariance matrix: Cov(i,j) = corr(i,j) * vol(i) * vol(j)
  const cov = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      cov[i][j] =
          currentUniverse.correlations[i][j] * assets[i].vol * assets[j].vol;
    }
  }

  // Monte Carlo Weight Sampling
  sampledPortfolios = [];
  minVarPortfolio = null;
  maxSharpePortfolio = null;

  let minVar = Infinity;
  let maxSharpe = -Infinity;

  for (let s = 0; s < numSamples; s++) {
    // Uniform / Dirichlet normalized weights
    const rawW = Array(n).fill(0).map(() => Math.random());
    const sumW = rawW.reduce((a, b) => a + b, 0);
    const w = rawW.map(v => v / sumW);

    // Portfolio Return: E(Rp) = sum(w_i * mu_i)
    let ret = 0;
    for (let i = 0; i < n; i++)
      ret += w[i] * assets[i].ret;

    // Portfolio Variance: Var(Rp) = w' * Cov * w
    let varP = 0;
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        varP += w[i] * w[j] * cov[i][j];
      }
    }
    const volP = Math.sqrt(varP);
    const sharpe = (ret - rfRate) / volP;

    const portObj = {weights : w, ret, vol : volP, sharpe};
    sampledPortfolios.push(portObj);

    if (volP < minVar) {
      minVar = volP;
      minVarPortfolio = portObj;
    }

    if (sharpe > maxSharpe) {
      maxSharpe = sharpe;
      maxSharpePortfolio = portObj;
    }
  }

  // Update UI Elements
  updateAssetSummaryTable(rfRate);
  updateWeightsTable();
  const maxSharpeEl = document.getElementById('maxSharpeVal');
  if (maxSharpeEl && maxSharpePortfolio) {
    maxSharpeEl.innerText =
        `MAX SHARPE: ${maxSharpePortfolio.sharpe.toFixed(3)} | MIN VOL: ${
            (minVarPortfolio.vol * 100).toFixed(2)}%`;
  }

  renderFrontierChart();
}

// RENDER EFFICIENT FRONTIER CANVAS
function renderFrontierChart() {
  if (!ctx || !canvas)
    return;
  const w = canvas.width;
  const h = canvas.height;
  const padding = 50;

  ctx.fillStyle = '#020305';
  ctx.fillRect(0, 0, w, h);

  if (sampledPortfolios.length === 0)
    return;

  // Determine Axis Bounds
  const assets = currentUniverse.assets;
  let maxVol =
      Math.max(
          ...sampledPortfolios.map(p => p.vol), ...assets.map(a => a.vol)) *
      1.15;
  let minVol = 0;
  let maxRet =
      Math.max(
          ...sampledPortfolios.map(p => p.ret), ...assets.map(a => a.ret)) *
      1.15;
  let minRet =
      Math.min(
          ...sampledPortfolios.map(p => p.ret), ...assets.map(a => a.ret), 0) *
      0.9;

  function toScreenX(vol) {
    return padding + ((vol - minVol) / (maxVol - minVol)) * (w - padding * 2);
  }
  function toScreenY(ret) {
    return h - padding -
        ((ret - minRet) / (maxRet - minRet)) * (h - padding * 2);
  }

  // Grid lines & Axis
  ctx.strokeStyle = 'rgba(30, 41, 59, 0.3)';
  ctx.lineWidth = 0.5;
  ctx.fillStyle = '#475569';
  ctx.font = '10px "Fira Code", monospace';

  for (let v = 0; v <= maxVol; v += 0.05) {
    const sx = toScreenX(v);
    ctx.beginPath();
    ctx.moveTo(sx, padding);
    ctx.lineTo(sx, h - padding);
    ctx.stroke();
    ctx.fillText(`${(v * 100).toFixed(0)}%`, sx - 10, h - padding + 18);
  }

  for (let r = 0; r <= maxRet; r += 0.05) {
    const sy = toScreenY(r);
    ctx.beginPath();
    ctx.moveTo(padding, sy);
    ctx.lineTo(w - padding, sy);
    ctx.stroke();
    ctx.fillText(`${(r * 100).toFixed(0)}%`, padding - 35, sy + 3);
  }

  // Axis Labels
  ctx.fillStyle = '#94A3B8';
  ctx.fillText('PORTFOLIO VOLATILITY (RISK σ)', w / 2 - 60, h - 15);

  // 1. Draw Monte Carlo Scatter Cloud
  sampledPortfolios.forEach(p => {
    const x = toScreenX(p.vol);
    const y = toScreenY(p.ret);

    // Color based on Sharpe Ratio
    ctx.fillStyle = p.sharpe > (maxSharpePortfolio.sharpe * 0.8)
        ? 'rgba(0, 240, 255, 0.4)'
        : 'rgba(148, 163, 184, 0.15)';
    ctx.beginPath();
    ctx.arc(x, y, 1.8, 0, Math.PI * 2);
    ctx.fill();
  });

  // 2. Draw Capital Allocation Line (CAL) from Rf through Tangency Point
  const rfRate =
      (parseFloat(document.getElementById('rfRate')?.value) || 4.5) / 100.0;
  const rfX = toScreenX(0);
  const rfY = toScreenY(rfRate);
  const tangX = toScreenX(maxSharpePortfolio.vol);
  const tangY = toScreenY(maxSharpePortfolio.ret);

  // Extend CAL line
  const slope = (tangY - rfY) / (tangX - rfX);
  const calEndX = w - padding;
  const calEndY = rfY + slope * (calEndX - rfX);

  ctx.strokeStyle = '#E5B958';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(rfX, rfY);
  ctx.lineTo(calEndX, calEndY);
  ctx.stroke();

  // 3. Draw Individual Asset Points
  assets.forEach(a => {
    const ax = toScreenX(a.vol);
    const ay = toScreenY(a.ret);

    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(ax, ay, 4.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#94A3B8';
    ctx.font = '11px "Fira Code", monospace';
    ctx.fillText(a.ticker, ax + 8, ay - 6);
  });

  // 4. Draw Minimum Variance Point (Glowing Triangle ▲)
  if (minVarPortfolio) {
    const mvX = toScreenX(minVarPortfolio.vol);
    const mvY = toScreenY(minVarPortfolio.ret);

    ctx.fillStyle = '#00F0FF';
    ctx.beginPath();
    ctx.moveTo(mvX, mvY - 8);
    ctx.lineTo(mvX - 7, mvY + 6);
    ctx.lineTo(mvX + 7, mvY + 6);
    ctx.closePath();
    ctx.fill();
  }

  // 5. Draw Tangency Max Sharpe Point (Glowing Star ★)
  if (maxSharpePortfolio) {
    ctx.fillStyle = '#E5B958';
    ctx.beginPath();
    ctx.arc(tangX, tangY, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }
}

// HOVER TOOLTIP INTERACTION
function handleCanvasHover(e) {
  if (!canvas || sampledPortfolios.length === 0)
    return;
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;

  const padding = 50;
  const w = canvas.width;
  const h = canvas.height;
  const assets = currentUniverse.assets;

  let maxVol =
      Math.max(
          ...sampledPortfolios.map(p => p.vol), ...assets.map(a => a.vol)) *
      1.15;
  let minVol = 0;
  let maxRet =
      Math.max(
          ...sampledPortfolios.map(p => p.ret), ...assets.map(a => a.ret)) *
      1.15;
  let minRet =
      Math.min(
          ...sampledPortfolios.map(p => p.ret), ...assets.map(a => a.ret), 0) *
      0.9;

  function toScreenX(vol) {
    return padding + ((vol - minVol) / (maxVol - minVol)) * (w - padding * 2);
  }
  function toScreenY(ret) {
    return h - padding -
        ((ret - minRet) / (maxRet - minRet)) * (h - padding * 2);
  }

  // Find closest portfolio point
  let closest = null;
  let minDist = 20;

  sampledPortfolios.forEach(p => {
    const px = toScreenX(p.vol);
    const py = toScreenY(p.ret);
    const dist = Math.hypot(px - mx, py - my);
    if (dist < minDist) {
      minDist = dist;
      closest = p;
    }
  });

  const tooltip = document.getElementById('chartTooltip');
  if (closest && tooltip) {
    tooltip.style.display = 'block';
    tooltip.style.left = `${mx + 15}px`;
    tooltip.style.top = `${my - 30}px`;
    tooltip.innerHTML = `
            <div><strong>PORTFOLIO METRICS</strong></div>
            <div>Return E(R): ${(closest.ret * 100).toFixed(2)}%</div>
            <div>Risk (σ): ${(closest.vol * 100).toFixed(2)}%</div>
            <div>Sharpe Ratio: ${closest.sharpe.toFixed(3)}</div>
        `;
  } else if (tooltip) {
    tooltip.style.display = 'none';
  }
}

// UPDATE ASSET SUMMARY TABLE
function updateAssetSummaryTable(rfRate) {
  const tbody = document.querySelector('#assetSummaryTable tbody');
  if (!tbody)
    return;
  tbody.innerHTML = '';

  currentUniverse.assets.forEach(a => {
    const sharpe = (a.ret - rfRate) / a.vol;
    const row = document.createElement('tr');
    row.innerHTML = `
            <td><strong>${a.ticker}</strong></td>
            <td>${(a.ret * 100).toFixed(2)}%</td>
            <td>${(a.vol * 100).toFixed(2)}%</td>
            <td class="${sharpe > 0.5 ? 'cyan-text' : 'muted'}">${sharpe.toFixed(3)}</td>
        `;
    tbody.appendChild(row);
  });
}

// UPDATE WEIGHTS TABLE
function updateWeightsTable() {
  const tbody = document.querySelector('#weightsTable tbody');
  if (!tbody || !minVarPortfolio || !maxSharpePortfolio)
    return;
  tbody.innerHTML = '';

  const colors = [ '#00F0FF', '#E5B958', '#50FA7B', '#FF79C6', '#BD93F9' ];

  currentUniverse.assets.forEach((a, i) => {
    const minW = (minVarPortfolio.weights[i] * 100).toFixed(2);
    const tangW = (maxSharpePortfolio.weights[i] * 100).toFixed(2);
    const color = colors[i % colors.length];

    const row = document.createElement('tr');
    row.innerHTML = `
            <td><strong>${a.ticker}</strong></td>
            <td>${minW}%</td>
            <td class="gold-text"><strong>${tangW}%</strong></td>
            <td>
                <div class="weight-bar-container">
                    <div class="weight-segment" style="width: ${tangW}%; background-color: ${color};"></div>
                </div>
            </td>
        `;
    tbody.appendChild(row);
  });
}

// CUSTOM TICKERS FUNCTION
function applyCustomTickers() {
  const input = document.getElementById('customTickers')?.value;
  if (!input)
    return;
  const tickers = input.split(',')
                      .map(t => t.trim().toUpperCase())
                      .filter(t => t.length > 0);
  if (tickers.length < 2)
    return;

  // Generate synthetic universe for custom tickers
  const customAssets = tickers.map((t, idx) => ({
                                     ticker : t,
                                     ret : 0.10 + Math.random() * 0.15,
                                     vol : 0.15 + Math.random() * 0.20
                                   }));

  const n = customAssets.length;
  const customCorr = Array(n).fill(0).map(
      (_, i) => Array(n).fill(0).map(
          (_, j) => (i === j ? 1.0 : 0.3 + Math.random() * 0.4)));

  UNIVERSES['custom'] = {
    name : "Custom",
    assets : customAssets,
    correlations : customCorr
  };
  currentUniverseKey = 'custom';
  currentUniverse = UNIVERSES['custom'];

  runOptimization();
}
