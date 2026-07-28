/* ==========================================================================
   AXIOM QUANT — RESEARCH PORTAL & WEB WORKER ORCHESTRATOR
   ========================================================================== */

let computeWorker = null;

document.addEventListener('DOMContentLoaded', () => {
    initWebWorker();
    initServiceWorker();

    // Initial paper typesetting
    if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise();
    }
});

/* 1. INITIALIZE WEB WORKER */
function initWebWorker() {
    if (window.Worker) {
        computeWorker = new Worker('/worker.js');

        computeWorker.onmessage = function(e) {
            const { type, payload } = e.data;

            if (type === 'GBM_RESULTS') {
                console.log('[Worker] Monte Carlo GBM simulation complete:', payload);
            } else if (type === 'VPIN_RESULTS') {
                console.log('[Worker] VPIN Toxicity calculation complete:', payload);
            } else if (type === 'ERDOS_RESULTS') {
                console.log('[Worker] Erdős graph sampling complete:', payload);
            }
        };

        // Dispatch background warmup calculation
        computeWorker.postMessage({ type: 'SIMULATE_GBM', payload: { S: 100, vol: 0.2, r: 0.05, T: 1, numPaths: 1000 } });
        computeWorker.postMessage({ type: 'SIMULATE_ERDOS_GRAPH', payload: { n: 100, p: 0.02 } });
    }
}

/* 2. INITIALIZE SERVICE WORKER (PWA) */
function initServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('[SW] ServiceWorker registered:', reg.scope))
            .catch(err => console.warn('[SW] ServiceWorker registration failed:', err));
    }
}

/* Tab Switching between Monograph Papers */
function loadPaper(paperId) {
    const navItems = document.querySelectorAll('.paper-nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('data-paper') === paperId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    const paperViews = document.querySelectorAll('.paper-content');
    paperViews.forEach(view => {
        if (view.id === `paper-${paperId}`) {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });

    const breadcrumb = document.getElementById('paperBreadcrumb');
    if (breadcrumb) {
        const titles = {
            'concept-map': 'MONOGRAPH // 01 // CONCEPT MAP',
            'ultramarathon': 'MONOGRAPH // 02 // THE ULTRAMARATHON',
            'dyadic-ternary': 'MONOGRAPH // 03 // DYADIC-TERNARY BRIDGE',
            'microstructure-chaos': 'MONOGRAPH // 04 // MICROSTRUCTURE & CHAOS',
            'transfer-operator': 'MONOGRAPH // 05 // TRANSFER OPERATOR',
            'black-scholes': 'MONOGRAPH // 06 // BLACK-SCHOLES GREEKS',
            'backyard-ultra': 'MONOGRAPH // 08 // BACKYARD ULTRA LOOP ENGINEERING',
            'bibliography': 'CATALOG // FOUNDATIONAL BIBLIOGRAPHY'
        };
        breadcrumb.innerText = titles[paperId] || 'MONOGRAPH // RESEARCH';
    }

    const content = document.querySelector('.portal-content');
    if (content) content.scrollTop = 0;

    if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise();
    }
}

/* Real-time Paper & Concept Filtering */
function filterPapers() {
    const query = document.getElementById('paperSearch').value.toLowerCase();
    const navItems = document.querySelectorAll('.paper-nav-item');

    navItems.forEach(item => {
        const title = item.querySelector('.p-title').innerText.toLowerCase();
        const sub = item.querySelector('.p-sub').innerText.toLowerCase();
        
        if (title.includes(query) || sub.includes(query)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}
