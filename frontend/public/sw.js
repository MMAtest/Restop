const CACHE_NAME = 'restop-v1.1.0';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json'
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
  console.log('🚀 Service Worker: Installation');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('📦 Cache ouvert');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
  console.log('✅ Service Worker: Activation');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Suppression ancien cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Interception des requêtes (Network First pour API, Cache First pour assets)
self.addEventListener('fetch', (event) => {
  // Détecter si c'est une requête API
  const isAPIRequest = event.request.url.includes('/api/');
  
  if (isAPIRequest) {
    // Network First pour les API (données dynamiques)
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Cloner la réponse pour le cache
          const responseToCache = response.clone();
          
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });
          
          return response;
        })
        .catch(() => {
          // Si réseau échoue, utiliser le cache
          return caches.match(event.request);
        })
    );
  } else {
    // Cache First pour les assets statiques (CSS, JS, images)
    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          // Retourner du cache si disponible
          if (response) {
            return response;
          }
          
          // Sinon, faire la requête réseau
          return fetch(event.request).then((response) => {
            // Vérifier si c'est une réponse valide
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Cloner la réponse pour le cache
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return response;
          }).catch(() => {
            // Mode offline - retourner page d'erreur basique
            if (event.request.destination === 'document') {
              return new Response(`
                <!DOCTYPE html>
                <html>
                  <head>
                    <meta charset="utf-8">
                    <title>ResTop - Offline</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                      body { 
                        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                        display: flex; align-items: center; justify-content: center;
                        min-height: 100vh; margin: 0; background: #f9fafb;
                        text-align: center; padding: 20px;
                      }
                      .offline-container { 
                        background: white; padding: 40px; border-radius: 12px; 
                        box-shadow: 0 4px 16px rgba(0,0,0,0.1); max-width: 400px;
                      }
                      .icon { font-size: 64px; margin-bottom: 20px; }
                      h1 { color: #059669; margin: 0 0 16px 0; }
                      p { color: #6b7280; margin: 0 0 24px 0; line-height: 1.5; }
                      button { 
                        background: #10b981; color: white; border: none; 
                        padding: 12px 24px; border-radius: 8px; cursor: pointer;
                        font-weight: 600;
                      }
                    </style>
                  </head>
                  <body>
                    <div class="offline-container">
                      <div class="icon">📱</div>
                      <h1>Mode Hors Ligne</h1>
                      <p>Vous êtes actuellement hors ligne. Certaines fonctionnalités peuvent être limitées.</p>
                      <button onclick="window.location.reload()">🔄 Réessayer</button>
                    </div>
                  </body>
                </html>
              `, {
                headers: {
                  'Content-Type': 'text/html'
                }
              });
            }
          });
        })
    );
  }
});

// Notifications push (pour les missions)
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'Nouvelle notification ResTop',
    icon: '/manifest.json',
    badge: '/manifest.json',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '2'
    },
    actions: [
      {
        action: 'explore', 
        title: 'Voir détails',
        icon: '/images/checkmark.png'
      },
      {
        action: 'close', 
        title: 'Fermer',
        icon: '/images/xmark.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('ResTop - La Table d\'Augustine', options)
  );
});

// Gestion des clics sur notifications
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'explore') {
    // Ouvrir l'app sur la section missions
    event.waitUntil(clients.openWindow('/?tab=dashboard&alert=mission'));
  } else if (event.action === 'close') {
    // Fermer la notification
    event.notification.close();
  } else {
    // Clic sur la notification principale
    event.waitUntil(clients.openWindow('/'));
  }
});