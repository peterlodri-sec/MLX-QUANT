/* ==========================================================================
   AXIOM QUANT — HEAVY COMPUTE WEB WORKER ENGINE
   Runs off-main-thread stochastic simulations & matrix calculations.
   ========================================================================== */

self.onmessage = function(e) {
    const { type, payload } = e.data;

    switch (type) {
        case 'SIMULATE_GBM':
            const gbmResults = runGBMSimulation(payload);
            self.postMessage({ type: 'GBM_RESULTS', payload: gbmResults });
            break;

        case 'CALCULATE_VPIN':
            const vpinResults = runVPINCalculation(payload);
            self.postMessage({ type: 'VPIN_RESULTS', payload: vpinResults });
            break;

        case 'SIMULATE_ERDOS_GRAPH':
            const graphResults = runErdosSimulation(payload);
            self.postMessage({ type: 'ERDOS_RESULTS', payload: graphResults });
            break;

        default:
            console.warn('Unknown worker message type:', type);
    }
};

/* 1. Fast Monte Carlo GBM Simulation (10,000+ paths) */
function runGBMSimulation({ S, vol, r, T, numPaths = 500, steps = 100 }) {
    const dt = T / steps;
    const paths = [];
    const finalPrices = [];

    for (let p = 0; p < numPaths; p++) {
        let price = S;
        const path = [price];

        for (let s = 1; s <= steps; s++) {
            const z = boxMuller();
            price = price * Math.exp((r - 0.5 * vol * vol) * dt + vol * Math.sqrt(dt) * z);
            path.push(price);
        }
        paths.push(path);
        finalPrices.push(price);
    }

    // Calculate mean & VaR (95%)
    finalPrices.sort((a, b) => a - b);
    const meanFinal = finalPrices.reduce((a, b) => a + b, 0) / numPaths;
    const var95 = S - finalPrices[Math.floor(numPaths * 0.05)];

    return { samplePaths: paths.slice(0, 20), meanFinal, var95 };
}

/* Box-Muller Gaussian Noise */
function boxMuller() {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

/* 2. VPIN Toxicity Stream Calculation */
function runVPINCalculation({ buckets = 50, bucketVolume = 10000 }) {
    let totalImbalance = 0;
    const vpinSeries = [];

    for (let b = 0; b < buckets; b++) {
        const buyVol = Math.floor(Math.random() * bucketVolume);
        const sellVol = bucketVolume - buyVol;
        const imbalance = Math.abs(buyVol - sellVol);
        totalImbalance += imbalance;

        const vpin = totalImbalance / ((b + 1) * bucketVolume);
        vpinSeries.push(vpin);
    }

    return { latestVPIN: vpinSeries[vpinSeries.length - 1], vpinSeries };
}

/* 3. Erdős–Rényi Random Graph Sampling */
function runErdosSimulation({ n = 50, p = 0.04 }) {
    let edges = 0;
    let beta1 = 0;

    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            if (Math.random() < p) {
                edges++;
            }
        }
    }

    const components = 1; // Simplification for high p
    beta1 = Math.max(0, edges - n + components);

    return { n, edges, beta1, requiresComplex: beta1 > 0 };
}
