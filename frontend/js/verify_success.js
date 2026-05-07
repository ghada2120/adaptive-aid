document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const status = params.get("status");

  const icon = document.getElementById("icon");
  const title = document.getElementById("title");
  const message = document.getElementById("message");

  if (status === "success") {
    icon.innerHTML = '<i class="fas fa-check-circle verify-success"></i>';
    title.textContent = "Email Verified";
    message.textContent = "Your email has been verified successfully. You can now log in.";
  } else {
    icon.innerHTML = '<i class="fas fa-times-circle verify-error"></i>';
    title.textContent = "Invalid or Expired Link";
    message.textContent = "This verification link is invalid or has already been used. Please register again or request a new verification email.";
  }
});