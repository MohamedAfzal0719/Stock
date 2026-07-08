self.addEventListener('push', function(event) {
  if (!event.data) {
    console.log('Push event received with no data.');
    return;
  }

  let data = {};
  try {
    data = event.data.json();
  } catch (e) {
    data = { title: 'GoldBeES AI Signal Update', body: event.data.text() };
  }

  const options = {
    body: data.body || 'A new AI trading recommendation is available!',
    icon: data.icon || '/icon.png',
    badge: data.badge || '/badge.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1',
      url: data.url || '/'
    },
    actions: [
      { action: 'explore', title: 'Open Dashboard', icon: '/icon.png' },
      { action: 'close', title: 'Dismiss' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'GoldBeES Alert', options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(function(clientList) {
      for (let i = 0; i < clientList.length; i++) {
        let client = clientList[i];
        if (client.url === '/' && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});
