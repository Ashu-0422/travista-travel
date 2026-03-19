(function registerPwa() {
  if (!("serviceWorker" in navigator)) {
    return;
  }

  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {
      // Service worker registration failed; app still works without offline cache.
    });
  });
})();
