/**
 * cookies.js - Sistema de consentimiento de cookies para Abraham Hernández
 * Muestra un banner de cookies cada vez que el usuario visita el sitio.
 * Crea cookies reales del navegador según las preferencias del usuario.
 */
(function () {
    'use strict';

    // ===== Configuración =====
    const COOKIE_CONSENT_KEY = 'jah_cookie_consent';
    const COOKIE_PREFS_KEY = 'jah_cookie_preferences';

    // ===== Estado =====
    let settingsPanelOpen = false;

    // ===== Utilidades de localStorage =====
    function getConsent() {
        try {
            return JSON.parse(localStorage.getItem(COOKIE_CONSENT_KEY));
        } catch {
            return null;
        }
    }

    function getPreferences() {
        try {
            return JSON.parse(localStorage.getItem(COOKIE_PREFS_KEY)) || defaultPreferences();
        } catch {
            return defaultPreferences();
        }
    }

    function defaultPreferences() {
        return {
            necessary: true,    // Siempre activas
            analytics: false,
            marketing: false,
            personalization: false
        };
    }

    function saveConsent(accepted, preferences) {
        const consent = {
            accepted: accepted,
            timestamp: new Date().toISOString(),
            preferences: preferences
        };
        localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(consent));
        localStorage.setItem(COOKIE_PREFS_KEY, JSON.stringify(preferences));
    }

    // ===== Utilidades de cookies del navegador =====
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = 'expires=' + date.toUTCString();
        const secure = location.protocol === 'https:' ? '; Secure' : '';
        document.cookie = name + '=' + encodeURIComponent(value) + '; ' + expires + '; path=/; SameSite=Lax' + secure;
    }

    function deleteCookie(name) {
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Lax';
    }

    function getCookie(name) {
        const nameEQ = name + '=';
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let c = cookies[i].trim();
            if (c.indexOf(nameEQ) === 0) {
                return decodeURIComponent(c.substring(nameEQ.length));
            }
        }
        return null;
    }

    // ===== Crear HTML del banner =====
    function createBanner() {
        // Overlay
        const overlay = document.createElement('div');
        overlay.className = 'cookie-overlay';
        overlay.id = 'cookieOverlay';

        // Banner
        const banner = document.createElement('div');
        banner.className = 'cookie-banner';
        banner.id = 'cookieBanner';
        banner.setAttribute('role', 'dialog');
        banner.setAttribute('aria-label', 'Consentimiento de cookies');

        banner.innerHTML = `
            <div class="cookie-banner-inner">
                <div class="cookie-card">
                    <div class="cookie-icon-wrapper">
                        <div class="cookie-icon">
                            <i class="fas fa-cookie-bite"></i>
                        </div>
                        <h3>Utilizamos cookies</h3>
                    </div>
                    <div class="cookie-content">
                        <div class="cookie-text">
                            <p>Usamos cookies para mejorar tu experiencia de navegación, analizar el tráfico del sitio y personalizar el contenido. Al hacer clic en "Aceptar todas", consientes el uso de todas las cookies. Puedes gestionar tus preferencias en cualquier momento.</p>
                        </div>
                        <div class="cookie-actions">
                            <button class="cookie-btn cookie-btn-accept" id="cookieAcceptAll" type="button">
                                <i class="fas fa-check" style="margin-right: 6px;"></i> Aceptar todas
                            </button>
                            <button class="cookie-btn cookie-btn-reject" id="cookieRejectAll" type="button">
                                Rechazar
                            </button>
                            <button class="cookie-btn cookie-btn-settings" id="cookieSettingsBtn" type="button">
                                <i class="fas fa-sliders-h" style="margin-right: 4px;"></i> Configurar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Panel de configuración
        const settingsPanel = document.createElement('div');
        settingsPanel.className = 'cookie-settings-panel';
        settingsPanel.id = 'cookieSettingsPanel';
        settingsPanel.setAttribute('role', 'dialog');
        settingsPanel.setAttribute('aria-label', 'Configuración de cookies');

        const prefs = getPreferences();

        settingsPanel.innerHTML = `
            <div class="cookie-settings-header">
                <h3><i class="fas fa-cog" style="color: #00ff9d; margin-right: 8px;"></i>Configuración de cookies</h3>
                <button class="cookie-settings-close" id="cookieSettingsClose" type="button" aria-label="Cerrar">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="cookie-settings-body">
                <p>Gestiona tus preferencias de cookies. Las cookies necesarias son imprescindibles para el funcionamiento del sitio y no pueden desactivarse.</p>
                
                <!-- Necesarias -->
                <div class="cookie-category">
                    <div class="cookie-category-header">
                        <h4><i class="fas fa-lock"></i> Necesarias</h4>
                        <span class="cookie-badge-required">Siempre activas</span>
                    </div>
                    <p>Esenciales para el funcionamiento básico del sitio web: navegación, seguridad y preferencias del usuario.</p>
                </div>

                <!-- Analíticas -->
                <div class="cookie-category">
                    <div class="cookie-category-header">
                        <h4><i class="fas fa-chart-bar"></i> Analíticas</h4>
                        <label class="cookie-toggle">
                            <input type="checkbox" id="cookieAnalytics" ${prefs.analytics ? 'checked' : ''}>
                            <span class="cookie-toggle-slider"></span>
                        </label>
                    </div>
                    <p>Nos ayudan a entender cómo los visitantes interactúan con el sitio, recopilando información de forma anónima.</p>
                </div>

                <!-- Marketing -->
                <div class="cookie-category">
                    <div class="cookie-category-header">
                        <h4><i class="fas fa-bullhorn"></i> Marketing</h4>
                        <label class="cookie-toggle">
                            <input type="checkbox" id="cookieMarketing" ${prefs.marketing ? 'checked' : ''}>
                            <span class="cookie-toggle-slider"></span>
                        </label>
                    </div>
                    <p>Se utilizan para mostrar anuncios relevantes y campañas de marketing ajustadas a tus intereses.</p>
                </div>

                <!-- Personalización -->
                <div class="cookie-category">
                    <div class="cookie-category-header">
                        <h4><i class="fas fa-palette"></i> Personalización</h4>
                        <label class="cookie-toggle">
                            <input type="checkbox" id="cookiePersonalization" ${prefs.personalization ? 'checked' : ''}>
                            <span class="cookie-toggle-slider"></span>
                        </label>
                    </div>
                    <p>Permiten recordar tus preferencias de idioma, tema y otras configuraciones personales.</p>
                </div>
            </div>
            <div class="cookie-settings-footer">
                <button class="cookie-btn cookie-btn-reject" id="cookieSaveSettings" type="button">
                    Guardar preferencias
                </button>
                <button class="cookie-btn cookie-btn-accept" id="cookieAcceptAllSettings" type="button">
                    Aceptar todas
                </button>
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(banner);
        document.body.appendChild(settingsPanel);
    }

    // ===== Mostrar/Ocultar banner =====
    function showBanner() {
        const banner = document.getElementById('cookieBanner');
        const overlay = document.getElementById('cookieOverlay');
        if (banner) {
            requestAnimationFrame(() => {
                banner.classList.add('active');
                overlay.classList.add('active');
            });
        }
    }

    function hideBanner(callback) {
        const banner = document.getElementById('cookieBanner');
        const overlay = document.getElementById('cookieOverlay');
        if (banner) {
            banner.classList.remove('active');
            banner.classList.add('hiding');
            overlay.classList.remove('active');
            setTimeout(() => {
                banner.classList.remove('hiding');
                if (callback) callback();
            }, 600);
        }
    }

    // ===== Panel de configuración =====
    function openSettingsPanel() {
        const panel = document.getElementById('cookieSettingsPanel');
        const overlay = document.getElementById('cookieOverlay');
        if (panel) {
            settingsPanelOpen = true;
            panel.classList.add('active');
            overlay.classList.add('active');
        }
    }

    function closeSettingsPanel() {
        const panel = document.getElementById('cookieSettingsPanel');
        const overlay = document.getElementById('cookieOverlay');
        if (panel) {
            settingsPanelOpen = false;
            panel.classList.remove('active');
            const banner = document.getElementById('cookieBanner');
            if (!banner || !banner.classList.contains('active')) {
                overlay.classList.remove('active');
            }
        }
    }

    // ===== Acciones =====
    function acceptAll() {
        const prefs = {
            necessary: true,
            analytics: true,
            marketing: true,
            personalization: true
        };
        saveConsent(true, prefs);
        closeSettingsPanel();
        hideBanner(() => {
            applyCookies(prefs);
        });
    }

    function rejectAll() {
        const prefs = {
            necessary: true,
            analytics: false,
            marketing: false,
            personalization: false
        };
        saveConsent(false, prefs);
        closeSettingsPanel();
        hideBanner(() => {
            applyCookies(prefs);
        });
    }

    function saveSettings() {
        const prefs = {
            necessary: true,
            analytics: document.getElementById('cookieAnalytics')?.checked || false,
            marketing: document.getElementById('cookieMarketing')?.checked || false,
            personalization: document.getElementById('cookiePersonalization')?.checked || false
        };
        saveConsent(true, prefs);
        closeSettingsPanel();
        hideBanner(() => {
            applyCookies(prefs);
        });
    }

    // ===== Aplicar cookies según preferencias =====
    function applyCookies(prefs) {
        const COOKIE_DURATION = 365; // días

        // Disparar evento personalizado para que otros scripts puedan reaccionar
        window.dispatchEvent(new CustomEvent('cookieConsentUpdated', {
            detail: prefs
        }));

        // --- Cookie de consentimiento (siempre se crea) ---
        setCookie('jah_consent', JSON.stringify({
            accepted: true,
            timestamp: new Date().toISOString(),
            preferences: prefs
        }), COOKIE_DURATION);

        // --- Cookies necesarias (siempre activas) ---
        setCookie('jah_necessary', 'true', COOKIE_DURATION);
        setCookie('jah_session_id', generateSessionId(), COOKIE_DURATION);

        // --- Cookies analíticas ---
        if (prefs.analytics) {
            setCookie('jah_analytics', 'true', COOKIE_DURATION);
            setCookie('jah_first_visit', getCookie('jah_first_visit') || new Date().toISOString(), COOKIE_DURATION);
            setCookie('jah_page_views', String(parseInt(getCookie('jah_page_views') || '0') + 1), COOKIE_DURATION);
            setCookie('jah_referrer', document.referrer || 'direct', COOKIE_DURATION);
            console.log('[Cookies] 🍪 Cookies analíticas activadas');
        } else {
            deleteCookie('jah_analytics');
            deleteCookie('jah_first_visit');
            deleteCookie('jah_page_views');
            deleteCookie('jah_referrer');
            console.log('[Cookies] Cookies analíticas desactivadas');
        }

        // --- Cookies de marketing ---
        if (prefs.marketing) {
            setCookie('jah_marketing', 'true', COOKIE_DURATION);
            setCookie('jah_campaign_source', getUrlParam('utm_source') || 'none', COOKIE_DURATION);
            setCookie('jah_campaign_medium', getUrlParam('utm_medium') || 'none', COOKIE_DURATION);
            setCookie('jah_campaign_name', getUrlParam('utm_campaign') || 'none', COOKIE_DURATION);
            console.log('[Cookies] 🍪 Cookies de marketing activadas');
        } else {
            deleteCookie('jah_marketing');
            deleteCookie('jah_campaign_source');
            deleteCookie('jah_campaign_medium');
            deleteCookie('jah_campaign_name');
            console.log('[Cookies] Cookies de marketing desactivadas');
        }

        // --- Cookies de personalización ---
        if (prefs.personalization) {
            setCookie('jah_personalization', 'true', COOKIE_DURATION);
            setCookie('jah_theme', getCookie('jah_theme') || 'dark', COOKIE_DURATION);
            setCookie('jah_language', getCookie('jah_language') || navigator.language || 'es', COOKIE_DURATION);
            setCookie('jah_last_visited_page', window.location.pathname, COOKIE_DURATION);
            console.log('[Cookies] 🍪 Cookies de personalización activadas');
        } else {
            deleteCookie('jah_personalization');
            deleteCookie('jah_theme');
            deleteCookie('jah_language');
            deleteCookie('jah_last_visited_page');
            console.log('[Cookies] Cookies de personalización desactivadas');
        }
    }

    // ===== Helpers =====
    function generateSessionId() {
        return 'jah_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 9);
    }

    function getUrlParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }

    // ===== Event listeners =====
    function bindEvents() {
        // Aceptar todas
        document.getElementById('cookieAcceptAll')?.addEventListener('click', acceptAll);

        // Rechazar todas
        document.getElementById('cookieRejectAll')?.addEventListener('click', rejectAll);

        // Abrir configuración
        document.getElementById('cookieSettingsBtn')?.addEventListener('click', () => {
            openSettingsPanel();
        });

        // Cerrar configuración
        document.getElementById('cookieSettingsClose')?.addEventListener('click', closeSettingsPanel);

        // Guardar preferencias desde panel
        document.getElementById('cookieSaveSettings')?.addEventListener('click', saveSettings);

        // Aceptar todas desde panel
        document.getElementById('cookieAcceptAllSettings')?.addEventListener('click', acceptAll);

        // Click en overlay cierra el panel si está abierto
        document.getElementById('cookieOverlay')?.addEventListener('click', () => {
            if (settingsPanelOpen) {
                closeSettingsPanel();
            }
        });

        // Tecla Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (settingsPanelOpen) {
                    closeSettingsPanel();
                }
            }
        });
    }

    // ===== Inicialización =====
    function init() {
        // Siempre crear y mostrar el banner al entrar al sitio
        createBanner();
        bindEvents();

        // Pequeño delay para que el DOM esté listo y la animación se vea suave
        setTimeout(() => {
            showBanner();
        }, 1200); // Espera a que el preloader termine
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
