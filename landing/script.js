/* ==========================================================================
   AXIOM QUANT — PLATFORM ENGINE v1.0
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initSpectralCanvas();
    initTabNavigation();
    initQuantChartCanvas();
    initTelemetryTicker();
    updateCertificate();
});

/* 1. TAB NAVIGATION SWITCHER */
function switchTab(tabId) {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navButtons.forEach(btn => {
        if (btn.getAttribute('data-tab') === tabId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    tabContents.forEach(content => {
        if (content.id === tabId) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });

    // Resize chart canvas if switching to terminal tab
    if (tabId === 'terminal-tab') {
        setTimeout(resizeQuantCanvas, 50);
    }
}

function initTabNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-tab');
            switchTab(target);
        });
    });
}

/* 2. BACKGROUND SPECTRAL CANVAS */
function initSpectralCanvas() {
    const canvas = document.getElementById('spectralCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let width, height, cx, cy;
    let mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    let time = 0;

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        cx = width / 2;
        cy = height / 2;
    }

    window.addEventListener('resize', resize);
    resize();

    window.addEventListener('mousemove', (e) => {
        mouse.targetX = (e.clientX - cx) / cx;
        mouse.targetY = (e.clientY - cy) / cy;
    });

    const particles = [];
    for (let i = 0; i < 140; i++) {
        particles.push({
            r: Math.random() * Math.min(width, height) * 0.45,
            angle: Math.random() * Math.PI * 2,
            speed: (Math.random() * 0.0008 + 0.0002) * (Math.random() > 0.5 ? 1 : -1),
            size: Math.random() * 1.8 + 0.5,
            color: Math.random() > 0.45 ? '#00F0FF' : '#E5B958',
            alpha: Math.random() * 0.35 + 0.1
        });
    }

    function render() {
        time += 0.015;
        mouse.x += (mouse.targetX - mouse.x) * 0.05;
        mouse.y += (mouse.targetY - mouse.y) * 0.05;

        ctx.fillStyle = '#06070B';
        ctx.fillRect(0, 0, width, height);

        // Grid
        ctx.strokeStyle = 'rgba(30, 41, 59, 0.15)';
        ctx.lineWidth = 0.5;
        for (let x = 0; x < width; x += 60) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
        }
        for (let y = 0; y < height; y += 60) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
        }

        // Concentric Rings
        const ringRadii = [60, 120, 200, 310, 440];
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.12)';
        ctx.lineWidth = 0.6;
        ringRadii.forEach((r, idx) => {
            ctx.beginPath();
            ctx.arc(cx + mouse.x * (idx + 1) * 6, cy + mouse.y * (idx + 1) * 6, r, 0, Math.PI * 2);
            ctx.stroke();
        });

        // Golden Ratio Circle
        ctx.strokeStyle = 'rgba(229, 185, 88, 0.35)';
        ctx.setLineDash([4, 6]);
        ctx.beginPath();
        ctx.arc(cx, cy, 216.18, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Quantum Waveforms
        const colors = ['rgba(0, 240, 255, 0.6)', 'rgba(229, 185, 88, 0.4)', 'rgba(148, 163, 184, 0.25)'];
        [0, 15, -15].forEach((offsetY, i) => {
            ctx.beginPath();
            ctx.strokeStyle = colors[i];
            ctx.lineWidth = 1.0;

            for (let x = 0; x < width; x += 4) {
                const normX = (x - cx) / 160;
                const gaussian = Math.exp(-Math.pow(normX, 2) / 2);
                const wave = Math.cos(normX * 3.5 - time + mouse.x * 2) * gaussian * 120;
                const y = cy + offsetY + wave + mouse.y * 15;

                if (x === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
        });

        // Golden Spiral
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(229, 185, 88, 0.35)';
        ctx.lineWidth = 0.8;
        const a = 2.0, b = 0.14;
        for (let theta = 0; theta < Math.PI * 8; theta += 0.05) {
            const r = a * Math.exp(b * theta);
            const x = cx + r * Math.cos(theta + time * 0.08);
            const y = cy + r * Math.sin(theta + time * 0.08);
            if (theta === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // Particles
        particles.forEach((p) => {
            p.angle += p.speed;
            const px = cx + p.r * Math.cos(p.angle) + mouse.x * 15;
            const py = cy + p.r * Math.sin(p.angle) + mouse.y * 15;

            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.alpha;
            ctx.beginPath();
            ctx.arc(px, py, p.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        });

        requestAnimationFrame(render);
    }
    render();
}

/* 3. INTERACTIVE 0xTERMINAL CHART CANVAS & SIMULATOR */
let currentSimMode = 'gbm';
let quantCanvas, quantCtx;

function initQuantChartCanvas() {
    quantCanvas = document.getElementById('quantChartCanvas');
    if (!quantCanvas) return;
    quantCtx = quantCanvas.getContext('2d');

    window.addEventListener('resize', resizeQuantCanvas);
    resizeQuantCanvas();
    renderSimulation(currentSimMode);
}

function resizeQuantCanvas() {
    if (!quantCanvas) return;
    const rect = quantCanvas.parentElement.getBoundingClientRect();
    quantCanvas.width = rect.width - 32;
    quantCanvas.height = rect.height - 50;
    renderSimulation(currentSimMode);
}

function runSim(mode) {
    currentSimMode = mode;
    const titleEl = document.getElementById('canvasTitle');

    if (mode === 'gbm') {
        if (titleEl) titleEl.innerText = 'GEOMETRIC BROWNIAN MOTION (MONTE CARLO SDE)';
        appendLog('cmd', '0x> simulate --gbm --drift=0.08 --vol=0.25 --paths=50');
        appendLog('output', 'Running 50 Stochastic Paths (dt=0.01)... Convergence Verified.');
    } else if (mode === 'greeks') {
        if (titleEl) titleEl.innerText = 'OPTION GREEKS PROFILE (DELTA & GAMMA)';
        appendLog('cmd', '0x> calculate --greeks --spot=100 --strike=105 --vol=0.20');
        appendLog('output', 'Black-Scholes Delta (Δ): 0.584 | Gamma (Γ): 0.038 | Vega (ν): 0.312');
    } else if (mode === 'orderbook') {
        if (titleEl) titleEl.innerText = 'LEVEL-2 LIMIT ORDER BOOK DEPTH';
        appendLog('cmd', '0x> inspect --orderbook --depth=15 --spread=0.05');
        appendLog('output', 'L2 Depth Active: Bid Vol = 142,500 | Ask Vol = 138,900 | Mid = 100.025');
    } else if (mode === 'frontier') {
        if (titleEl) titleEl.innerText = 'MARKOWITZ EFFICIENT FRONTIER OPTIMIZATION';
        appendLog('cmd', '0x> optimize --frontier --assets=4 --target-return=0.15');
        appendLog('output', 'Optimal Sharpe Ratio: 2.14 | Min Variance Weight Vector: [0.35, 0.25, 0.20, 0.20]');
    }

    renderSimulation(mode);
}

function renderSimulation(mode) {
    if (!quantCtx || !quantCanvas) return;
    const w = quantCanvas.width;
    const h = quantCanvas.height;

    quantCtx.fillStyle = '#020305';
    quantCtx.fillRect(0, 0, w, h);

    // Chart grid
    quantCtx.strokeStyle = 'rgba(30, 41, 59, 0.3)';
    quantCtx.lineWidth = 0.5;
    for (let x = 0; x < w; x += 40) {
        quantCtx.beginPath(); quantCtx.moveTo(x, 0); quantCtx.lineTo(x, h); quantCtx.stroke();
    }
    for (let y = 0; y < h; y += 40) {
        quantCtx.beginPath(); quantCtx.moveTo(0, y); quantCtx.lineTo(w, y); quantCtx.stroke();
    }

    if (mode === 'gbm') {
        // Render 25 Stochastic Paths
        const steps = 100;
        for (let path = 0; path < 25; path++) {
            quantCtx.beginPath();
            quantCtx.strokeStyle = path === 0 ? '#00F0FF' : (path === 1 ? '#E5B958' : 'rgba(148, 163, 184, 0.25)');
            quantCtx.lineWidth = path < 2 ? 1.5 : 0.8;

            let price = h / 2;
            quantCtx.moveTo(0, price);

            for (let s = 1; s <= steps; s++) {
                const x = (s / steps) * w;
                const change = (Math.random() - 0.48) * 14;
                price -= change;
                price = Math.max(10, Math.min(h - 10, price));
                quantCtx.lineTo(x, price);
            }
            quantCtx.stroke();
        }
    } else if (mode === 'greeks') {
        // Render Delta & Gamma curves
        quantCtx.beginPath();
        quantCtx.strokeStyle = '#00F0FF';
        quantCtx.lineWidth = 2;
        for (let x = 0; x < w; x += 2) {
            const normX = (x / w - 0.5) * 6;
            const delta = 1 / (1 + Math.exp(-normX));
            const y = h - (delta * (h - 40) + 20);
            if (x === 0) quantCtx.moveTo(x, y);
            else quantCtx.lineTo(x, y);
        }
        quantCtx.stroke();

        // Gamma curve
        quantCtx.beginPath();
        quantCtx.strokeStyle = '#E5B958';
        quantCtx.lineWidth = 1.5;
        for (let x = 0; x < w; x += 2) {
            const normX = (x / w - 0.5) * 4;
            const gamma = Math.exp(-normX * normX / 2);
            const y = h - (gamma * (h - 80) + 20);
            if (x === 0) quantCtx.moveTo(x, y);
            else quantCtx.lineTo(x, y);
        }
        quantCtx.stroke();
    } else if (mode === 'orderbook') {
        // Render Bids (Green) & Asks (Red) Depth Bars
        const numBars = 15;
        const barWidth = (w / 2 - 20) / numBars;

        for (let i = 0; i < numBars; i++) {
            // Bids
            const bidVol = (numBars - i) * 18 + Math.random() * 10;
            const bh = (bidVol / (numBars * 20)) * (h - 40);
            quantCtx.fillStyle = 'rgba(80, 250, 123, 0.4)';
            quantCtx.strokeStyle = '#50FA7B';
            quantCtx.fillRect(w / 2 - (i + 1) * barWidth, h - bh - 20, barWidth - 2, bh);
            quantCtx.strokeRect(w / 2 - (i + 1) * barWidth, h - bh - 20, barWidth - 2, bh);

            // Asks
            const askVol = (i + 1) * 18 + Math.random() * 10;
            const ah = (askVol / (numBars * 20)) * (h - 40);
            quantCtx.fillStyle = 'rgba(255, 85, 85, 0.4)';
            quantCtx.strokeStyle = '#FF5555';
            quantCtx.fillRect(w / 2 + i * barWidth, h - ah - 20, barWidth - 2, ah);
            quantCtx.strokeRect(w / 2 + i * barWidth, h - ah - 20, barWidth - 2, ah);
        }
    } else if (mode === 'frontier') {
        // Render Markowitz Parabola & Tangency Line
        quantCtx.beginPath();
        quantCtx.strokeStyle = '#E5B958';
        quantCtx.lineWidth = 2.0;

        for (let y = 30; y < h - 30; y += 2) {
            const normY = (y - h / 2) / (h / 3);
            const x = 50 + normY * normY * 180;
            if (y === 30) quantCtx.moveTo(x, y);
            else quantCtx.lineTo(x, y);
        }
        quantCtx.stroke();

        // Capital Allocation Line (CAL)
        quantCtx.beginPath();
        quantCtx.strokeStyle = '#00F0FF';
        quantCtx.lineWidth = 1.5;
        quantCtx.moveTo(20, h - 30);
        quantCtx.lineTo(w - 40, 40);
        quantCtx.stroke();
    }
}

/* 4. CONSOLE INPUT PARSER */
function handleConsoleSubmit(event) {
    event.preventDefault();
    const input = document.getElementById('consoleInput');
    if (!input || !input.value.trim()) return;

    const cmd = input.value.trim();
    input.value = '';
    appendLog('cmd', `0x> ${cmd}`);

    const lower = cmd.toLowerCase();
    if (lower.includes('help')) {
        appendLog('info', 'Available commands: gbm, greeks, orderbook, frontier, clear');
    } else if (lower.includes('clear')) {
        const consoleLogs = document.getElementById('consoleOutput');
        if (consoleLogs) consoleLogs.innerHTML = '';
    } else if (lower.includes('gbm') || lower.includes('simulate')) {
        runSim('gbm');
    } else if (lower.includes('greeks')) {
        runSim('greeks');
    } else if (lower.includes('orderbook')) {
        runSim('orderbook');
    } else if (lower.includes('frontier') || lower.includes('optimize')) {
        runSim('frontier');
    } else {
        appendLog('output', `Executing instruction '${cmd}'... Processed with status 0x00.`);
    }
}

function appendLog(type, text) {
    const consoleLogs = document.getElementById('consoleOutput');
    if (!consoleLogs) return;

    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.innerText = text;
    consoleLogs.appendChild(line);
    consoleLogs.scrollTop = consoleLogs.scrollHeight;
}

/* 5. CERTIFICATE PREVIEW GENERATOR */
function updateCertificate() {
    const nameInput = document.getElementById('studentName');
    const trackSelect = document.getElementById('trackSelect');
    const nameDisplay = document.getElementById('certNameDisplay');
    const trackDisplay = document.getElementById('certTrackDisplay');

    if (nameInput && nameDisplay) {
        nameDisplay.innerText = nameInput.value.toUpperCase() || 'SCHOLAR NAME';
    }
    if (trackSelect && trackDisplay) {
        trackDisplay.innerText = trackSelect.value;
    }
}

/* 6. TELEMETRY & FORM HANDLERS */
function initTelemetryTicker() {
    const ticker = document.getElementById('heroLatency');
    if (!ticker) return;
    setInterval(() => {
        const latency = (0.00035 + Math.random() * 0.00015).toFixed(5);
        ticker.innerText = `${latency} ns`;
    }, 1800);
}

function handleAccessSubmit(event) {
    event.preventDefault();
    const emailInput = document.getElementById('userEmail');
    const feedback = document.getElementById('accessFeedback');
    const btn = document.getElementById('accessBtn');

    if (!emailInput || !emailInput.value) return;

    btn.disabled = true;
    btn.innerHTML = '<span>AUTHENTICATING...</span>';

    setTimeout(() => {
        feedback.className = 'form-feedback success';
        feedback.innerText = '✓ INSTITUTIONAL KEY VERIFIED :: ACCESS GRANTED FOR AXIOM QUANT FOUNDATION V1';
        emailInput.value = '';
        btn.disabled = false;
        btn.innerHTML = '<span>INITIALIZE ACCESS</span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    }, 1000);
}
