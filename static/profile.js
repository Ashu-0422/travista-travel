document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(
    ".meta-grid article, .stat-card, .row, .insight-card, .trend-card, .coverage-card, .recommend-card, .longest-card"
  );
  cards.forEach((card, index) => {
    card.classList.add("reveal");
    card.style.animationDelay = `${index * 60}ms`;
  });
});
