
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("operatorForm");
  const errorMsg = document.getElementById("errorMsg");
  const priceinput = document.getElementById("price");
  const coverImageInput = document.getElementById("coverImageInput");
  const previewCoverImage = document.getElementById("previewCoverImage");
  const hotelImageInput = document.getElementById("hotelImageInput");
  const previewHotelImage = document.getElementById("previewHotelImage");
  const placeImageInput = document.getElementById("placeImageInput");
  const previewPlaceImage = document.getElementById("previewPlaceImage");
  const travelDate = document.getElementById("traveldate");
  const travelDatee = document.getElementById("traveldatee");
  const journeyStartDate = document.getElementById("journeyStartDate");
  const tripDays = document.getElementById("tripDays");
  const dayDetails = document.getElementById("dayDetails");
  const sourceCity = document.getElementById("sourcee");
  const destinationCity = document.getElementById("destination");
  const pickupTimeText = document.getElementById("pickupTimeText");
  const pickupMeridiem = document.getElementById("pickupMeridiem");
  const pickupTimeValue = document.getElementById("pickupTimeValue");

  const isValidTwelveHour = (value) => /^(0?[1-9]|1[0-2]):[0-5][0-9]$/.test((value || "").trim());
  const bindAmPmTime = (timeTextInput, meridiemInput, hiddenField) => {
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

  const updateTripDays = () => {
    if (!travelDate || !travelDatee || !tripDays) {
      return;
    }

    if (!travelDate.value || !travelDatee.value) {
      tripDays.value = "";
      if (dayDetails) {
        dayDetails.innerHTML = "";
      }
      return;
    }

    const start = new Date(travelDate.value);
    const end = new Date(travelDatee.value);
    start.setHours(0, 0, 0, 0);
    end.setHours(0, 0, 0, 0);

    if (end < start) {
      tripDays.value = "";
      if (errorMsg) {
        errorMsg.textContent = "Destination date must be on or after source date.";
        errorMsg.style.color = "red";
      }
      return;
    }

    if (errorMsg && errorMsg.textContent.includes("Destination date")) {
      errorMsg.textContent = "";
    }

    const diffMs = end.getTime() - start.getTime();
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1;
    tripDays.value = String(days);
    renderDayDetails(days, start);
  };

  const renderDayDetails = (days, startDate) => {
    if (!dayDetails) {
      return;
    }
    dayDetails.innerHTML = "";
    if (!days || days <= 0) {
      return;
    }

    for (let i = 0; i < days; i += 1) {
      const dayDate = new Date(startDate);
      dayDate.setDate(startDate.getDate() + i);
      const dateValue = dayDate.toISOString().split("T")[0];

      const card = document.createElement("div");
      card.className = "day-card";

      const title = document.createElement("h4");
      title.textContent = `Day ${i + 1} - ${dateValue}`;
      card.appendChild(title);

      const dateRow = document.createElement("div");
      dateRow.className = "row";
      const dateLabel = document.createElement("label");
      dateLabel.textContent = "Date";
      const dateInput = document.createElement("input");
      dateInput.type = "date";
      dateInput.name = `day_${i + 1}_date`;
      dateInput.value = dateValue;
      dateInput.readOnly = true;
      dateRow.appendChild(dateLabel);
      dateRow.appendChild(dateInput);
      card.appendChild(dateRow);

      const placeRow = document.createElement("div");
      placeRow.className = "row";
      const placeLabel = document.createElement("label");
      placeLabel.textContent = "Place / Location";
      const placeInput = document.createElement("input");
      placeInput.type = "textarea";
      placeInput.name = `day_${i + 1}_place`;
      placeInput.placeholder = "Example: City tour / Museum";
      placeInput.required = true;
      placeRow.appendChild(placeLabel);
      placeRow.appendChild(placeInput);
      card.appendChild(placeRow);

      const timeRow = document.createElement("div");
      timeRow.className = "row";
      const timeLabel = document.createElement("label");
      timeLabel.textContent = "Time";
      const timeInput = document.createElement("input");
      timeInput.type = "textarea";
      timeInput.placeholder = "hh:mm";
      timeInput.pattern = "^(0?[1-9]|1[0-2]):[0-5][0-9]$";
      timeInput.title = "Use 12-hour time format like 09:30";
      timeInput.required = true;
      const meridiemSelect = document.createElement("select");
      meridiemSelect.required = true;
      meridiemSelect.innerHTML = '<option value="AM">AM</option><option value="PM">PM</option>';
      const timeHidden = document.createElement("input");
      timeHidden.type = "hidden";
      timeHidden.name = `day_${i + 1}_time`;
      timeHidden.setAttribute("data-ampm-hidden", "1");
      bindAmPmTime(timeInput, meridiemSelect, timeHidden);
      timeRow.appendChild(timeLabel);
      timeRow.appendChild(timeInput);
      timeRow.appendChild(meridiemSelect);
      timeRow.appendChild(timeHidden);
      card.appendChild(timeRow);

      const planRow = document.createElement("div");
      planRow.className = "row";
      const planLabel = document.createElement("label");
      planLabel.textContent = "Plan / Details";
      const planInput = document.createElement("textarea");
      planInput.name = `day_${i + 1}_plan`;
      planInput.rows = 2;
      planInput.placeholder = "Short plan for the day";
      planInput.required = true;
      planRow.appendChild(planLabel);
      planRow.appendChild(planInput);
      card.appendChild(planRow);

      const imageRow = document.createElement("div");
      imageRow.className = "row";
      const imageLabel = document.createElement("label");
      imageLabel.textContent = "Place Image";
      const imageInput = document.createElement("input");
      imageInput.type = "file";
      imageInput.name = `day_${i + 1}_image`;
      imageInput.accept = "image/*";
      imageInput.multiple = true;
      imageInput.required = true;
      const imagePreviewWrap = document.createElement("div");
      imagePreviewWrap.className = "preview-grid";

      imageInput.addEventListener("change", function () {
        const files = Array.from(this.files || []);
        imagePreviewWrap.innerHTML = "";
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
            img.alt = `Day ${i + 1} place image preview`;
            img.src = this.result;
            imagePreviewWrap.appendChild(img);
          });
          reader.readAsDataURL(file);
        });
      });
      imageRow.appendChild(imageLabel);
      imageRow.appendChild(imageInput);
      imageRow.appendChild(imagePreviewWrap);
      card.appendChild(imageRow);

      dayDetails.appendChild(card);
    }
  };

  if (travelDate) {
    travelDate.addEventListener("change", () => {
      if (travelDatee && travelDate.value) {
        travelDatee.min = travelDate.value;
      }
      if (journeyStartDate) {
        journeyStartDate.value = travelDate.value || "";
      }
      updateTripDays();
    });
  }

  if (travelDate && journeyStartDate && travelDate.value) {
    journeyStartDate.value = travelDate.value;
  }

  if (travelDatee) {
    travelDatee.addEventListener("change", updateTripDays);
  }

  if (form) {
    const validateRouteCities = () => {
      if (!sourceCity || !destinationCity) {
        return true;
      }
      const source = (sourceCity.value || "").trim().toLowerCase();
      const destination = (destinationCity.value || "").trim().toLowerCase();
      if (source && destination && source === destination) {
        if (errorMsg) {
          errorMsg.textContent = "Source and destination cannot be the same.";
          errorMsg.style.color = "red";
        }
        return false;
      }
      return true;
    };

    if (sourceCity && destinationCity) {
      sourceCity.addEventListener("change", validateRouteCities);
      destinationCity.addEventListener("change", validateRouteCities);
    }

    form.addEventListener("submit", function (e) {
      if (!errorMsg || !priceinput) {
        return;
      }

      // reset error
      errorMsg.textContent = "";
      errorMsg.style.color = "red";

      if (pickupTimeText && pickupMeridiem && pickupTimeValue) {
        if (!isValidTwelveHour((pickupTimeText.value || "").trim())) {
          e.preventDefault();
          errorMsg.textContent = "Pickup time should be in hh:mm format with AM/PM.";
          return;
        }
        pickupTimeValue.value = `${pickupTimeText.value.trim()} ${pickupMeridiem.value}`;
      }

      const hiddenDayTimes = Array.from(form.querySelectorAll("input[data-ampm-hidden='1']"));
      const hasInvalidDayTime = hiddenDayTimes.some((item) => !item.value);
      if (hasInvalidDayTime) {
        e.preventDefault();
        errorMsg.textContent = "Each day time should be in hh:mm format with AM/PM.";
        return;
      }

      const priceValue = Number(priceinput.value);
      if (!priceinput.value || Number.isNaN(priceValue) || priceValue <= 0) {
        e.preventDefault();
        errorMsg.textContent = "Price should be greater than 0";
        return;
      }
      if (!validateRouteCities()) {
        e.preventDefault();
        return;
      }

      alert("Trip details submitted successfully!");
    });
  }

  if (pickupTimeText && pickupMeridiem && pickupTimeValue) {
    bindAmPmTime(pickupTimeText, pickupMeridiem, pickupTimeValue);
  }

  const bindMultiPreview = (inputEl, previewWrap) => {
    if (!inputEl || !previewWrap) return;
    inputEl.multiple = true;
    inputEl.addEventListener("change", function () {
      const files = Array.from(this.files || []);
      previewWrap.innerHTML = "";
      if (!files.length) return;

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
  };

  bindMultiPreview(coverImageInput, previewCoverImage);
  bindMultiPreview(hotelImageInput, previewHotelImage);
  bindMultiPreview(placeImageInput, previewPlaceImage);
});
