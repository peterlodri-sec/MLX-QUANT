/* ==========================================================================
   AXIOM QUANT — SERVICE WORKER (OFFLINE PWA CACHE)
   ========================================================================== */

const CACHE_NAME = 'axiom-quant-v1.0';
const ASSETS = [
    '/',
    '/index.html',
    '/style.css',
    '/script.js',
    '/worker.js',
    '/markowitz',
    '/black-scholes',
    '/microstructure',
    '/thresholds',
    '/dyadic'
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS);
        })
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            );
        })
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
    );
});
