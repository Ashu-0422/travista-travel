document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("operatorEditForm");
  const errorMsg = document.getElementById("errorMsg");
  const pickupTimeText = document.getElementById("pickupTimeText");
  const pickupMeridiem = document.getElementById("pickupMeridiem");
  const pickupTimeValue = document.getElementById("pickupTimeValue");
  const travelDate = document.getElementById("traveldate");
  const travelDatee = document.getElementById("traveldatee");
  const journeyStartDate = document.getElementById("journeyStartDate");
  const sourceCity = document.getElementById("sourcee");
  const destinationCity = document.getElementById("destination");

  const isValidTwelveHour = (value) => /^(0?[1-9]|1[0-2]):[0-5][0-9]$/.test((value || "").trim());

  const bindAmPmTime = (timeTextInput, meridiemInput, hiddenField) => {
    if (!timeTextInput || !meridiemInput || !hiddenField) {
      return;
    }
    const syncValue = () => {
      const rawTime = (timeTextInput.value || "").trim();
      const meridiem = (meridiemInput.value || "AM").toUpperCase();
      if (!isValidTwelveHour(rawTime)) {
        hiddenField.value = "";
        return;
      }
      hiddenField.value = `${rawTime} ${meridiem}`;
    };
    timeTextInput.addEventListener("input", syncValue);
    meridiemInput.addEventListener("change", syncValue);
    syncValue();
  };

  bindAmPmTime(pickupTimeText, pickupMeridiem, pickupTimeValue);

  const tomorrow = new Date();
  tomorrow.setHours(0, 0, 0, 0);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split("T")[0];

  if (travelDate) {
    travelDate.min = tomorrowStr;
  }

  if (travelDatee) {
    travelDatee.min = tomorrowStr;
  }

  if (journeyStartDate) {
    journeyStartDate.min = tomorrowStr;
  }

  const dayCards = Array.from(document.querySelectorAll(".day-card"));
  dayCards.forEach((card) => {
    const timeText = card.querySelector(".day-time-text");
    const timeMeridiem = card.querySelector(".day-time-meridiem");
    const timeHidden = card.querySelector(".day-time-hidden");
    bindAmPmTime(timeText, timeMeridiem, timeHidden);

    const fileInput = card.querySelector("input[type='file']");
    const previewWrap = card.querySelector("[data-preview-for]");
    if (fileInput && previewWrap) {
      fileInput.addEventListener("change", function () {
        const files = Array.from(this.files || []);
        previewWrap.innerHTML = "";
        if (!files.length) {
          return;
        }
        const invalidFile = files.find((f) => !f.type.startsWith("image/"));
        if (invalidFile) {
          if (errorMsg) {
            errorMsg.textContent = "Please select a valid image file.";
            errorMsg.style.color = "red";
          }
          return;
        }
        files.forEach((file) => {
          const reader = new FileReader();
          reader.addEventListener("load", function () {
            const img = document.createElement("img");
            img.className = "day-image-preview";
            img.alt = "Image preview";
            img.src = this.result;
            previewWrap.appendChild(img);
          });
          reader.readAsDataURL(file);
        });
      });
    }
  });

  if (form) {
    form.addEventListener("submit", (e) => {
      if (!errorMsg) {
        return;
      }
      errorMsg.textContent = "";

      if (pickupTimeText && pickupMeridiem && pickupTimeValue) {
        if (!isValidTwelveHour((pickupTimeText.value || "").trim())) {
          e.preventDefault();
          errorMsg.textContent = "Pickup time should be in hh:mm format with AM/PM.";
          return;
        }
        pickupTimeValue.value = `${pickupTimeText.value.trim()} ${pickupMeridiem.value}`;
      }

      const hiddenDayTimes = Array.from(document.querySelectorAll(".day-time-hidden"));
      const hasInvalidDayTime = hiddenDayTimes.some((item) => !item.value);
      if (hasInvalidDayTime) {
        e.preventDefault();
        errorMsg.textContent = "Each day time should be in hh:mm format with AM/PM.";
        return;
      }

      if (sourceCity && destinationCity) {
        const source = (sourceCity.value || "").trim().toLowerCase();
        const destination = (destinationCity.value || "").trim().toLowerCase();
        if (source && destination && source === destination) {
          e.preventDefault();
          errorMsg.textContent = "Source and destination cannot be the same.";
          return;
        }
      }
    });
  }
});
