(function () {
  "use strict";

  const body = document.body;
  if (!body || !body.classList.contains("jah-preview-surface")) return;

  const LOCALE_KEY = "portfolio-locale";
  const originalTextNodes = new WeakMap();
  const originalAttrs = new WeakMap();
  let originalTitle = document.title;

  const isLegalDocument = () => Boolean(document.getElementById("contet-container"));

  const getRelativeBase = () => {
    return document.querySelector('meta[name="relative-base"]')?.getAttribute("content") || "";
  };

  const getLocale = () => {
    const saved = localStorage.getItem(LOCALE_KEY);
    if (saved === "en") return "en";
    if (saved === "de") {
      localStorage.setItem(LOCALE_KEY, "es");
      return "es";
    }
    if (saved === "es") return "es";
    return document.documentElement.lang.toLowerCase().startsWith("en") ? "en" : "es";
  };

  const getLabels = (locale = getLocale()) => {
    if (locale === "en") {
      return {
        privacy: "Privacy",
        legal: "Legal notice",
        language: "ES",
        nav: "Main navigation",
        footer: "Main site links"
      };
    }

    return {
      privacy: "Privacidad",
      legal: "Aviso legal",
      language: "EN",
      nav: "Navegación principal",
      footer: "Enlaces principales del sitio"
    };
  };

  const getLegalHref = (page, locale = getLocale()) => {
    const base = getRelativeBase();
    const suffix = page === "legal" ? "legal.html" : "privacy.html";
    return locale === "en"
      ? `${base}preview-2025/${suffix}`
      : `${base}preview-2025/es/${suffix}`;
  };

  const getDictionary = () => window.JAH_SITE_I18N?.esToEn || {};

  const translateValue = (value, locale = getLocale()) => {
    if (locale !== "en") return value;
    const trimmed = value.trim();
    if (!trimmed) return value;
    const normalized = trimmed.replace(/\s+/g, " ");
    const translated = getDictionary()[trimmed] || getDictionary()[normalized];
    if (!translated) return value;
    return value.replace(trimmed, translated);
  };

  const loadSiteI18n = () => {
    if (window.JAH_SITE_I18N) return Promise.resolve();

    return new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = `${getRelativeBase()}js/site-i18n.js`;
      script.onload = () => resolve();
      script.onerror = () => resolve();
      document.head.appendChild(script);
    });
  };

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

    const isSpanish = document.documentElement.lang.toLowerCase().startsWith("es");
    const labels = isSpanish
      ? {
          nav: "Navegacion legal",
          home: "Inicio",
          services: "Servicios",
          projects: "Proyectos",
          resources: "Recursos",
          contact: "Contacto",
          privacy: "Privacidad",
          legal: "Aviso legal",
          language: "EN",
          languageHref: "../privacy.html",
          copyright: "Todos los derechos reservados"
        }
      : {
          nav: "Legal navigation",
          home: "Home",
          services: "Services",
          projects: "Projects",
          resources: "Resources",
          contact: "Contact",
          privacy: "Privacy",
          legal: "Legal notice",
          language: "ES",
          languageHref: "es/privacy.html",
          copyright: "All rights reserved"
        };

    const pageName = window.location.pathname.endsWith("/legal.html") ? "legal" : "privacy";
    if (isSpanish) labels.languageHref = `../${pageName}.html`;
    else labels.languageHref = `es/${pageName}.html`;

    const isNested = window.location.pathname.includes("/preview-2025/es/");
    const base = isNested ? "../../" : "../";
    const privacyHref = "privacy.html";
    const legalHref = "legal.html";

    const header = document.createElement("header");
    header.innerHTML = `
      <nav class="navbar" id="navbar" aria-label="${labels.nav}">
        <div class="logo">
          <a href="${base}index.html" class="brand-logo" aria-label="Inicio - Abraham Hernandez">
            <img src="${base}assets/jah-logo.png" alt="Logo JAH de Abraham Hernandez" width="180" height="120" loading="eager" decoding="async">
          </a>
        </div>
        <div class="nav-links">
          <a href="${base}index.html" class="nav-link">${labels.home}</a>
          <a href="${base}index.html#servicios" class="nav-link">${labels.services}</a>
          <a href="${base}index.html#proyectos" class="nav-link">${labels.projects}</a>
          <a href="${base}index.html#recursos" class="nav-link">${labels.resources}</a>
          <a href="${base}index.html#contacto" class="nav-link">${labels.contact}</a>
          <a href="${privacyHref}" class="nav-link">${labels.privacy}</a>
          <a href="${legalHref}" class="nav-link">${labels.legal}</a>
          <a href="${labels.languageHref}" class="nav-link">${labels.language}</a>
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
        <a href="${base}index.html#servicios">${labels.services}</a>
        <a href="${base}index.html#proyectos">${labels.projects}</a>
        <a href="${base}index.html#recursos">${labels.resources}</a>
        <a href="${base}index.html#contacto">${labels.contact}</a>
        <a href="${privacyHref}">${labels.privacy}</a>
        <a href="${legalHref}">${labels.legal}</a>
        <a href="${labels.languageHref}">${labels.language}</a>
      </div>
      <p>© 2026 Abraham Hernandez - ${labels.copyright}</p>
    `;
    body.appendChild(footer);
  };

  const addSiteLanguageControls = () => {
    if (isLegalDocument()) return;
    const labels = getLabels();
    const privacyHref = getLegalHref("privacy");
    const legalHref = getLegalHref("legal");

    document.querySelectorAll(".nav-links").forEach((nav) => {
      nav.setAttribute("aria-label", labels.nav);

      let privacy = nav.querySelector('[data-site-i18n-link="privacy"]');
      if (!privacy) {
        privacy = document.createElement("a");
        privacy.className = "nav-link";
        privacy.setAttribute("data-site-i18n-link", "privacy");
        nav.appendChild(privacy);
      }
      privacy.href = privacyHref;
      privacy.textContent = labels.privacy;

      let legal = nav.querySelector('[data-site-i18n-link="legal"]');
      if (!legal) {
        legal = document.createElement("a");
        legal.className = "nav-link";
        legal.setAttribute("data-site-i18n-link", "legal");
        nav.appendChild(legal);
      }
      legal.href = legalHref;
      legal.textContent = labels.legal;

      nav.querySelector('[data-site-i18n-link="language"]')?.remove();
    });

    document.querySelectorAll(".site-footer-links").forEach((footerLinks) => {
      footerLinks.setAttribute("aria-label", labels.footer);

      let privacy = footerLinks.querySelector('[data-site-i18n-link="privacy"]');
      if (!privacy) {
        privacy = document.createElement("a");
        privacy.setAttribute("data-site-i18n-link", "privacy");
        footerLinks.appendChild(privacy);
      }
      privacy.href = privacyHref;
      privacy.textContent = labels.privacy;

      let legal = footerLinks.querySelector('[data-site-i18n-link="legal"]');
      if (!legal) {
        legal = document.createElement("a");
        legal.setAttribute("data-site-i18n-link", "legal");
        footerLinks.appendChild(legal);
      }
      legal.href = legalHref;
      legal.textContent = labels.legal;

      let language = footerLinks.querySelector('[data-site-i18n-link="language"]');
      if (!language) {
        language = document.createElement("a");
        language.href = "#";
        language.setAttribute("data-site-i18n-link", "language");
        footerLinks.appendChild(language);
      }
      language.textContent = labels.language;
      language.setAttribute("aria-label", labels.language === "EN" ? "Cambiar a inglés" : "Switch to Spanish");
    });
  };

  const translateAttributes = (locale = getLocale()) => {
    const attrs = ["placeholder", "aria-label", "alt", "title"];

    document.querySelectorAll("*").forEach((element) => {
      if (element.closest("script, style, noscript")) return;
      if (element.closest("[data-site-i18n-link]")) return;

      let saved = originalAttrs.get(element);
      if (!saved) {
        saved = {};
        originalAttrs.set(element, saved);
      }

      attrs.forEach((attr) => {
        if (!element.hasAttribute(attr)) return;
        if (!Object.prototype.hasOwnProperty.call(saved, attr)) {
          saved[attr] = element.getAttribute(attr);
        }

        const original = saved[attr];
        element.setAttribute(attr, locale === "en" ? translateValue(original, locale) : original);
      });
    });
  };

  const translateTextNodes = (locale = getLocale()) => {
    const walker = document.createTreeWalker(
      body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const parent = node.parentElement;
          if (!parent || parent.closest("script, style, noscript")) return NodeFilter.FILTER_REJECT;
          if (parent.closest("[data-site-i18n-link]")) return NodeFilter.FILTER_REJECT;
          if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach((node) => {
      if (!originalTextNodes.has(node)) originalTextNodes.set(node, node.nodeValue);
      const original = originalTextNodes.get(node);
      node.nodeValue = locale === "en" ? translateValue(original, locale) : original;
    });
  };

  const translateMeta = (locale = getLocale()) => {
    if (locale === "en") {
      document.title = translateValue(originalTitle, locale);
    } else {
      document.title = originalTitle;
    }

    document.querySelectorAll('meta[name="description"], meta[property="og:title"], meta[property="og:description"], meta[name="twitter:title"], meta[name="twitter:description"]').forEach((meta) => {
      if (!meta.dataset.siteI18nOriginal) meta.dataset.siteI18nOriginal = meta.getAttribute("content") || "";
      const original = meta.dataset.siteI18nOriginal;
      meta.setAttribute("content", locale === "en" ? translateValue(original, locale) : original);
    });
  };

  const applySiteLocale = (locale = getLocale()) => {
    if (isLegalDocument()) return;
    document.documentElement.lang = locale === "en" ? "en" : "es";
    localStorage.setItem(LOCALE_KEY, locale);
    addSiteLanguageControls();
    translateAttributes(locale);
    translateTextNodes(locale);
    translateMeta(locale);
  };

  const bindLanguageToggle = () => {
    document.addEventListener("click", (event) => {
      const toggle = event.target.closest('[data-site-i18n-link="language"]');
      if (!toggle || isLegalDocument()) return;
      event.preventDefault();
      applySiteLocale(getLocale() === "en" ? "es" : "en");
    });
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
    bindLanguageToggle();
    loadSiteI18n().then(() => {
      applySiteLocale(getLocale());
    });
  });
})();
