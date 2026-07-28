/* ==========================================================================
   AXIOM QUANT — LANDING PAGE ENGINE v1.0
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initSpectralCanvas();
    initLiveLatencyTicker();
});

/* 1. BACKGROUND SPECTRAL CANVAS */
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

/* 2. LIVE LATENCY TICKER */
function initLiveLatencyTicker() {
    const ticker = document.getElementById('liveLatency');
    if (!ticker) return;
    setInterval(() => {
        const latency = (0.00035 + Math.random() * 0.00015).toFixed(5);
        ticker.innerText = `${latency} ns`;
    }, 1800);
}
