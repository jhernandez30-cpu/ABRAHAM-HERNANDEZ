(() => {
  const LOCAL_API_BASE_URL = 'http://127.0.0.1:8787';
  const PRODUCTION_API_BASE_URL = 'https://jah-ai-bridge-production.up.railway.app';
  const GITHUB_PAGES_HOSTS = new Set(['jhernandez30-cpu.github.io']);
  const currentConfig = window.APP_CONFIG || {};

  function readMeta(name) {
    const meta = document.querySelector(`meta[name="${name}"]`);
    return String(meta?.getAttribute('content') || '').trim();
  }

  function readMetaApiBaseUrl() {
    return readMeta('jah-api-base-url');
  }

  function readMetaSupabaseUrl() {
    return readMeta('supabase-url');
  }

  function readMetaSupabaseAnonKey() {
    return readMeta('supabase-anon-key');
  }

  function readMetaRunMode() {
    const value = readMeta('jah-run-mode').toLowerCase();
    if (value === 'production' || value === 'local') return value;
    return '';
  }

  function readQueryApiBaseUrl() {
    try {
      return String(new URLSearchParams(window.location.search).get('api_base') || '').trim();
    } catch (error) {
      return '';
    }
  }

  function readStoredRunMode() {
    try {
      const stored = String(localStorage.getItem('jahBridgeRunMode') || '').trim().toLowerCase();
      if (stored === 'production' || stored === 'local') return stored;
    } catch (error) {
      return '';
    }
    return '';
  }

  function isPrivateIpv4(hostname) {
    const parts = String(hostname || '').split('.').map(part => Number(part));
    if (parts.length !== 4 || parts.some(part => Number.isNaN(part))) return false;
    if (parts[0] === 10) return true;
    if (parts[0] === 192 && parts[1] === 168) return true;
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;
    return false;
  }

  function isLocalHostname(hostname) {
    const host = String(hostname || '').toLowerCase();
    if (!host || host === 'localhost' || host === '127.0.0.1' || host === '::1') return true;
    if (host.endsWith('.localhost')) return true;
    return isPrivateIpv4(host);
  }

  function isGitHubPagesHost() {
    return GITHUB_PAGES_HOSTS.has(String(window.location.hostname || '').toLowerCase());
  }

  function detectLocalMode() {
    if (window.location.protocol === 'file:') return true;
    return isLocalHostname(window.location.hostname);
  }

  function normalizeApiBaseUrl(value) {
    return String(value || '').trim().replace(/\/$/, '');
  }

  function isProductionSafeApiUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && !isLocalHostname(url.hostname);
    } catch (error) {
      return false;
    }
  }

  function resolveProductionApiBaseUrl(liveConfig = currentConfig) {
    const configured = normalizeApiBaseUrl(
      readQueryApiBaseUrl()
      || readMetaApiBaseUrl()
      || liveConfig.API_BASE_URL
      || PRODUCTION_API_BASE_URL
    );
    if (configured && isProductionSafeApiUrl(configured)) return configured;
    return PRODUCTION_API_BASE_URL;
  }

  function resolveRunMode() {
    const explicit = readMetaRunMode()
      || readStoredRunMode()
      || String(currentConfig.RUN_MODE || '').trim().toLowerCase();
    if (explicit === 'production' || explicit === 'local') return explicit;

    if (detectLocalMode()) return 'local';
    if (isGitHubPagesHost()) return 'production';
    const productionUrl = readQueryApiBaseUrl() || readMetaApiBaseUrl() || currentConfig.API_BASE_URL;
    if (productionUrl) return 'production';
    return 'production';
  }

  function resolveApiBaseUrl() {
    const liveConfig = window.APP_CONFIG || currentConfig;
    const runMode = resolveRunMode();

    if (runMode === 'production') {
      return resolveProductionApiBaseUrl(liveConfig);
    }

    return normalizeApiBaseUrl(
      readQueryApiBaseUrl()
      || liveConfig.API_BASE_URL
      || window.TUTOR_IA_BRIDGE_URL
      || LOCAL_API_BASE_URL
    );
  }

  const runMode = resolveRunMode();
  const configuredApiBaseUrl = resolveApiBaseUrl();
  const supabaseUrl = String(readMetaSupabaseUrl() || currentConfig.SUPABASE_URL || '').trim().replace(/\/$/, '');
  const supabaseAnonKey = String(readMetaSupabaseAnonKey() || currentConfig.SUPABASE_ANON_KEY || '').trim();

  window.APP_CONFIG = {
    ...currentConfig,
    RUN_MODE: runMode,
    API_BASE_URL: configuredApiBaseUrl,
    SUPABASE_URL: supabaseUrl,
    SUPABASE_ANON_KEY: supabaseAnonKey,
    SUPABASE_AUTH_ENABLED: Boolean(supabaseUrl && supabaseAnonKey),
    SUPABASE_GOOGLE_ENABLED: currentConfig.SUPABASE_GOOGLE_ENABLED === true,
    SUPABASE_APPLE_ENABLED: currentConfig.SUPABASE_APPLE_ENABLED === true,
    LOCAL_API_BASE_URL,
    PRODUCTION_API_BASE_URL,
    IS_LOCAL_MODE: detectLocalMode(),
    IS_GITHUB_PAGES: isGitHubPagesHost(),
    resolveApiBaseUrl,
    setRunMode(mode) {
      const normalized = String(mode || '').trim().toLowerCase();
      if (normalized !== 'production' && normalized !== 'local') return;
      try {
        localStorage.setItem('jahBridgeRunMode', normalized);
      } catch (error) {
        return;
      }
      window.location.reload();
    }
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
