z// static/service-worker.js
const CACHE_NAME = 'spicerhome_cache_v1';
const urlsToCache = [
  '/',
  '/internal/chores/',
  '/internal/search',
  '/internal/admin/',
  '/internal/search/track',
  '/internal/search/history',
  '/internal/search/commands'
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