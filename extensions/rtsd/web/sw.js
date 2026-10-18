/* rtsd PWA service worker: cache-first for the app shell only.
   Live state always comes from /snapshot + /ws at runtime. */
var CACHE = "rtsd-v1";
var SHELL = ["./index.html", "./manifest.webmanifest"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return c.addAll(SHELL);
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.map(function (k) {
      if (k !== CACHE) return caches.delete(k);
    }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (e) {
  var u = new URL(e.request.url);
  if (u.origin !== location.origin ||
      /\/(ws|snapshot|decisions|event|intent|health)/.test(u.pathname)) {
    return; // network only for live data
  }
  e.respondWith(caches.match(e.request).then(function (hit) {
    return hit || fetch(e.request);
  }));
});
