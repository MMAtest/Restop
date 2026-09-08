// Service Worker ResTop - v1.2.0
// IMPORTANT: Les API ne sont JAMAIS mises en cache (toujours du réseau frais)
// Seuls les assets statiques (HTML, CSS, JS, images) sont cachés
const CACHE_NAME = 'restop-v1.2.0';
const STATIC_ASSETS = [
  '/',
  '/manifest.json'
];

// Installation
self.addEventListener('install', (event) => {
  console.log('🚀 SW Install v1.2.0');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activation : on supprime tous les anciens caches
self.addEventListener('activate', (event) => {
  console.log('✅ SW Activate v1.2.0');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Suppression cache obsolète:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Stratégie fetch
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  const isAPIRequest = url.pathname.includes('/api/');

  // ❌ JAMAIS de cache pour les API : toujours réseau frais
  if (isAPIRequest) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' })
        .catch(() => new Response(
          JSON.stringify({ error: 'offline' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        ))
    );
    return;
  }

  // Pour les autres requêtes : Cache First avec mise à jour réseau
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
        }
        return networkResponse;
      }).catch(() => {
        if (event.request.destination === 'document') {
          return new Response(`
            <!DOCTYPE html>
            <html><head><meta charset="utf-8"><title>ResTop - Hors ligne</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>body{font-family:-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f9fafb;text-align:center;padding:20px}.c{background:white;padding:40px;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,.1);max-width:400px}h1{color:#2C4A3B}button{background:#2C4A3B;color:white;border:none;padding:12px 24px;border-radius:8px;cursor:pointer;font-weight:600}</style>
            </head><body><div class="c"><div style="font-size:64px">📱</div><h1>Mode Hors Ligne</h1><p>Connexion internet requise.</p><button onclick="location.reload()">Réessayer</button></div></body></html>
          `, { headers: { 'Content-Type': 'text/html' } });
        }
      });
      return cachedResponse || fetchPromise;
    })
  );
});

// Notifications push
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'Nouvelle notification ResTop',
    icon: '/manifest.json',
    badge: '/manifest.json',
    vibrate: [100, 50, 100]
  };
  event.waitUntil(
    self.registration.showNotification('ResTop - La Table d\'Augustine', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow('/'));
});

// Permettre au front de forcer le skipWaiting (mise à jour immédiate)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
