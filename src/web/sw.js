const CACHE = 'gocb2-v2';
const URLS = [
  '/',
  '/index.html',
  '/manifest.json',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const { request } = e;
  if (request.url.startsWith('chrome-extension://')) return;
  // Skip CDN resources that don't support CORS
  if (request.url.includes('tailwindcss.com') || request.url.includes('googleapis.com')) {
    e.respondWith(fetch(request).catch(() => new Response('', {status: 503})));
    return;
  }
  e.respondWith(
    caches.match(request).then(r => r || fetch(request).then(res => {
      if (res.ok && request.url.startsWith(location.origin)) {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(request, clone));
      }
      return res;
    }).catch(() => caches.match('/')))
  );
});
