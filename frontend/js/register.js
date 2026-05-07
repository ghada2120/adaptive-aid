const API_BASE_URL = "http://127.0.0.1:8000";
const REGISTER_ENDPOINT = `${API_BASE_URL}/auth/register`;

document.addEventListener("DOMContentLoaded", () => {
  const registerForm = document.getElementById("registerForm");
  const registerMessage = document.getElementById("registerMessage");
  const registerBtn = document.getElementById("registerBtn");

  const passwordInput = document.getElementById("password");
  const ruleLength = document.getElementById("rule-length");
  const ruleUppercase = document.getElementById("rule-uppercase");
  const ruleLowercase = document.getElementById("rule-lowercase");
  const ruleNumber = document.getElementById("rule-number");

  function showMessage(text, type = "error") {
  registerMessage.className = "message";

  void registerMessage.offsetWidth; // forces the message to re-animate

  registerMessage.textContent = text;
  registerMessage.className = `message ${type} flash`;
}

  function clearMessage() {
    registerMessage.textContent = "";
    registerMessage.className = "message";
  }

  function setButtonLoading(isLoading) {
    if (isLoading) {
      registerBtn.disabled = true;
      registerBtn.classList.add("loading");
      registerBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Registering...`;
    } else {
      registerBtn.disabled = false;
      registerBtn.classList.remove("loading");
      registerBtn.innerHTML = `<i class="fas fa-user-check"></i> Register`;
    }
  }

  function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function updatePasswordRules(password) {
    ruleLength.className = password.length >= 8 ? "valid" : "invalid";
    ruleUppercase.className = /[A-Z]/.test(password) ? "valid" : "invalid";
    ruleLowercase.className = /[a-z]/.test(password) ? "valid" : "invalid";
    ruleNumber.className = /[0-9]/.test(password) ? "valid" : "invalid";
  }

  function validatePassword(password, name, email) {
  const commonPasswords = [
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "admin123"
  ];

  const passwordLower = password.toLowerCase();
  const nameLower = name.toLowerCase();
  const emailName = email.split("@")[0].toLowerCase();

  if (commonPasswords.includes(passwordLower)) {
    return "Password is too common.";
  }

  if (password.length < 8) {
    return "Password must be at least 8 characters long.";
  }

  if (password.length > 64) {
    return "Password must not be longer than 64 characters.";
  }

  if (emailName && passwordLower.includes(emailName)) {
    return "Password cannot contain your email name.";
  }

  if (nameLower && passwordLower.includes(nameLower)) {
    return "Password cannot contain your name.";
  }

  if (!/[A-Z]/.test(password)) {
    return "Password must contain at least one uppercase letter.";
  }

  if (!/[a-z]/.test(password)) {
    return "Password must contain at least one lowercase letter.";
  }

  if (!/[0-9]/.test(password)) {
    return "Password must contain at least one number.";
  }

  return null;
}

  if (passwordInput) {
    passwordInput.addEventListener("input", () => {
      updatePasswordRules(passwordInput.value);
    });
  }

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearMessage();

    const name = document.getElementById("name")?.value.trim();
    const email = document.getElementById("email")?.value.trim();
    const password = document.getElementById("password")?.value;

    if (!name || !email || !password) {
      showMessage("Please fill in all fields.");
      return;
    }

    if (!validateEmail(email)) {
      showMessage("Please enter a valid email address.");
      return;
    }

    const passwordError = validatePassword(password, name, email);
    if (passwordError) {
      showMessage(passwordError);
      return;
    }

    setButtonLoading(true);

    try {
      const response = await fetch(REGISTER_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: name,
          email: email,
          password: password
        })
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        showMessage(data.detail || data.message || "Registration failed.");
        return;
      }

      if (data.verification_link) {
      showMessage(
        "Registration successful, but the verification email could not be sent. Please use the verification link shown below.",
        "success"
      );

      registerMessage.innerHTML = `
        Registration successful, but the verification email could not be sent.<br><br>
        Please verify your email using this link:<br>
        <a href="${data.verification_link}" target="_blank">Verify Email</a>
        `;

        return;
}

showMessage(
  data.message || "Account created. Please verify your email before logging in.",
  "success"
);

if (data.verification_link) {
  registerMessage.innerHTML = `
    Account created, but the verification email could not be sent.<br><br>
    Please verify your email using this link:<br>
    <a href="${data.verification_link}" target="_blank">Verify Email</a>
    <br><br>
    After verifying, you can <a href="login.html">go to login</a>.
  `;
} else {
  registerMessage.innerHTML = `
    Account created successfully.<br>
    Please check your email and verify your account before logging in.<br><br>
    <a href="login.html">Go to Login</a>
  `;
}



    } catch (error) {
      console.error("Registration error:", error);
      showMessage("Could not connect to the server.");
    } finally {
      setButtonLoading(false);
    }
  });
});