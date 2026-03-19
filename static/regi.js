const stateCityMap = {
  "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati"],
  "Arunachal Pradesh": ["Itanagar", "Naharlagun"],
  "Assam": ["Guwahati", "Dibrugarh", "Silchar"],
  "Bihar": ["Patna", "Gaya", "Bhagalpur"],
  "Chhattisgarh": ["Raipur", "Bilaspur", "Bhilai"],
  "Goa": ["Panaji", "Margao", "Vasco da Gama"],
  "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
  "Haryana": ["Gurugram", "Faridabad", "Panipat"],
  "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala"],
  "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad"],
  "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi"],
  "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
  "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior"],
  "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Thane"],
  "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Puri"],
  "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"],
  "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota"],
  "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
  "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
  "Uttar Pradesh": ["Lucknow", "Noida", "Kanpur", "Agra"],
  "West Bengal": ["Kolkata", "Howrah", "Durgapur"]
};

const cityPincodePrefixes = {
  "Visakhapatnam": ["530"],
  "Vijayawada": ["520"],
  "Guntur": ["522"],
  "Tirupati": ["517"],
  "Itanagar": ["791"],
  "Naharlagun": ["791"],
  "Guwahati": ["781"],
  "Dibrugarh": ["786"],
  "Silchar": ["788"],
  "Patna": ["800", "801"],
  "Gaya": ["823"],
  "Bhagalpur": ["812", "813"],
  "Raipur": ["492"],
  "Bilaspur": ["495"],
  "Bhilai": ["490"],
  "Panaji": ["403"],
  "Margao": ["403"],
  "Vasco da Gama": ["403"],
  "Ahmedabad": ["380"],
  "Surat": ["395"],
  "Vadodara": ["390"],
  "Rajkot": ["360"],
  "Gurugram": ["122"],
  "Faridabad": ["121"],
  "Panipat": ["132"],
  "Shimla": ["171"],
  "Manali": ["175"],
  "Dharamshala": ["176"],
  "Ranchi": ["834"],
  "Jamshedpur": ["831"],
  "Dhanbad": ["826"],
  "Bengaluru": ["560"],
  "Mysuru": ["570"],
  "Mangaluru": ["575"],
  "Hubballi": ["580"],
  "Kochi": ["682"],
  "Thiruvananthapuram": ["695"],
  "Kozhikode": ["673"],
  "Bhopal": ["462"],
  "Indore": ["452"],
  "Gwalior": ["474"],
  "Mumbai": ["400", "401"],
  "Pune": ["411", "412"],
  "Nagpur": ["440"],
  "Nashik": ["422"],
  "Thane": ["400", "401"],
  "Bhubaneswar": ["751"],
  "Cuttack": ["753"],
  "Rourkela": ["769"],
  "Puri": ["752"],
  "Ludhiana": ["141"],
  "Amritsar": ["143"],
  "Jalandhar": ["144"],
  "Jaipur": ["302"],
  "Jodhpur": ["342"],
  "Udaipur": ["313"],
  "Kota": ["324"],
  "Chennai": ["600"],
  "Coimbatore": ["641"],
  "Madurai": ["625"],
  "Salem": ["636"],
  "Hyderabad": ["500"],
  "Warangal": ["506"],
  "Nizamabad": ["503"],
  "Lucknow": ["226"],
  "Noida": ["201"],
  "Kanpur": ["208"],
  "Agra": ["282"],
  "Kolkata": ["700"],
  "Howrah": ["711"],
  "Durgapur": ["713"]
};

function normalizePincode(value) {
  return (value || "").replace(/\D/g, "").trim();
}

function validateCityPincode() {
  const city = document.getElementById("city").value;
  const pincodeInput = document.querySelector('input[name="pincode"]');
  const rawPincode = pincodeInput.value;
  const pincode = normalizePincode(rawPincode);
  const validPrefixes = cityPincodePrefixes[city] || [];

  if (!pincode) {
    pincodeInput.setCustomValidity("");
    return true;
  }

  if (pincode.length !== 6) {
    pincodeInput.setCustomValidity("Pincode must be exactly 6 digits.");
    return false;
  }

  if (!validPrefixes.length) {
    pincodeInput.setCustomValidity("");
    return true;
  }

  const isValidForCity = validPrefixes.some((prefix) => pincode.startsWith(prefix));
  if (!isValidForCity) {
    pincodeInput.setCustomValidity("Invalid pincode. City and pincode must match.");
    return false;
  }

  pincodeInput.setCustomValidity("");
  return true;
}

// Load states when page loads
window.onload = function () {
  const stateSelect = document.getElementById("state");
  const citySelect = document.getElementById("city");
  const pincodeInput = document.querySelector('input[name="pincode"]');
  const passwordInput = document.getElementById("password");
  const confirmPasswordInput = document.getElementById("confirm_password");
  const form = document.querySelector(".register-form");
  const selectedState = stateSelect.dataset.selected || "";
  const selectedCity = citySelect.dataset.selected || "";

  for (let state in stateCityMap) {
    let option = document.createElement("option");
    option.value = state;
    option.textContent = state;
    stateSelect.appendChild(option);
  }

  if (selectedState && stateCityMap[selectedState]) {
    stateSelect.value = selectedState;
    loadCities(selectedCity);
  }

  function validatePasswordMatch() {
    if (passwordInput.value !== confirmPasswordInput.value) {
      confirmPasswordInput.setCustomValidity("Passwords do not match.");
      return false;
    }
    confirmPasswordInput.setCustomValidity("");
    return true;
  }

  citySelect.addEventListener("change", validateCityPincode);
  pincodeInput.addEventListener("input", validateCityPincode);
  confirmPasswordInput.addEventListener("input", validatePasswordMatch);
  passwordInput.addEventListener("input", validatePasswordMatch);
  form.addEventListener("submit", function (event) {
    const isCityPincodeValid = validateCityPincode();
    const isPasswordValid = validatePasswordMatch();

    if (!isCityPincodeValid || !isPasswordValid) {
      event.preventDefault();
      if (!isPasswordValid) {
        confirmPasswordInput.reportValidity();
        return;
      }
      pincodeInput.reportValidity();
    }
  });
};

function loadCities(selectedCity = "") {
  const stateSelect = document.getElementById("state");
  const citySelect = document.getElementById("city");

  citySelect.innerHTML = '<option value="">Select City</option>';

  const selectedState = stateSelect.value;
  if (!selectedState) return;

  stateCityMap[selectedState].forEach(city => {
    let option = document.createElement("option");
    option.value = city;
    option.textContent = city;
    if (selectedCity && selectedCity === city) {
      option.selected = true;
    }
    citySelect.appendChild(option);
  });
  validateCityPincode();
}

function showPopup() {
    document.getElementById("welcomePopup").style.display = "flex";
}

function closePopup() {
    document.getElementById("welcomePopup").style.display = "none";
}


function togglePassword() {
    const password = document.getElementById("password");
    const toggle = document.querySelector('.password-box button[onclick="togglePassword()"]');

    if (password.type === "password") {
        password.type = "text";
        if (toggle) toggle.textContent = "Hide";
    } else {
        password.type = "password";
        if (toggle) toggle.textContent = "Show";
    }
}

function toggleConfirmPassword() {
    const confirmPassword = document.getElementById("confirm_password");
    const toggle = document.querySelector('.password-box button[onclick="toggleConfirmPassword()"]');

    if (confirmPassword.type === "password") {
        confirmPassword.type = "text";
        if (toggle) toggle.textContent = "Hide";
    } else {
        confirmPassword.type = "password";
        if (toggle) toggle.textContent = "Show";
    }
}
