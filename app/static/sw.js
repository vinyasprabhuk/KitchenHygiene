// Minimal service worker -- present only so the browser considers this
// installable as a PWA. No offline caching: every page here needs a live
// server round-trip anyway (login, photo upload, live data), so caching
// would just risk showing stale content for no real benefit.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {});
