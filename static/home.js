document.addEventListener("DOMContentLoaded", () => {
  const travelToggle = document.getElementById("travelToggle");
  const sectionTitle = document.getElementById("sectionTitle");
  const travelList = document.getElementById("travelList");

  if (!travelToggle || !travelList || !sectionTitle) {
    return;
  }

  travelToggle.addEventListener("click", () => {
    sectionTitle.classList.add("is-visible");
    travelList.classList.add("is-visible");
    sectionTitle.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  const swipeToggles = Array.from(document.querySelectorAll("[data-home-swipe]"));
  swipeToggles.forEach((swipeToggle) => {
    const operatorPanel = swipeToggle.closest(".itinerary-content")?.querySelector("[data-home-operator]");
    if (!operatorPanel) {
      return;
    }

    const setVisible = (isOpen) => {
      operatorPanel.style.display = isOpen ? "block" : "none";
      swipeToggle.classList.toggle("active", isOpen);
      swipeToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    };

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
        setVisible(!isOpen);
        return;
      }
      setVisible(delta > 0);
    };

    swipeToggle.addEventListener("mousedown", onPointerDown);
    swipeToggle.addEventListener("mousemove", onPointerMove);
    swipeToggle.addEventListener("mouseup", onPointerUp);
    swipeToggle.addEventListener("mouseleave", onPointerUp);
    swipeToggle.addEventListener("touchstart", onPointerDown, { passive: true });
    swipeToggle.addEventListener("touchmove", onPointerMove, { passive: true });
    swipeToggle.addEventListener("touchend", onPointerUp);
  });

  const sortSelect = document.getElementById("sortSelect");
  if (sortSelect) {
    const sortTrips = () => {
      const sortValue = sortSelect.value;
      const cards = Array.from(travelList.querySelectorAll(".itinerary-card"));

      const sorted = cards.slice();
      if (sortValue === "low-to-high") {
        sorted.sort((a, b) => Number(a.dataset.price || 0) - Number(b.dataset.price || 0));
      } else if (sortValue === "high-to-low") {
        sorted.sort((a, b) => Number(b.dataset.price || 0) - Number(a.dataset.price || 0));
      } else {
        sorted.sort((a, b) => Number(a.dataset.order || 0) - Number(b.dataset.order || 0));
      }

      sorted.forEach((card) => travelList.appendChild(card));
    };

    sortSelect.addEventListener("change", sortTrips);
  }
});
