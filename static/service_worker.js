const CACHE_NAME = "voiceaura-v1";

const urlsToCache = [
  "/",
  "/static/main_logo.png",
  "/static/mini_icon.png",
  "/static/manifest.json"
];

self.addEventListener("install", function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener("fetch", function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
  );
});