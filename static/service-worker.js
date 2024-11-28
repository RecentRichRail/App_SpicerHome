// static/service-worker.js
const CACHE_NAME = 'spicerhome_cache_v1';
const urlsToCache = [
  '/',
  '/static/styles.css',
  '/static/scripts.js',
  '/internal/chores/',
  '/internal/search/',
  '/internal/admin/'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});