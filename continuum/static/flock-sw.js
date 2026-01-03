// ═══════════════════════════════════════════════════════════════════════════════
//     WILDFIRE SERVICE WORKER
//     Offline Persistence & Anti-Censorship Cache
//     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
// ═══════════════════════════════════════════════════════════════════════════════

const CACHE_NAME = 'continuum-flock-v2';
const ASSETS = [
    '/',
    '/flock.html',
    '/flock.js',
    '/static/models/neural_attention.onnx',
    '/static/models/neural_attention.quant.onnx',
    'https://cdn.tailwindcss.com',
    'https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/ort.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'
];

// Install: Cache the revolution
self.addEventListener('install', (event) => {
    console.log('[Wildfire] Installing ServiceWorker...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Wildfire] Caching core assets');
            return cache.addAll(ASSETS);
        })
    );
});

// Activate: Clean up old versions
self.addEventListener('activate', (event) => {
    console.log('[Wildfire] Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Wildfire] Removing old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Fetch: Offline-First Strategy
// 1. Try Cache
// 2. If miss, Try Network
// 3. If Network fails, serve Fallback (or nothing)
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // Handle ONNX models with special care (large files)
    if (event.request.url.includes('.onnx')) {
        event.respondWith(
            caches.open(CACHE_NAME).then((cache) => {
                return cache.match(event.request).then((response) => {
                    if (response) return response;
                    return fetch(event.request).then((networkResponse) => {
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                });
            })
        );
        return;
    }

    // Standard Stale-While-Revalidate for UI
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request).then((networkResponse) => {
                // Update cache with new version
                if (networkResponse && networkResponse.status === 200) {
                    const responseToCache = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseToCache);
                    });
                }
                return networkResponse;
            }).catch(() => {
                // Network failed, do nothing (we rely on cache)
            });

            return cachedResponse || fetchPromise;
        })
    );
});

// P2P Coordination via ServiceWorker (Future)
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// ═══════════════════════════════════════════════════════════════════════════════
//     JACKKNIFE AI
//     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
// ═══════════════════════════════════════════════════════════════════════════════
