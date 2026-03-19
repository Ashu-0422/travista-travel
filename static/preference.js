const slider = document.getElementById("rating");
const ratingValue = document.getElementById("ratingValue");
const daysInput = document.getElementById("days");
const budgetInput = document.getElementById("budget");
const errorMsg = document.getElementById("errorMsg");
const form = document.querySelector(".preference-form");
const peopleInput = document.getElementById("people");
const sourceInput = document.getElementById("source");
const destinationInput = document.getElementById("destination");

document.addEventListener("DOMContentLoaded", () => {
  const dateInput = document.getElementById("traveldate");
  if (!dateInput) {
    return;
  }
  const tomorrow = new Date();
  tomorrow.setHours(0, 0, 0, 0);
  tomorrow.setDate(tomorrow.getDate() + 1);
  dateInput.min = tomorrow.toISOString().split("T")[0];
});

if (slider && ratingValue) {
  slider.addEventListener("input", () => {
    ratingValue.textContent = slider.value;
  });
}

if (form) {
  form.addEventListener("submit", (e) => {
    errorMsg.textContent = "";
    errorMsg.style.color = "red";

    if (daysInput.value && Number(daysInput.value) <= 0) {
      e.preventDefault();
      errorMsg.textContent = "Number of days must be positive";
      return;
    }

    if (peopleInput.value && Number(peopleInput.value) <= 0) {
      e.preventDefault();
      errorMsg.textContent = "Number of people must be greater than 0";
      return;
    }

    if (budgetInput.value && Number(budgetInput.value) < 2000) {
      e.preventDefault();
      errorMsg.textContent = "Minimum budget should be 2000";
      return;
    }

    const source = (sourceInput.value || "").trim().toLowerCase();
    const destination = (destinationInput.value || "").trim().toLowerCase();
    if (source && destination && source === destination) {
      e.preventDefault();
      errorMsg.textContent = "Source and destination cannot be same.";
    }
  });
}
