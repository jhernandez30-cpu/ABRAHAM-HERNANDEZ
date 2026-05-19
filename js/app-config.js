(() => {
  const currentConfig = window.APP_CONFIG || {};
  const localApiBaseUrl = 'http://127.0.0.1:8787';
  const isLocalMode = ['localhost', '127.0.0.1', ''].includes(window.location.hostname)
    || window.location.protocol === 'file:';

  const configuredApiBaseUrl = String(
    currentConfig.API_BASE_URL
    || window.TUTOR_IA_BRIDGE_URL
    || (isLocalMode ? localApiBaseUrl : '')
  ).replace(/\/$/, '');

  window.APP_CONFIG = {
    ...currentConfig,
    API_BASE_URL: configuredApiBaseUrl,
    LOCAL_API_BASE_URL: localApiBaseUrl,
    IS_LOCAL_MODE: isLocalMode
  };

  window.TUTOR_IA_BRIDGE_URL = configuredApiBaseUrl;
  window.TUTOR_IA_PROJECT_PATH = window.TUTOR_IA_PROJECT_PATH || '';
  window.TUTOR_IA_BRAIN_ROOT = window.TUTOR_IA_BRAIN_ROOT || '';
  window.JARVIS_READ_RESPONSES = true;
  window.JARVIS_ADVANCED_PROVIDER = 'mark_xxxix';
  window.TUTOR_IA_ENDPOINTS = window.TUTOR_IA_ENDPOINTS || (
    configuredApiBaseUrl ? [`${configuredApiBaseUrl}/api/chat`] : []
  );
})();
