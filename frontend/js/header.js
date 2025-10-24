(async () => {
  /* === THEME bootstrap (global) === */
  // 1) activar clase en <body>
  document.body.classList.add("theme-warm");
const t = localStorage.getItem("sp_theme");   // "dark" | "light"
const g = localStorage.getItem("sp_grain");   // "on" | "off"
const m = localStorage.getItem("sp_motion");  // "on" | "reduced"
document.body.classList.toggle("theme-dark", t === "dark");
document.body.classList.toggle("no-grain", g === "off");
document.body.classList.toggle("reduce-motion", m === "reduced");

  // 2) prefijo relativo según si estoy en /html/
  const inHtmlDir = location.pathname.includes("/html/");
  const PREFIX = inHtmlDir ? ".." : ".";

  // 3) inyectar theme.css si no está linkeado aún
  const hasTheme = Array.from(document.styleSheets).some(s => (s.href || "").includes("/theme.css"));
  if (!hasTheme) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `${PREFIX}/theme.css?v=2`;
    document.head.appendChild(link);
  }

  // DEBUG rápido
  console.log("[header] theme class on body?", document.body.classList.contains("theme-warm"));
  console.log("[header] theme.css present?", hasTheme || "injected");
  /* === /THEME bootstrap === */

  // Montar header
  const mount = document.getElementById("site-header");
  if (!mount) return;

  const res = await fetch(`${PREFIX}/partials/header.html`);
  const html = await res.text();
  mount.innerHTML = html;

  // Asegurar clases para que el CSS las agarre
  mount.classList.add("topbar"); // fallback por si el partial no trae clase
  const first = mount.firstElementChild;
  if (first) first.classList.add("topbar-wrap"); // contenedor interno

  // Reescribir data-href -> href con prefijo
  mount.querySelectorAll("[data-href]").forEach(a => {
    const path = a.getAttribute("data-href");
    a.setAttribute("href", `${PREFIX}/${path}`);
  });

  // Marcar activo
  const here = location.pathname.replace(/\\/g, "/");
  mount.querySelectorAll("a[href]").forEach(a => {
    const href = a.getAttribute("href");
    if (here.endsWith(href) || (here.endsWith("/frontend/") && href.endsWith("/index.html"))) {
      a.classList.add("active");
    }
  });

  console.log("[header] mounted. classes:", mount.className, first && first.className);
})();
