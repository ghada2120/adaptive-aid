const API_BASE_URL = "http://127.0.0.1:8000";

const params = new URLSearchParams(window.location.search);
const token = params.get("token");
const passwordInput = document.getElementById("password");
const ruleLength = document.getElementById("rule-length");
const ruleUppercase = document.getElementById("rule-uppercase");
const ruleLowercase = document.getElementById("rule-lowercase");
const ruleNumber = document.getElementById("rule-number");

function updatePasswordRules(password) {
  ruleLength.className = password.length >= 8 ? "valid" : "invalid";
  ruleUppercase.className = /[A-Z]/.test(password) ? "valid" : "invalid";
  ruleLowercase.className = /[a-z]/.test(password) ? "valid" : "invalid";
  ruleNumber.className = /[0-9]/.test(password) ? "valid" : "invalid";
}

function validatePassword(password) {
  if (password.length < 8) return "Password must be at least 8 characters long.";
  if (!/[A-Z]/.test(password)) return "Password must contain at least one uppercase letter.";
  if (!/[a-z]/.test(password)) return "Password must contain at least one lowercase letter.";
  if (!/[0-9]/.test(password)) return "Password must contain at least one number.";
  return null;
}

if (passwordInput) {
  passwordInput.addEventListener("input", () => {
    updatePasswordRules(passwordInput.value);
  });
}
document.getElementById("resetBtn").addEventListener("click", async () => {
  const password = document.getElementById("password").value;
  const msg = document.getElementById("msg");

  const passwordError = validatePassword(password);

if (passwordError) {
  msg.className = "message error";
  msg.textContent = passwordError;
  return;
}

  try {
    const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        token: token,
        new_password: password
      })
    });

    const data = await res.json();

    if (!res.ok) {
      msg.className = "message error";
      msg.textContent = data.detail;
      return;
    }

    msg.className = "message success";
    msg.textContent = "Password reset successful. Redirecting...";

    setTimeout(() => {
      window.location.href = "login.html";
    }, 1500);

  } catch (err) {
    msg.className = "message error";
    msg.textContent = "Server error";
  }
});