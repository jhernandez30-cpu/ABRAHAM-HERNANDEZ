(function () {
  "use strict";

  const body = document.body;
  if (!body || !body.classList.contains("jah-preview-surface")) return;

  const addExternalAttrs = () => {
    document.querySelectorAll('a[href^="http"]').forEach((link) => {
      link.target = "_blank";
      const rel = new Set((link.getAttribute("rel") || "").split(/\s+/).filter(Boolean));
      rel.add("noopener");
      rel.add("noreferrer");
      link.setAttribute("rel", Array.from(rel).join(" "));
    });
  };

  const addReveal = () => {
    const targets = document.querySelectorAll(
      ".page-hero, .page-section, .section, .seo-card, .service-card, .faq-card, .project-card, .resource-card, .feature-card, .product-card, .category-card, .testimonial, .info-card, .form-card, .hero-panel, .cta-band"
    );

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      targets.forEach((item) => item.classList.add("jah-visible"));
      return;
    }

    targets.forEach((item) => item.classList.add("jah-reveal"));

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("jah-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.08 }
    );

    targets.forEach((item) => observer.observe(item));
  };

  const addLegalShell = () => {
    const content = document.getElementById("contet-container");
    if (!content || document.querySelector(".navbar")) return;

    const isNested = window.location.pathname.includes("/preview-2025/de/");
    const base = isNested ? "../../" : "../";

    const header = document.createElement("header");
    header.innerHTML = `
      <nav class="navbar" id="navbar" aria-label="Navegacion legal">
        <div class="logo">
          <a href="${base}index.html" class="brand-logo" aria-label="Inicio - Abraham Hernandez">
            <img src="${base}assets/jah-logo.png" alt="Logo JAH de Abraham Hernandez" width="180" height="120" loading="eager" decoding="async">
          </a>
        </div>
        <div class="nav-links">
          <a href="${base}index.html" class="nav-link">Inicio</a>
          <a href="${base}index.html#servicios" class="nav-link">Servicios</a>
          <a href="${base}index.html#proyectos" class="nav-link">Proyectos</a>
          <a href="${base}index.html#recursos" class="nav-link">Recursos</a>
          <a href="${base}index.html#contacto" class="nav-link">Contacto</a>
        </div>
      </nav>
    `;
    body.insertBefore(header, body.firstChild);

    const footer = document.createElement("footer");
    footer.innerHTML = `
      <div class="footer-logo">
        <img src="${base}assets/jah-logo.png" alt="Logo JAH de Abraham Hernandez" width="180" height="120" loading="lazy" decoding="async">
      </div>
      <div class="site-footer-links">
        <a href="${base}index.html#servicios">Servicios</a>
        <a href="${base}index.html#proyectos">Proyectos</a>
        <a href="${base}index.html#recursos">Recursos</a>
        <a href="${base}index.html#contacto">Contacto</a>
      </div>
      <p>© 2026 Abraham Hernandez - Todos los derechos reservados</p>
    `;
    body.appendChild(footer);
  };

  const syncBrandFallbacks = () => {
    document.querySelectorAll(".footer-brand .logo-text").forEach((logo) => {
      if (logo.querySelector("img")) return;
      const image = document.createElement("img");
      image.src = "../assets/jah-logo.png";
      image.alt = "Logo JAH";
      image.width = 180;
      image.height = 120;
      image.loading = "lazy";
      image.decoding = "async";
      logo.replaceChildren(image);
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    addExternalAttrs();
    addLegalShell();
    syncBrandFallbacks();
    addReveal();
    body.classList.add("jah-ready");
  });
})();
