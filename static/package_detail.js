document.addEventListener("DOMContentLoaded", () => {
  const operatorToggle = document.querySelector("[data-operator-toggle]");
  const operatorPanel = document.querySelector("[data-operator-panel]");
  const swipeToggle = document.querySelector("[data-swipe-toggle]");
  const setOperatorVisible = (isOpen) => {
    if (!operatorPanel || !swipeToggle) return;
    operatorPanel.style.display = isOpen ? "block" : "none";
    swipeToggle.classList.toggle("active", isOpen);
    swipeToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  };
  if (swipeToggle && operatorPanel) {
    let startX = 0;
    let currentX = 0;
    let dragging = false;

    const onPointerDown = (e) => {
      dragging = true;
      startX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
      currentX = startX;
    };
    const onPointerMove = (e) => {
      if (!dragging) return;
      currentX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
    };
    const onPointerUp = () => {
      if (!dragging) return;
      dragging = false;
      const delta = currentX - startX;
      if (Math.abs(delta) < 20) {
        const isOpen = operatorPanel.style.display === "block";
        setOperatorVisible(!isOpen);
        return;
      }
      setOperatorVisible(delta > 0);
    };

    swipeToggle.addEventListener("mousedown", onPointerDown);
    swipeToggle.addEventListener("mousemove", onPointerMove);
    swipeToggle.addEventListener("mouseup", onPointerUp);
    swipeToggle.addEventListener("mouseleave", onPointerUp);
    swipeToggle.addEventListener("touchstart", onPointerDown, { passive: true });
    swipeToggle.addEventListener("touchmove", onPointerMove, { passive: true });
    swipeToggle.addEventListener("touchend", onPointerUp);
  }

  const modal = document.getElementById("imageModal");
  const modalGrid = document.getElementById("imageModalGrid");
  const modalTitle = document.getElementById("imageModalTitle");
  const closeTargets = Array.from(document.querySelectorAll("[data-close-modal]"));

  const closeModal = () => {
    if (!modal) return;
    modal.classList.remove("active");
    modal.setAttribute("aria-hidden", "true");
    if (modalGrid) modalGrid.innerHTML = "";
  };

  closeTargets.forEach((btn) => {
    btn.addEventListener("click", closeModal);
  });

  const dayImages = Array.from(document.querySelectorAll(".day-images img"));
  if (dayImages.length && modal && modalGrid) {
    dayImages.forEach((img) => {
      img.addEventListener("click", () => {
        const dayNo = img.getAttribute("data-day") || "";
        const sameDayImages = dayImages.filter((item) => item.getAttribute("data-day") === dayNo);
        modalGrid.innerHTML = "";
        sameDayImages.forEach((item) => {
          const clone = document.createElement("img");
          clone.src = item.getAttribute("data-src") || item.src;
          clone.alt = item.alt || "Trip image";
          modalGrid.appendChild(clone);
        });
        if (modalTitle) {
          modalTitle.textContent = dayNo ? `Day ${dayNo} Images` : "Day Images";
        }
        modal.classList.add("active");
        modal.setAttribute("aria-hidden", "false");
      });
    });
  }
});
