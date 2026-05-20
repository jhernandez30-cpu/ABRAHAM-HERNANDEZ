(function () {
  "use strict";

  const STORAGE_KEY = "jah_cookie_consent";
  const PREFS_KEY = "jah_cookie_preferences";
  const path = window.location.pathname.split("/").pop() || "index.html";
  const isPreviewHome = path === "index-preview.html" || path === "index.html";

  if (!isPreviewHome) return;
  if (window.localStorage.getItem(STORAGE_KEY)) return;
  if (document.getElementById("cookieBanner")) return;

  const savePreference = (value, preferences) => {
    window.localStorage.setItem(STORAGE_KEY, value);
    window.localStorage.setItem(PREFS_KEY, JSON.stringify(preferences));
  };

  const closeBanner = () => {
    document.getElementById("cookieBanner")?.remove();
  };

  const createBanner = () => {
    const banner = document.createElement("section");
    banner.id = "cookieBanner";
    banner.className = "cookie-banner active";
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-live", "polite");
    banner.setAttribute("aria-labelledby", "cookieTitle");

    banner.innerHTML = `
      <div class="cookie-banner-inner">
        <div class="cookie-card">
          <button class="cookie-settings-close" id="cookieClose" type="button" aria-label="Cerrar aviso de cookies">&times;</button>
          <div class="cookie-icon-wrapper">
            <span class="cookie-icon" aria-hidden="true">✓</span>
            <h3 id="cookieTitle">Uso de cookies</h3>
          </div>
          <div class="cookie-content">
            <div class="cookie-text">
              <p>Usamos cookies necesarias para que el sitio funcione y cookies opcionales para mejorar la experiencia de navegacion.</p>
            </div>
            <div class="cookie-actions">
              <button type="button" class="cookie-btn cookie-btn-accept" id="cookieAcceptAll">Aceptar</button>
              <button type="button" class="cookie-btn cookie-btn-reject" id="cookieRejectAll">Rechazar</button>
              <button type="button" class="cookie-btn cookie-btn-settings" id="cookieSettingsBtn">Configurar</button>
            </div>
          </div>
          <div class="cookie-settings" id="cookieSettings" hidden>
            <label><input type="checkbox" checked disabled> Cookies necesarias</label>
            <label><input type="checkbox" id="analyticsCookies"> Analitica</label>
            <label><input type="checkbox" id="marketingCookies"> Marketing</label>
            <button type="button" class="cookie-btn cookie-btn-accept" id="cookieSaveSettings">Guardar preferencias</button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(banner);

    banner.querySelector("#cookieAcceptAll")?.addEventListener("click", () => {
      savePreference("accepted", { necessary: true, analytics: true, marketing: true });
      closeBanner();
    });

    banner.querySelector("#cookieRejectAll")?.addEventListener("click", () => {
      savePreference("rejected", { necessary: true, analytics: false, marketing: false });
      closeBanner();
    });

    banner.querySelector("#cookieClose")?.addEventListener("click", () => {
      savePreference("closed", { necessary: true, analytics: false, marketing: false });
      closeBanner();
    });

    banner.querySelector("#cookieSettingsBtn")?.addEventListener("click", () => {
      const settings = banner.querySelector("#cookieSettings");
      if (settings) settings.hidden = !settings.hidden;
    });

    banner.querySelector("#cookieSaveSettings")?.addEventListener("click", () => {
      savePreference("custom", {
        necessary: true,
        analytics: Boolean(banner.querySelector("#analyticsCookies")?.checked),
        marketing: Boolean(banner.querySelector("#marketingCookies")?.checked)
      });
      closeBanner();
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createBanner, { once: true });
  } else {
    createBanner();
  }
})();
