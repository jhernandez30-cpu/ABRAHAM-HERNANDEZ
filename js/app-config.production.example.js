/**
 * Plantilla de configuracion para produccion.
 * Copia este archivo como app-config.production.js y define la URL publica del backend.
 * No subas secretos aqui; solo la URL base del bridge_api desplegado.
 */
(() => {
  const productionApiBaseUrl = 'https://URL_PUBLICA_DE_RAILWAY';

  window.APP_CONFIG = {
    ...(window.APP_CONFIG || {}),
    API_BASE_URL: productionApiBaseUrl.replace(/\/$/, '')
  };

  window.TUTOR_IA_BRIDGE_URL = window.APP_CONFIG.API_BASE_URL;
  if (window.APP_CONFIG.API_BASE_URL) {
    window.TUTOR_IA_ENDPOINTS = [`${window.APP_CONFIG.API_BASE_URL}/api/chat`];
  }
})();
