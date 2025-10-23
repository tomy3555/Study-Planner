(async () => {
  const mount = document.getElementById("site-header");
  if (!mount) return;

  // si la ruta contiene /html/ estamos en subcarpeta
  const inHtmlDir = location.pathname.includes("/html/");
  const PREFIX = inHtmlDir ? ".." : ".";

  // cargar el partial con ruta relativa al archivo actual
  const res = await fetch(`${PREFIX}/partials/header.html`);
  mount.innerHTML = await res.text();

  // reescribir data-href -> href con prefijo correcto
  mount.querySelectorAll("[data-href]").forEach(a => {
    const path = a.getAttribute("data-href");
    a.setAttribute("href", `${PREFIX}/${path}`);
  });

  // marcar activo
  const here = location.pathname.replace(/\\/g, "/");
  mount.querySelectorAll("a[href]").forEach(a => {
    const href = a.getAttribute("href");
    // marca activo si termina igual o si coincide exacto con index
    if (here.endsWith(href) || (here.endsWith("/frontend/") && href.endsWith("/index.html"))) {
      a.classList.add("active");
    }
  });
})();
