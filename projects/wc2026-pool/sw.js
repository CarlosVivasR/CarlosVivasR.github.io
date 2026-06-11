/* Service worker — network-first (always fresh while we iterate; cache = offline fallback).
   Bump CACHE to force clients to drop the old cache. */
const CACHE = 'wc26-v37';
self.addEventListener('install', e=>{ self.skipWaiting(); });
self.addEventListener('activate', e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', e=>{
  const req=e.request;
  if(req.method!=='GET' || new URL(req.url).origin!==location.origin) return;
  e.respondWith(
    fetch(req).then(res=>{
      const copy=res.clone();
      caches.open(CACHE).then(c=>c.put(req,copy)).catch(()=>{});
      return res;
    }).catch(()=> caches.match(req))
  );
});
