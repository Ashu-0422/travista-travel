const form = document.getElementsByClassName("login-form")[0];
const username = document.getElementById("username");
const password = document.getElementById("password");
const errorMsg = document.getElementById("errorMsg");

form.addEventListener("submit", function (e) {
  e.preventDefault();

  errorMsg.textContent = "";

  if (username.value.trim() === "") {
    errorMsg.textContent = "Username is required";
    return;
  }

  if (password.value.trim() === "") {
    errorMsg.textContent = "Password is required";
    return;
  }
 
    // ✅ ALL GOOD → redirect
  form.submit();

});

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

