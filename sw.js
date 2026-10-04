// Serves the new tab from cache so opening one never waits on the network.
// GitHub Pages pins Cache-Control to max-age=600 and offers no way to change
// it, so past ten minutes the browser must revalidate — a cold DNS + TLS
// handshake before a byte of HTML parses. Answering from here skips the
// network entirely rather than merely making it faster.

const CACHE = 'homepage-v1';
const PAGE = './';

// 'reload' bypasses the HTTP cache. Without it a refresh landing inside the
// 600-second window would re-read the same stale copy and the cache would
// never pick up a deploy.
const freshPage = () => fetch(new Request(PAGE, { cache: 'reload' }));

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => freshPage().then(res => cache.put(PAGE, res)))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  // Only the new tab navigation is answered from cache. checkLiveness() probes
  // local services to find out whether they are up right now; served from a
  // cache it would report a stale "online" forever instead of failing loudly.
  if (event.request.mode !== 'navigate') return;

  event.respondWith(
    caches.open(CACHE).then(cache =>
      cache.match(PAGE).then(cached => {
        const fresh = freshPage()
          .then(res => {
            if (res.ok) cache.put(PAGE, res.clone());
            return res;
          })
          .catch(() => cached);

        // The refetch outlives the response, so it needs waitUntil or the
        // worker can be killed before the new copy is written.
        event.waitUntil(fresh);
        return cached || fresh;
      })
    )
  );
});
