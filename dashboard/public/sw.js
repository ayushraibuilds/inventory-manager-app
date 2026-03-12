const CACHE_NAME = 'ondc-super-seller-v3';

self.addEventListener('install', () => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;

    // Never intercept API calls — let them go straight to the network.
    // This prevents Cache.put() errors from opaque/streaming responses.
    if (event.request.url.includes('/api/')) return;

    // Cache-first for static assets only
    if (event.request.url.includes('/_next/static/')) {
        event.respondWith(
            caches.match(event.request).then((cached) =>
                cached || fetch(event.request).then((res) => {
                    if (res.ok) {
                        const clone = res.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    }
                    return res;
                })
            )
        );
    }
});
