/**
 * Plantilla de configuracion para produccion.
 * Copia este archivo como app-config.production.js y define la URL publica del backend.
 * No subas secretos aqui. La anon key de Supabase es publica, pero la service role
 * key y DATABASE_URL van solo en Railway.
 */
(() => {
  const productionApiBaseUrl = 'https://jah-ai-bridge-production.up.railway.app';
  const supabaseUrl = 'https://TU-PROYECTO.supabase.co';
  const supabaseAnonKey = 'TU_SUPABASE_ANON_KEY_PUBLICA';

  window.APP_CONFIG = {
    ...(window.APP_CONFIG || {}),
    RUN_MODE: 'production',
    API_BASE_URL: productionApiBaseUrl.replace(/\/$/, ''),
    SUPABASE_URL: supabaseUrl.replace(/\/$/, ''),
    SUPABASE_ANON_KEY: supabaseAnonKey,
    SUPABASE_AUTH_ENABLED: Boolean(supabaseUrl && supabaseAnonKey),
    SUPABASE_GOOGLE_ENABLED: true,
    SUPABASE_APPLE_ENABLED: true
  };

  window.TUTOR_IA_BRIDGE_URL = window.APP_CONFIG.API_BASE_URL;
  if (window.APP_CONFIG.API_BASE_URL) {
    window.TUTOR_IA_ENDPOINTS = [`${window.APP_CONFIG.API_BASE_URL}/api/chat`];
  }
})();
