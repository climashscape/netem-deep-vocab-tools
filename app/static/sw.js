const CACHE_NAME = 'netem-deep-vocab-v2.0.0';
const ASSETS_TO_CACHE = [
    './',
    './index.html',
    './static/manifest.json',
    './static/netem_full_list.json',
    './static/legacy_data.json',
    './static/lib/tailwind.min.js',
    './static/lib/marked.min.js',
    './static/lib/dexie.min.js',
    './static/lib/font-awesome/css/all.min.css',
    './static/lib/font-awesome/webfonts/fa-solid-900.woff2',
    './static/lib/font-awesome/webfonts/fa-regular-400.woff2',
    './static/lib/font-awesome/webfonts/fa-brands-400.woff2',
    './static/js/db.js',
    './static/js/ebbinghaus.js',
    './static/js/llm.js',
    './static/js/local_api.js',
    './static/img/icon-192.png',
    './static/img/icon-512.png'
];

// Install Event - Caching assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('SW: Pre-caching all static assets');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// Activate Event - Cleaning up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('SW: Deleting old cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch Event - Serving from cache
self.addEventListener('fetch', (event) => {
    // Only intercept GET requests
    if (event.request.method !== 'GET') return;

    const url = new URL(event.request.url);
    
    // Ignore API calls - LocalAPI handles them via fetch proxy in index.html
    if (url.pathname.startsWith('/api/')) {
        return;
    }

    // Ignore cross-origin requests like external images (unless specifically cached later)
    if (url.origin !== self.location.origin) {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }

            return fetch(event.request).then((response) => {
                // Check if valid response to cache
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }

                // Cache static assets dynamically if they weren't in pre-cache
                const responseToCache = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });

                return response;
            }).catch(() => {
                // Final offline fallback
                if (event.request.mode === 'navigate') {
                    return caches.match('./index.html');
                }
            });
        })
    );
});
