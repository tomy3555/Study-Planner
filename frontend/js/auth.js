const apiBase = "http://localhost:8000";

// Helper para mostrar mensajes
function showMsg(msg, ok = false) {
  const el = document.getElementById("form-msg");
  if (!el) return;
  el.textContent = msg;
  el.classList.toggle("ok", ok);
}

// ===== REGISTRO =====
const form = document.querySelector("form");
if (form && document.querySelector("h2")?.textContent.includes("Registrarse")) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const [nombre, email, pass1, pass2] = form.querySelectorAll("input");

    if (!nombre.value.trim() || !email.value.trim() || !pass1.value.trim() || !pass2.value.trim()) {
      return showMsg("Todos los campos son obligatorios.");
    }
    if (pass1.value !== pass2.value) {
      return showMsg("Las contraseñas no coinciden.");
    }

    try {
      const res = await fetch(`${apiBase}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: nombre.value.trim(),
          email: email.value.trim(),
          password: pass1.value,
        }),
      });
      const data = await res.json();

      if (!res.ok) {
        return showMsg(data.error?.includes("email") ? "Ese email ya está en uso." : "Error al registrarse.");
      }

      // login automático tras registrarse
      const loginRes = await fetch(`${apiBase}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.value.trim(), password: pass1.value }),
      });
      const loginData = await loginRes.json();
      if (!loginRes.ok) return showMsg("Error al iniciar sesión automáticamente.");

      // guardar token y nombre
      localStorage.setItem("access_token", loginData.accessToken);
      localStorage.setItem("user_name", loginData.user?.name || "Usuario");

      showMsg("Registro exitoso ✅ Redirigiendo...", true);
      setTimeout(() => (window.location.href = "../index.html"), 1000);
    } catch (err) {
      console.error(err);
      showMsg("Error de conexión con el servidor.");
    }
  });
}

// ===== LOGIN =====
if (form && document.querySelector("h2")?.textContent.includes("Iniciar")) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const [email, password] = form.querySelectorAll("input");

    if (!email.value.trim() || !password.value.trim()) {
      return showMsg("Completá ambos campos.");
    }

    try {
      const res = await fetch(`${apiBase}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.value.trim(), password: password.value }),
      });
      const data = await res.json();

      if (!res.ok) return showMsg("Email o contraseña incorrectos.");

      localStorage.setItem("access_token", data.accessToken);
      // opcionalmente podés hacer una consulta al backend para traer el nombre
      localStorage.setItem("user_name", data.user?.name || "Usuario");

      showMsg("Inicio de sesión correcto ✅", true);
      setTimeout(() => (window.location.href = "../index.html"), 1000);
    } catch (err) {
      console.error(err);
      showMsg("Error conectando con el servidor.");
    }
  });
}
