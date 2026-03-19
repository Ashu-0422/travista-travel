document.addEventListener("DOMContentLoaded", () => {
  const successModal = document.getElementById("bookingSuccessModal");
  const successOk = document.getElementById("bookingSuccessOk");
  const form = document.getElementById("bookingForm");
  const travelersInput = document.getElementById("travelers");
  const totalTravelers = document.getElementById("totalTravelers");
  const totalAmount = document.getElementById("totalAmount");
  const pricePerTraveler = document.getElementById("pricePerTraveler");
  const paymentMode = document.getElementById("paymentMode");
  const upiFields = document.getElementById("upiFields");
  const cardFields = document.getElementById("cardFields");
  const netBankingFields = document.getElementById("netBankingFields");

  if (successModal && successOk) {
    successOk.addEventListener("click", () => {
      successModal.remove();
    });
  }

  if (!form || !travelersInput || !totalTravelers || !totalAmount || !pricePerTraveler || !paymentMode) {
    return;
  }

  const unitPrice = Number(form.dataset.price || "0");
  const maxTravelers = 12;

  const fieldsByMode = {
    UPI: [
      document.getElementById("upiApp"),
      document.getElementById("upiId"),
    ],
    Card: [
      document.getElementById("cardHolder"),
      document.getElementById("cardNumber"),
      document.getElementById("cardExpiry"),
      document.getElementById("cardCvv"),
    ],
    "Net Banking": [
      document.getElementById("bankName"),
      document.getElementById("accountNumber"),
      document.getElementById("ifscCode"),
    ],
  };

  const formatInr = (amount) => `\u20b9${amount.toFixed(2)}`;
  const onlyDigits = (value) => String(value || "").replace(/\D/g, "");

  const showError = (message) => {
    let errorBox = form.querySelector(".form-error");
    if (!errorBox) {
      errorBox = document.createElement("div");
      errorBox.className = "form-error";
      form.insertBefore(errorBox, form.children[1]);
    }
    errorBox.textContent = message;
  };

  const clearError = () => {
    const errorBox = form.querySelector(".form-error");
    if (errorBox) {
      errorBox.remove();
    }
  };

  const refreshFare = () => {
    const travelers = Math.min(maxTravelers, Math.max(1, Number(travelersInput.value || "1")));
    travelersInput.value = String(travelers);
    totalTravelers.textContent = String(travelers);
    pricePerTraveler.textContent = formatInr(unitPrice);
    totalAmount.textContent = formatInr(unitPrice * travelers);
  };

  const togglePaymentFields = () => {
    const mode = paymentMode.value;
    upiFields.hidden = mode !== "UPI";
    cardFields.hidden = mode !== "Card";
    netBankingFields.hidden = mode !== "Net Banking";

    Object.entries(fieldsByMode).forEach(([fieldMode, fields]) => {
      fields.forEach((field) => {
        if (!field) {
          return;
        }
        field.required = fieldMode === mode;
      });
    });
  };

  const validatePayment = () => {
    const mode = paymentMode.value;
    if (!mode) {
      return "Select a payment method.";
    }

    if (mode === "UPI") {
      const upiApp = document.getElementById("upiApp").value.trim();
      const upiId = document.getElementById("upiId").value.trim();
      if (!upiApp) {
        return "Select a UPI app.";
      }
      if (!/^[A-Za-z0-9.\-_]{2,}@[A-Za-z]{2,}$/.test(upiId)) {
        return "Enter a valid UPI ID.";
      }
    }

    if (mode === "Card") {
      const cardHolder = document.getElementById("cardHolder").value.trim();
      const cardNumber = onlyDigits(document.getElementById("cardNumber").value);
      const cardExpiry = document.getElementById("cardExpiry").value.trim();
      const cardCvv = onlyDigits(document.getElementById("cardCvv").value);

      if (cardHolder.length < 3) {
        return "Enter the card holder name.";
      }
      if (cardNumber.length !== 16) {
        return "Enter a valid 16-digit card number.";
      }
      if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(cardExpiry)) {
        return "Enter card expiry in MM/YY format.";
      }
      if (cardCvv.length !== 3) {
        return "Enter a valid 3-digit CVV.";
      }
    }

    if (mode === "Net Banking") {
      const bankName = document.getElementById("bankName").value.trim();
      const accountNumber = onlyDigits(document.getElementById("accountNumber").value);
      const ifscCode = document.getElementById("ifscCode").value.trim().toUpperCase();

      if (!bankName) {
        return "Select a bank for net banking.";
      }
      if (accountNumber.length < 9 || accountNumber.length > 18) {
        return "Enter a valid account number.";
      }
      if (!/^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifscCode)) {
        return "Enter a valid IFSC code.";
      }
    }

    return "";
  };

  travelersInput.addEventListener("input", refreshFare);
  paymentMode.addEventListener("change", () => {
    clearError();
    togglePaymentFields();
  });

  form.addEventListener("submit", (event) => {
    clearError();
    refreshFare();

    if (Number(travelersInput.value || "1") > maxTravelers) {
      event.preventDefault();
      showError("One account can book a maximum of 12 travellers only.");
      return;
    }

    const paymentError = validatePayment();
    if (paymentError) {
      event.preventDefault();
      showError(paymentError);
    }
  });

  refreshFare();
  togglePaymentFields();
});
