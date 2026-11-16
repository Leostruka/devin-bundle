/* Atlas service worker: offline shell + lazy bodies.
   Precaches the app shell; runtime-caches data/*.html and raw/* with
   stale-while-revalidate so new deploys flow through automatically.
   Cache version bumps on deploy via ?v= query on sw.js registration. */
const CACHE = "atlas-v1";
const SHELL = ["./", "index.html", "app.js", "style.css"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))
                .then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE)
                                .map(k => caches.delete(k))))
      .then(() => self.clients.claim()));
});

function swr(req) {
  return caches.open(CACHE).then(c =>
    c.match(req).then(hit => {
      const net = fetch(req).then(res => {
        if (res.ok) c.put(req, res.clone());
        return res;
      }).catch(() => hit);
      return hit || net;
    }));
}

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (SHELL.some(s => url.pathname.endsWith(s)) ||
      url.pathname.includes("/data/") ||
      url.pathname.includes("/raw/") ||
      url.pathname.endsWith("/") || url.pathname.endsWith("index.html")) {
    e.respondWith(swr(e.request));
  }
});
