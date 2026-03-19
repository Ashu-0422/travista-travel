(() => {
  const hour = new Date().getHours();
  const isDark = hour >= 18 || hour < 6;
  const root = document.documentElement;
  root.dataset.theme = isDark ? "dark" : "light";

  const overlayId = "theme-overlay";
  let overlay = document.getElementById(overlayId);

  if (isDark) {
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = overlayId;
      overlay.style.position = "fixed";
      overlay.style.inset = "0";
      overlay.style.background = "rgba(0, 0, 0, 0.35)";
      overlay.style.pointerEvents = "none";
      overlay.style.zIndex = "9999";
      overlay.style.transition = "opacity 0.6s ease";
      document.body.appendChild(overlay);
    }
    overlay.style.opacity = "1";
  } else if (overlay) {
    overlay.style.opacity = "0";
    setTimeout(() => overlay?.remove(), 700);
  }
})();
