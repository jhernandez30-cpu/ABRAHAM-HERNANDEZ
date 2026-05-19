const STORAGE_KEY = 'tutorIaChatHistory';
const ACTIVE_CHAT_KEY = 'tutorIaActiveChatId';
const SESSION_KEY = 'jah_ai_session_id';
const TUTOR_IA_ENABLED_KEY = 'tutorIaEnabled';
const DEFAULT_MODE = 'Cerebro Unificado';
const PROJECT_PATH = window.TUTOR_IA_PROJECT_PATH || '';
const BRAIN_ROOT = window.TUTOR_IA_BRAIN_ROOT || '';
const BRIDGE_URL = String(
  window.APP_CONFIG?.API_BASE_URL
  || window.TUTOR_IA_BRIDGE_URL
  || ''
).replace(/\/$/, '');
const DEFAULT_ENDPOINTS = BRIDGE_URL ? [`${BRIDGE_URL}/api/chat`] : [];
const CHAT_ENDPOINT = BRIDGE_URL ? `${BRIDGE_URL}/api/chat` : '';
const UPLOAD_ENDPOINT = BRIDGE_URL ? `${BRIDGE_URL}/api/upload` : '';
const JARVIS_MARK_STATUS_ENDPOINT = BRIDGE_URL ? `${BRIDGE_URL}/api/jarvis/mark/status` : '';
const JARVIS_MARK_LAUNCH_ENDPOINT = BRIDGE_URL ? `${BRIDGE_URL}/api/jarvis/mark/launch` : '';
const CHAT_TIMEOUT_MS = 120000;
const CLIENT_CONTEXT_TURNS = 6;
const CLIENT_CONTEXT_MAX_CHARS = 2400;
const JARVIS_READ_RESPONSES = window.JARVIS_READ_RESPONSES === undefined
  ? true
  : window.JARVIS_READ_RESPONSES === true || window.JARVIS_READ_RESPONSES === 'true';
const ALLOWED_FILE_EXTENSIONS = new Set([
  'png', 'jpg', 'jpeg', 'webp', 'pdf', 'docx', 'txt', 'md', 'csv', 'json', 'py', 'js', 'html', 'css', 'sql', 'cs'
]);

document.addEventListener('DOMContentLoaded', () => {
  const chatMain = document.querySelector('.chat-main');
  const coachMessages = document.getElementById('coachMessages');
  const emptyChatState = document.getElementById('emptyChatState');
  const coachForm = document.getElementById('coachForm');
  const coachInput = document.getElementById('coachInput');
  const brainStatus = document.getElementById('brainStatus');
  const brainStatusText = document.getElementById('brainStatusText');
  const adminOnlyElements = document.querySelectorAll('[data-admin-only]');
  const quickContextCard = document.querySelector('.quick-context-card');
  const newChatBtn = document.getElementById('newChatBtn');
  const chatSearchInput = document.getElementById('chatSearchInput');
  const chatHistoryList = document.getElementById('chatHistoryList');
  const activeChatLabel = document.getElementById('activeChatLabel');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  const openSidebarBtn = document.getElementById('openSidebarBtn');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const chatSidebar = document.getElementById('chatSidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const tutorIABtn = document.getElementById('tutorIABtn');
  const smartSearchBtn = document.getElementById('smartSearchBtn');
  const fileInput = document.getElementById('fileInput');
  const attachmentPreview = document.getElementById('attachmentPreview');
  const sendButton = coachForm ? coachForm.querySelector('.send-orb') : null;
  const jarvisVoiceBtn = document.getElementById('jarvisVoiceBtn');
  const jarvisStatus = document.getElementById('jarvisStatus');
  const endpointCandidates = normalizeEndpoints(window.TUTOR_IA_ENDPOINTS || DEFAULT_ENDPOINTS);

  let activeTutorEndpoint = '';
  let adminSystemStatusVisible = false;
  let tutorIAEnabled = readTutorIaPreference(true);
  let tutorConnectionStatus = 'UNKNOWN';
  let tutorConnectionLabel = 'Sin verificar';
  let smartSearchEnabled = false;
  let deepThinkingEnabled = false;
  let selectedFiles = [];
  let isSubmitting = false;
  let jarvisSupported = false;
  let jarvisAssistant = null;
  let chats = [];
  let activeChatId = '';
  let currentSessionId = '';
  let activeStorageScope = '';
  let authChecked = false;
  let appInitialized = false;
  let historyLoaded = false;
  let isHydrating = true;

  window.tutorIAEnabled = tutorIAEnabled;
  window.smartSearchEnabled = smartSearchEnabled;
  window.deepThinkingEnabled = deepThinkingEnabled;

  function normalizeEndpoints(endpoints) {
    return [...new Set(endpoints.filter(Boolean).map(endpoint => endpoint.replace(/\/$/, '')))];
  }

  function endpointBaseUrl(endpoint) {
    try {
      const url = new URL(endpoint);
      return `${url.protocol}//${url.hostname}${url.port ? `:${url.port}` : ''}`;
    } catch (error) {
      return BRIDGE_URL;
    }
  }

  function endpointHealthUrls(endpoint) {
    const base = endpointBaseUrl(endpoint);
    return [
      `${base}/health`,
      `${base}/status`,
      `${base}/api/health`,
      `${base}/api/status`,
      `${base}/api/unified-brain/health`,
      `${base}/api/unified-brain/status`
    ];
  }

  function ragHealthUrl() {
    return `${BRIDGE_URL}/api/health`;
  }

  function adminStatusUrl() {
    return `${BRIDGE_URL}/api/admin/system-status`;
  }

  function endpointHostKey(endpoint) {
    try {
      const url = new URL(endpoint);
      return `${url.protocol}//${url.hostname}${url.port ? `:${url.port}` : ''}`;
    } catch (error) {
      return endpoint;
    }
  }

  function normalizeHealthPayload(data) {
    const brain = data && typeof data.brain === 'object' ? data.brain : {};
    const models = data && typeof data.models === 'object' ? data.models : {};
    const model = data.model || brain.active_model || models.active_model || '';
    const fragments = Number(data.fragments || brain.local_sources || brain.fragments || 0);
    const obsidian = data.obsidian && typeof data.obsidian === 'object' ? data.obsidian : {};
    const agency = data.agency && typeof data.agency === 'object' ? data.agency : {};
    const jarvis = data.jarvis && typeof data.jarvis === 'object' ? data.jarvis : {};
    const anthropic = data.anthropic || brain.anthropic || {};
    const anthropicConfigured = Boolean(
      anthropic.configured ||
      anthropic.connected ||
      anthropic.available ||
      data.anthropic_configured
    );

    return {
      ok: Boolean(data.ok || data.success || Object.keys(brain).length),
      fragments,
      obsidianNotes: Number(obsidian.notes || brain.obsidian_notes || 0),
      agencyAgents: Number(agency.count || brain.agency_specialists || 0),
      jarvisProfiles: Number(jarvis.detected_profiles || brain.detected_profiles || 0),
      tutorConnected: Boolean(data.tutor_ia_connected || brain.openjarvis || fragments),
      model,
      root: data.tutor_ia_root || data.root_dir || brain.root || '',
      mode: brain.mode || data.mode || 'local-first',
      anthropicConfigured
    };
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function createId() {
    return `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function createChat() {
    const createdAt = nowIso();
    return {
      id: createId(),
      title: 'Nuevo chat',
      createdAt,
      updatedAt: createdAt,
      messages: []
    };
  }

  function flowLog(event, detail = {}) {
    if (!window.APP_CONFIG?.DEBUG_APP_FLOW) return;
    console.debug('[JAH AI flow]', event, {
      authChecked,
      appInitialized,
      historyLoaded,
      isHydrating,
      activeStorageScope,
      ...detail
    });
  }

  function getAuthStorageScope() {
    const context = getAuthContext();
    const user = context.user || {};
    const rawKey = user.id || user.email || '';
    if (!context.loggedIn || !rawKey) return 'guest';
    return `user:${String(rawKey).trim().toLowerCase()}`;
  }

  function scopedStorageKey(base, scope = activeStorageScope) {
    return scope && scope !== 'guest'
      ? `${base}:${scope}`
      : base;
  }

  function readStorageValue(key, fallback = '') {
    try {
      return localStorage.getItem(key) || fallback;
    } catch (error) {
      return fallback;
    }
  }

  function writeStorageValue(key, value) {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      return false;
    }
  }

  function readTutorIaPreference(fallback = true) {
    try {
      const stored = localStorage.getItem(TUTOR_IA_ENABLED_KEY);
      if (stored === 'true') return true;
      if (stored === 'false') return false;
    } catch (error) {
      return fallback;
    }
    return fallback;
  }

  function hasTutorIaPreference() {
    try {
      const stored = localStorage.getItem(TUTOR_IA_ENABLED_KEY);
      return stored === 'true' || stored === 'false';
    } catch (error) {
      return false;
    }
  }

  function persistTutorIaPreference(enabled) {
    return writeStorageValue(TUTOR_IA_ENABLED_KEY, String(Boolean(enabled)));
  }

  function loadChats() {
    try {
      const scopedKey = scopedStorageKey(STORAGE_KEY);
      let raw = readStorageValue(scopedKey);
      if (!raw) {
        raw = readStorageValue(STORAGE_KEY) || '[]';
        if (activeStorageScope && activeStorageScope !== 'guest' && raw !== '[]') {
          writeStorageValue(scopedKey, raw);
        }
      }
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.filter(chat => chat && chat.id) : [];
    } catch (error) {
      return [];
    }
  }

  function loadActiveChatId() {
    try {
      const scopedKey = scopedStorageKey(ACTIVE_CHAT_KEY);
      let value = readStorageValue(scopedKey);
      if (!value) {
        value = readStorageValue(ACTIVE_CHAT_KEY) || '';
        if (activeStorageScope && activeStorageScope !== 'guest' && value) {
          writeStorageValue(scopedKey, value);
        }
      }
      return value;
    } catch (error) {
      return '';
    }
  }

  function loadOrCreateSessionId() {
    try {
      const sessionKey = scopedStorageKey(SESSION_KEY);
      const scopedExisting = readStorageValue(sessionKey);
      const existing = scopedExisting || readStorageValue(SESSION_KEY);
      if (!scopedExisting && existing && activeStorageScope && activeStorageScope !== 'guest') {
        writeStorageValue(sessionKey, existing);
      }
      if (existing) return existing;
      const nextId = window.crypto && typeof window.crypto.randomUUID === 'function'
        ? window.crypto.randomUUID()
        : createId();
      writeStorageValue(sessionKey, nextId);
      return nextId;
    } catch (error) {
      return createId();
    }
  }

  function persist() {
    try {
      if (!shouldPersistChatHistory()) {
        localStorage.removeItem(scopedStorageKey(STORAGE_KEY));
        writeStorageValue(scopedStorageKey(ACTIVE_CHAT_KEY), activeChatId);
        return;
      }
      writeStorageValue(scopedStorageKey(STORAGE_KEY), JSON.stringify(chats));
      writeStorageValue(scopedStorageKey(ACTIVE_CHAT_KEY), activeChatId);
    } catch (error) {
      setBrainStatus('error', 'No se pudo guardar historial');
    }
  }

  function persistActiveChat() {
    try {
      writeStorageValue(scopedStorageKey(ACTIVE_CHAT_KEY), activeChatId);
    } catch (error) {
      return false;
    }
    return true;
  }

  function getAuthContext() {
    if (!window.JAHAuth || typeof window.JAHAuth.getContext !== 'function') {
      return { loggedIn: false, user: null, preferences: {} };
    }
    return window.JAHAuth.getContext();
  }

  function getAuthPreferences() {
    const context = getAuthContext();
    return context.preferences || {};
  }

  function shouldPersistChatHistory() {
    const preferences = getAuthPreferences();
    return preferences.chat_history_enabled !== false;
  }

  function initializeChatState(reason = 'initial') {
    const nextScope = getAuthStorageScope();
    if (historyLoaded && nextScope === activeStorageScope) {
      flowLog('history-skip', { reason, nextScope });
      return;
    }

    activeStorageScope = nextScope;
    chats = loadChats();
    activeChatId = loadActiveChatId();
    currentSessionId = loadOrCreateSessionId();

    if (!chats.length) {
      const initialChat = createChat();
      chats = [initialChat];
      activeChatId = initialChat.id;
      persist();
    }

    if (!chats.some(chat => chat.id === activeChatId)) {
      activeChatId = chats[0].id;
      persistActiveChat();
    }

    sortChats();
    historyLoaded = true;
    flowLog('history-loaded', {
      reason,
      chatCount: chats.length,
      activeChatId
    });
  }

  function completeAppHydration(reason = 'auth-ready') {
    authChecked = true;
    initializeChatState(reason);
    appInitialized = true;
    isHydrating = false;
    renderChat();
    refreshAdminTechnicalState();
    flowLog('app-ready', { reason });
  }

  function waitForAuthBeforeRender() {
    const authApi = window.JAHAuth;
    if (!authApi || typeof authApi.isReady !== 'function') {
      completeAppHydration('auth-api-unavailable');
      return;
    }
    if (authApi.isReady()) {
      completeAppHydration('auth-already-ready');
      return;
    }
    window.addEventListener('jah-auth-ready', () => {
      completeAppHydration('auth-ready-event');
    }, { once: true });
  }

  function syncAssistantPreferences(patch) {
    if (!window.JAHAuth || typeof window.JAHAuth.savePreferences !== 'function') return;
    window.JAHAuth.savePreferences(patch).catch(() => {
      setBrainStatus('offline', 'Preferencias guardadas localmente');
    });
  }

  function getActiveChat() {
    return chats.find(chat => chat.id === activeChatId) || chats[0];
  }

  function setBrainStatus(state, text) {
    if (!brainStatus || !brainStatusText) return;
    brainStatus.dataset.state = state;
    brainStatusText.textContent = text;
  }

  function tutorConnectionStateLabel(status = tutorConnectionStatus) {
    const normalized = String(status || 'UNKNOWN').toUpperCase();
    if (normalized === 'CONNECTED') return 'Conectado';
    if (normalized === 'RECOVERING') return 'Recuperando conexion';
    if (normalized === 'BACKEND_UNAVAILABLE') return 'Sin conexion';
    if (normalized === 'DISCONNECTED') return 'Sin conexion';
    if (normalized === 'DEGRADED') return 'Degradado';
    return 'Sin verificar';
  }

  function tutorConnectionUiState(status = tutorConnectionStatus) {
    const normalized = String(status || 'UNKNOWN').toUpperCase();
    if (!tutorIAEnabled) return 'offline';
    if (normalized === 'CONNECTED') return 'ready';
    if (normalized === 'RECOVERING' || normalized === 'UNKNOWN') return 'checking';
    return 'offline';
  }

  function updateTutorButtonState() {
    if (!tutorIABtn) return;
    tutorIABtn.classList.toggle('is-active', tutorIAEnabled);
    tutorIABtn.setAttribute('aria-pressed', String(tutorIAEnabled));
    tutorIABtn.dataset.preference = tutorIAEnabled ? 'enabled' : 'disabled';
    tutorIABtn.dataset.connection = tutorConnectionStatus;
    tutorIABtn.title = tutorIAEnabled
      ? `Cerebro tutor_ia: Activado · ${tutorConnectionLabel}`
      : 'Cerebro tutor_ia: Desactivado';
  }

  function renderTutorTechnicalStatus() {
    updateTutorButtonState();
    if (!adminSystemStatusVisible) return;
    if (!tutorIAEnabled) {
      setBrainStatus('offline', 'Cerebro tutor_ia: Desactivado');
      return;
    }
    setBrainStatus(
      tutorConnectionUiState(),
      `Cerebro tutor_ia: Activado · ${tutorConnectionLabel}`
    );
  }

  function setTutorConnectionStatus(status, label = '') {
    tutorConnectionStatus = String(status || 'UNKNOWN').toUpperCase();
    tutorConnectionLabel = label || tutorConnectionStateLabel(tutorConnectionStatus);
    renderTutorTechnicalStatus();
  }

  function isAdminUser() {
    const authContext = getAuthContext();
    return Boolean(
      authContext.isAdmin
      || authContext.user?.is_admin === true
      || authContext.user?.isAdmin === true
    );
  }

  function setAdminTechnicalVisibility(visible) {
    adminSystemStatusVisible = Boolean(visible);
    adminOnlyElements.forEach(element => {
      element.hidden = !adminSystemStatusVisible;
      if (element === quickContextCard) {
        element.setAttribute('aria-hidden', String(!adminSystemStatusVisible));
      }
    });
    renderTutorTechnicalStatus();
  }

  function refreshAdminTechnicalState() {
    const visible = isAdminUser();
    setAdminTechnicalVisibility(visible);
    if (visible && tutorIAEnabled) detectTutorBrain();
  }

  async function fetchWithTimeout(url, options = {}, timeoutMs = 12000) {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      window.clearTimeout(timeout);
    }
  }

  async function detectTutorBrain() {
    if (!adminSystemStatusVisible) return;
    if (!tutorIAEnabled) {
      setTutorConnectionStatus('UNKNOWN', 'Desactivado');
      return;
    }
    if (!BRIDGE_URL) {
      setTutorConnectionStatus('BACKEND_UNAVAILABLE', 'Sin conexion');
      return;
    }
    if (!endpointCandidates.length) {
      setTutorConnectionStatus('BACKEND_UNAVAILABLE', 'Sin endpoint');
      return;
    }

    setTutorConnectionStatus('RECOVERING', 'Recuperando conexion');

    try {
      const authHeaders = window.JAHAuth && typeof window.JAHAuth.getAuthHeaders === 'function'
        ? window.JAHAuth.getAuthHeaders()
        : {};
      const response = await fetchWithTimeout(adminStatusUrl(), {
        method: 'GET',
        headers: authHeaders
      }, 5000);

      if (response.status === 401 || response.status === 403) {
        setAdminTechnicalVisibility(false);
        return;
      }
      if (!response.ok) {
        setTutorConnectionStatus('BACKEND_UNAVAILABLE', 'Sin conexion');
        return;
      }

      const data = await response.json();
      activeTutorEndpoint = endpointCandidates[0] || CHAT_ENDPOINT;
      const tutorStatus = String(data.tutor_ia_status || data.tutor_status || 'DISCONNECTED').toUpperCase();
      const label = tutorStatus === 'CONNECTED'
        ? 'Conectado'
        : tutorStatus === 'RECOVERING'
          ? 'Recuperando conexion'
          : tutorStatus === 'DEGRADED'
            ? 'Degradado'
            : 'Sin conexion';
      setTutorConnectionStatus(tutorStatus, label);
    } catch (error) {
      setTutorConnectionStatus('BACKEND_UNAVAILABLE', 'Sin conexion');
    }
  }

  function buildChatFormData(question, chatId, source = 'typed_chat') {
    const authContext = getAuthContext();
    const preferences = authContext.preferences || {};
    const formData = new FormData();
    formData.append('message', question);
    formData.append('question', question);
    formData.append('mode', DEFAULT_MODE);
    formData.append('tutorIA', String(tutorIAEnabled));
    formData.append('smartSearch', String(smartSearchEnabled));
    formData.append('session_id', chatId);
    formData.append('chat_id', chatId);
    formData.append('client_context_summary', buildClientContextSummary(getActiveChat()));
    formData.append('client', 'abraham-programming-assistant');
    formData.append('source', source);
    formData.append('input_source', source);
    if (authContext.user) {
      formData.append('user_id', String(authContext.user.id || ''));
      formData.append('user_email', authContext.user.email || '');
      formData.append('user_name', authContext.user.name || '');
    }
    if (Object.keys(preferences).length) {
      formData.append('user_preferences', JSON.stringify(preferences));
      formData.append('response_style', preferences.response_style || '');
      formData.append('assistant_preference', preferences.assistant_preference || '');
      formData.append('visible_name', preferences.visible_name || '');
      formData.append('direct_answers', String(Boolean(preferences.direct_answers)));
      formData.append('chat_history_enabled', String(preferences.chat_history_enabled !== false));
    }
    formData.append('response_profile', 'web_fast');
    formData.append('local_first', 'true');
    formData.append('fast_mode', String(!deepThinkingEnabled));
    formData.append('deep_thinking', String(deepThinkingEnabled));
    formData.append('bridge_api', 'true');
    formData.append('bridge_api_url', BRIDGE_URL);
    formData.append('anthropic', 'true');
    if (BRAIN_ROOT) {
      formData.append('brain_root', BRAIN_ROOT);
    }
    formData.append('include_obsidian', String(tutorIAEnabled));
    formData.append('agency_enabled', String(tutorIAEnabled));
    formData.append('jarvis_profile', 'unified');
    formData.append('k', '4');
    formData.append('top_k', '1');
    formData.append('obsidian_top_k', '1');
    formData.append('show_sources', 'false');
    if (PROJECT_PATH) {
      formData.append('project_path', PROJECT_PATH);
      formData.append('workspace_path', PROJECT_PATH);
    }
    selectedFiles.forEach(file => formData.append('files', file, file.name));
    return formData;
  }

  function compactForContext(text, maxChars = 360) {
    const clean = String(text || '').replace(/\s+/g, ' ').trim();
    return clean.length > maxChars ? `${clean.slice(0, maxChars - 1).trim()}...` : clean;
  }

  function buildClientContextSummary(chat) {
    if (!chat || !Array.isArray(chat.messages) || !chat.messages.length) return '';
    const completedMessages = chat.messages
      .filter(message => message && !message.loading && message.content)
      .slice(-CLIENT_CONTEXT_TURNS * 2);
    const lines = completedMessages.map(message => {
      const role = message.role === 'user' ? 'Usuario' : 'JAH AI';
      return `${role}: ${compactForContext(message.content, message.role === 'user' ? 260 : 420)}`;
    });
    return compactForContext(lines.join('\n'), CLIENT_CONTEXT_MAX_CHARS);
  }

  async function verifyBackendHealth() {
    if (!BRIDGE_URL) return false;
    try {
      const response = await fetchWithTimeout(ragHealthUrl(), { method: 'GET' }, 4500);
      if (!response.ok) return false;
      const data = await response.json();
      return Boolean(data.ok || data.success);
    } catch (error) {
      return false;
    }
  }

  function backendConnectionError() {
    const target = BRIDGE_URL || 'API_BASE_URL';
    const error = new Error(`No se pudo conectar con el backend de JAH AI. Verifica que el servicio este activo o que ${target} este configurado correctamente.`);
    error.code = 'BACKEND_CONNECTION';
    return error;
  }

  function chatLoadingText() {
    if (smartSearchEnabled) return 'Buscando información actualizada...';
    if (tutorIAEnabled || deepThinkingEnabled) return 'Consultando cerebro tutor_ia...';
    return 'Pensando...';
  }

  function buildChatPayload(question, chatId, source = 'typed_chat') {
    const authContext = getAuthContext();
    const preferences = authContext.preferences || {};
    const chat = getActiveChat();
    return {
      message: question,
      question,
      mode: DEFAULT_MODE,
      use_rag: Boolean(tutorIAEnabled),
      use_web: Boolean(smartSearchEnabled),
      smartSearch: Boolean(smartSearchEnabled),
      smart_search: Boolean(smartSearchEnabled),
      deep_thinking: Boolean(tutorIAEnabled || deepThinkingEnabled),
      use_jarvis: source === 'jarvis_voice',
      session_id: currentSessionId || chatId,
      chat_id: chatId,
      client: 'abraham-programming-assistant',
      source,
      input_source: source,
      response_profile: tutorIAEnabled || deepThinkingEnabled ? 'balanced' : 'web_fast',
      local_first: true,
      fast_mode: !(tutorIAEnabled || deepThinkingEnabled),
      bridge_api: true,
      bridge_api_url: BRIDGE_URL,
      anthropic: true,
      brain_root: BRAIN_ROOT,
      project_path: PROJECT_PATH,
      workspace_path: PROJECT_PATH,
      user_id: authContext.user ? String(authContext.user.id || '') : '',
      user_email: authContext.user ? authContext.user.email || '' : '',
      user_name: authContext.user ? authContext.user.name || '' : '',
      user_preferences: preferences,
      client_context_summary: buildClientContextSummary(chat),
      response_style: preferences.response_style || '',
      assistant_preference: preferences.assistant_preference || '',
      visible_name: preferences.visible_name || '',
      direct_answers: Boolean(preferences.direct_answers),
      chat_history_enabled: preferences.chat_history_enabled !== false,
      show_sources: Boolean(tutorIAEnabled),
      k: 4,
      top_k: 3,
      obsidian_top_k: 2,
      include_obsidian: Boolean(tutorIAEnabled),
      agency_enabled: Boolean(tutorIAEnabled),
      jarvis_profile: 'unified'
    };
  }

  async function askBackendChat(question, chatId, source = 'typed_chat') {
    if (adminSystemStatusVisible) setBrainStatus('checking', chatLoadingText());
    const healthy = await verifyBackendHealth();
    if (!healthy) {
      if (adminSystemStatusVisible) setBrainStatus('error', 'Backend tutor_ia no disponible');
      throw backendConnectionError();
    }

    const authHeaders = window.JAHAuth && typeof window.JAHAuth.getAuthHeaders === 'function'
      ? window.JAHAuth.getAuthHeaders()
      : {};
    const response = await fetchWithTimeout(CHAT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders
      },
      body: JSON.stringify(buildChatPayload(question, chatId, source))
    }, CHAT_TIMEOUT_MS);

    let data = {};
    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }

    if (!response.ok) {
      throw new Error(data.detail || data.error || `HTTP ${response.status}`);
    }
    if (data && data.ok === false) {
      throw new Error(data.error || data.answer || 'El cerebro tutor_ia respondió con error.');
    }

    const sourcesCount = Array.isArray(data.sources) ? data.sources.length : 0;
    if (adminSystemStatusVisible) {
      setBrainStatus('ready', sourcesCount ? `Respuesta recibida - ${sourcesCount} fuentes` : 'Respuesta recibida');
    }
    return {
      ...data,
      show_sources: sourcesCount > 0,
      brain_parts: data.brain_parts || (tutorIAEnabled ? ['tutor_ia'] : ['chat']),
      usedTutorIA: true
    };
  }

  async function askTutorBrain(question, chatId, source = 'typed_chat') {
    return askBackendChat(question, chatId, source);
  }

  function escapeHtml(text) {
    return String(text || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatPlainText(text) {
    const escaped = escapeHtml(text);
    const withLinks = escaped.replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );
    return withLinks.replace(/\n/g, '<br>');
  }

  function renderCodeBlock(fenceContent) {
    let code = String(fenceContent || '').replace(/^\n/, '').replace(/\n$/, '');
    let language = 'cÃ³digo';
    const firstBreak = code.indexOf('\n');

    if (firstBreak > -1) {
      const firstLine = code.slice(0, firstBreak).trim();
      if (/^[a-zA-Z0-9_#+.-]{1,24}$/.test(firstLine)) {
        language = firstLine;
        code = code.slice(firstBreak + 1);
      }
    }

    return `
      <div class="code-block">
        <div class="code-header">
          <span>${escapeHtml(language)}</span>
          <button class="copy-code-btn" type="button">Copiar</button>
        </div>
        <pre><code>${escapeHtml(code)}</code></pre>
      </div>
    `;
  }

  function formatAssistantText(text) {
    const raw = String(text || '');
    const fencePattern = /```([\s\S]*?)```/g;
    let html = '';
    let lastIndex = 0;
    let match = fencePattern.exec(raw);

    while (match) {
      html += formatPlainText(raw.slice(lastIndex, match.index));
      html += renderCodeBlock(match[1]);
      lastIndex = match.index + match[0].length;
      match = fencePattern.exec(raw);
    }

    html += formatPlainText(raw.slice(lastIndex));
    return html;
  }

  function sourceTitle(source) {
    const metadata = source && source.metadata ? source.metadata : {};
    return source.title || source.file || metadata.title || metadata.source || source.url || '';
  }

  function sourceChunk(source) {
    return source.chunk || source.snippet || source.text || '';
  }

  function sourceScore(source) {
    const value = source.score ?? source.relevance ?? '';
    if (value === '' || value === null || value === undefined) return '';
    const number = Number(value);
    if (Number.isNaN(number)) return String(value);
    return number <= 1 ? number.toFixed(2) : String(number);
  }

  function renderSourceSummary(sources, showSources = false) {
    if (!showSources) return '';
    const cleanSources = (sources || [])
      .filter(Boolean)
      .slice(0, 4);
    if (!cleanSources.length) return '';

    const sourceItems = cleanSources.map(source => {
      const title = sourceTitle(source) || 'Documento';
      const chunk = sourceChunk(source);
      const score = sourceScore(source);
      const url = source.url || (source.metadata && source.metadata.url) || '';
      return `
        <li class="message-source-item">
          <strong>${escapeHtml(title)}</strong>
          ${score ? `<span>Relevancia: ${escapeHtml(score)}</span>` : ''}
          ${url ? `<span>${escapeHtml(url)}</span>` : ''}
          ${chunk ? `<p>${escapeHtml(chunk)}</p>` : ''}
        </li>
      `;
    }).join('');

    return `
      <div class="message-sources">
        <strong>Fuentes usadas:</strong>
        <ul class="message-source-list">${sourceItems}</ul>
      </div>
    `;
  }

  function fileMeta(file) {
    return {
      name: file.name,
      size: file.size,
      type: file.type || 'archivo'
    };
  }

  function renderUploadedFileSummary(files) {
    if (!Array.isArray(files) || !files.length) return '';
    const names = files
      .map(file => file && file.name ? file.name : '')
      .filter(Boolean)
      .slice(0, 5);
    if (!names.length) return '';
    return `<div class="message-sources"><strong>Adjuntos:</strong> ${names.map(escapeHtml).join(' - ')}</div>`;
  }

  function titleFromQuestion(question) {
    const clean = String(question || '').replace(/\s+/g, ' ').trim();
    if (!clean) return 'Nuevo chat';
    return clean.length > 42 ? `${clean.slice(0, 41).trim()}...` : clean;
  }

  function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return new Intl.DateTimeFormat('es-NI', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  }

  function addMessageToChat(chatId, message) {
    const chat = chats.find(item => item.id === chatId);
    if (!chat) return;
    chat.messages.push({
      id: createId(),
      createdAt: nowIso(),
      ...message
    });
    chat.updatedAt = nowIso();
    if (chat.title === 'Nuevo chat' && message.role === 'user') {
      chat.title = titleFromQuestion(message.content);
    }
    sortChats();
    persist();
  }

  function updateMessageInChat(chatId, messageId, patch) {
    const chat = chats.find(item => item.id === chatId);
    if (!chat) return;
    const message = chat.messages.find(item => item.id === messageId);
    if (!message) return;
    Object.assign(message, patch);
    chat.updatedAt = nowIso();
    sortChats();
    persist();
  }

  function sortChats() {
    chats.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
  }

  function renderChat() {
    if (isHydrating || !historyLoaded) {
      flowLog('render-deferred');
      return;
    }
    const chat = getActiveChat();
    if (!chat) return;

    activeChatLabel.textContent = chat.title || 'Nuevo chat';
    coachMessages.innerHTML = '';
    chatMain.classList.toggle('is-empty', !chat.messages.length);

    if (!chat.messages.length) {
      coachMessages.appendChild(emptyChatState);
    } else {
      chat.messages.forEach(message => {
        coachMessages.appendChild(createMessageElement(message));
      });
    }

    coachMessages.scrollTop = coachMessages.scrollHeight;
    renderHistory();
  }

  function createMessageElement(message) {
    const row = document.createElement('div');
    row.className = `message-row ${message.role === 'user' ? 'user' : 'assistant'}`;
    row.dataset.messageId = message.id;

    const bubble = document.createElement('div');
    bubble.className = `message-bubble${message.loading ? ' loading' : ''}`;
    bubble.innerHTML = [
      formatAssistantText(message.content),
      renderUploadedFileSummary(message.uploadedFiles),
      renderSourceSummary(message.sources, message.showSources)
    ].join('');
    row.appendChild(bubble);
    return row;
  }

  function updateRenderedMessage(messageId, content, options = {}) {
    const row = coachMessages.querySelector(`[data-message-id="${messageId}"]`);
    if (!row) return;
    const bubble = row.querySelector('.message-bubble');
    if (!bubble) return;
    bubble.classList.toggle('loading', Boolean(options.loading));
    bubble.innerHTML = [
      formatAssistantText(content),
      renderUploadedFileSummary(options.uploadedFiles),
      renderSourceSummary(options.sources, options.showSources)
    ].join('');
    coachMessages.scrollTop = coachMessages.scrollHeight;
  }

  function renderHistory() {
    const query = (chatSearchInput.value || '').trim().toLowerCase();
    const filtered = chats.filter(chat => {
      const haystack = [
        chat.title,
        ...chat.messages.map(message => message.content)
      ].join(' ').toLowerCase();
      return !query || haystack.includes(query);
    });

    chatHistoryList.innerHTML = '';
    if (!filtered.length) {
      const empty = document.createElement('div');
      empty.className = 'empty-history';
      empty.textContent = query ? 'No encontrÃ© chats con esa bÃºsqueda.' : 'Tus chats aparecerÃ¡n aquÃ­.';
      chatHistoryList.appendChild(empty);
      return;
    }

    filtered.forEach(chat => {
      const item = document.createElement('button');
      item.className = `history-item${chat.id === activeChatId ? ' active' : ''}`;
      item.type = 'button';
      item.innerHTML = `
        <span class="history-copy">
          <span class="history-title">${escapeHtml(chat.title || 'Nuevo chat')}</span>
          <span class="history-date">${escapeHtml(formatDate(chat.updatedAt))}</span>
        </span>
        <span class="delete-chat-btn" role="button" aria-label="Eliminar chat">
          <i class="fas fa-trash" aria-hidden="true"></i>
        </span>
      `;

      item.addEventListener('click', event => {
        if (event.target.closest('.delete-chat-btn')) {
          deleteChat(chat.id);
          return;
        }
        activeChatId = chat.id;
        persistActiveChat();
        renderChat();
        closeSidebar();
      });

      chatHistoryList.appendChild(item);
    });
  }

  function startNewChat() {
    const current = getActiveChat();
    if (current && !current.messages.length) {
      activeChatId = current.id;
    } else {
      const chat = createChat();
      chats.unshift(chat);
      activeChatId = chat.id;
    }
    persist();
    renderChat();
    closeSidebar();
    coachInput.focus();
  }

  function deleteChat(chatId) {
    chats = chats.filter(chat => chat.id !== chatId);
    if (!chats.length) {
      chats = [createChat()];
    }
    if (!chats.some(chat => chat.id === activeChatId)) {
      activeChatId = chats[0].id;
    }
    persist();
    renderChat();
  }

  function clearHistory() {
    chats = [createChat()];
    activeChatId = chats[0].id;
    persist();
    renderChat();
    coachInput.focus();
  }

  function setComposerLoading(isLoading) {
    if (sendButton) sendButton.disabled = isLoading;
    if (coachInput) coachInput.disabled = isLoading;
    if (fileInput) fileInput.disabled = isLoading;
    if (tutorIABtn) tutorIABtn.disabled = isLoading;
    if (smartSearchBtn) smartSearchBtn.disabled = isLoading;
    if (jarvisVoiceBtn) {
      jarvisVoiceBtn.disabled = isLoading || !jarvisSupported;
      jarvisVoiceBtn.classList.toggle('jarvis-disabled', !jarvisSupported);
      jarvisVoiceBtn.setAttribute('aria-disabled', String(isLoading || !jarvisSupported));
    }
  }

  function fallbackAnswer(error, filesForMessage = []) {
    const fileNames = Array.isArray(filesForMessage)
      ? filesForMessage.map(file => file.name).filter(Boolean)
      : [];
    const fileStatus = fileNames.length
      ? `Archivo recibido por la interfaz: ${fileNames.join(', ')}. El backend debe leerlo antes de llamar al modelo; vuelve a enviar la misma pregunta si el proceso local estaba ocupado.`
      : 'No habia archivos adjuntos en este mensaje.';

    if (error && error.name === 'AbortError') {
      return `El modelo local/Ollama no respondio dentro de ${Math.round(CHAT_TIMEOUT_MS / 1000)} segundos. ${fileStatus}\n\nPosibles soluciones:\n- Revisa que Ollama no tenga otra generacion en curso.\n- Usa un modelo ligero como llama3.2:1b para la interfaz web.\n- Reinicia el puente TUTOR_IA si el proceso quedo ocupado.\n- Si el archivo es grande, intenta una peticion mas concreta sobre una parte del archivo.`;
    }
    if (error && error.code === 'BACKEND_CONNECTION') {
      return error.message;
    }
    const detail = error && error.message ? ` Detalle: ${error.message}` : '';
    return `No pude completar la consulta con TUTOR_IA. ${fileStatus}${detail} Verifica el puente local en ${BRIDGE_URL}/health o ${BRIDGE_URL}/api/health.`;
  }

  function autosizeInput() {
    coachInput.style.height = 'auto';
    coachInput.style.height = `${Math.min(coachInput.scrollHeight, 220)}px`;
  }

  function openSidebar() {
    chatSidebar.classList.add('open');
    sidebarBackdrop.hidden = false;
  }

  function closeSidebar() {
    chatSidebar.classList.remove('open');
    sidebarBackdrop.hidden = true;
  }

  function setTutorIA(enabled, options = {}) {
    tutorIAEnabled = Boolean(enabled);
    window.tutorIAEnabled = tutorIAEnabled;
    if (options.persist !== false) {
      persistTutorIaPreference(tutorIAEnabled);
    }
    updateTutorButtonState();
    if (!tutorIAEnabled) {
      renderTutorTechnicalStatus();
    } else if (options.checkConnection !== false && adminSystemStatusVisible) {
      detectTutorBrain();
    } else {
      renderTutorTechnicalStatus();
    }
    if (options.sync !== false) {
      syncAssistantPreferences({
        use_rag: tutorIAEnabled,
        deep_thinking: Boolean(tutorIAEnabled || deepThinkingEnabled)
      });
    }
  }

  function setSmartSearch(enabled, options = {}) {
    smartSearchEnabled = Boolean(enabled);
    window.smartSearchEnabled = smartSearchEnabled;
    smartSearchBtn.classList.toggle('is-active', smartSearchEnabled);
    smartSearchBtn.setAttribute('aria-pressed', String(smartSearchEnabled));
    if (options.sync !== false) {
      syncAssistantPreferences({ use_web: smartSearchEnabled });
    }
  }

  function extensionForFile(file) {
    return String(file.name || '').split('.').pop().toLowerCase();
  }

  function isAllowedFile(file) {
    return ALLOWED_FILE_EXTENSIONS.has(extensionForFile(file));
  }

  function fileKey(file) {
    return `${file.name}-${file.size}-${file.lastModified}`;
  }

  function setSelectedFiles(files) {
    const existingKeys = new Set(selectedFiles.map(fileKey));
    Array.from(files || []).forEach(file => {
      if (!isAllowedFile(file)) return;
      const key = fileKey(file);
      if (!existingKeys.has(key)) {
        selectedFiles.push(file);
        existingKeys.add(key);
      }
    });
    renderAttachments();
  }

  function removeSelectedFile(index) {
    selectedFiles.splice(index, 1);
    renderAttachments();
  }

  function renderAttachments() {
    if (!attachmentPreview) return;
    attachmentPreview.hidden = selectedFiles.length === 0;
    attachmentPreview.innerHTML = selectedFiles.map((file, index) => `
      <span class="attachment-pill">
        <i class="fas fa-file" aria-hidden="true"></i>
        <span>${escapeHtml(file.name)}</span>
        <button class="remove-attachment" type="button" data-file-index="${index}" aria-label="Quitar ${escapeHtml(file.name)}">
          <i class="fas fa-times" aria-hidden="true"></i>
        </button>
      </span>
    `).join('');
    if (fileInput) fileInput.value = '';
  }

  async function uploadSelectedFiles(files) {
    const uploadFiles = Array.from(files || []).filter(isAllowedFile);
    if (!uploadFiles.length) return;
    if (!UPLOAD_ENDPOINT) {
      addMessageToChat(activeChatId, {
        role: 'assistant',
        content: 'El backend de archivos no esta configurado. Define API_BASE_URL o ejecuta el backend local antes de subir archivos.'
      });
      renderChat();
      return;
    }

    if (adminSystemStatusVisible) setBrainStatus('checking', 'Subiendo archivo al cerebro tutor_ia...');
    let uploaded = 0;
    let failed = 0;

    for (const file of uploadFiles) {
      const formData = new FormData();
      formData.append('file', file, file.name);
      const authHeaders = window.JAHAuth && typeof window.JAHAuth.getAuthHeaders === 'function'
        ? window.JAHAuth.getAuthHeaders()
        : {};
      try {
        const response = await fetchWithTimeout(UPLOAD_ENDPOINT, {
          method: 'POST',
          headers: {
            ...authHeaders,
            'X-Session-Id': currentSessionId
          },
          body: formData
        }, 60000);
        if (!response.ok) {
          failed += 1;
          continue;
        }
        uploaded += 1;
      } catch (error) {
        failed += 1;
      }
    }

    const chatId = activeChatId;
    if (uploaded) {
      const message = uploaded === 1
        ? 'Archivo cargado correctamente al cerebro tutor_ia.'
        : `${uploaded} archivos cargados correctamente al cerebro tutor_ia.`;
      addMessageToChat(chatId, { role: 'assistant', content: message });
      if (adminSystemStatusVisible) setBrainStatus('ready', message);
    }
    if (failed) {
      const message = 'No se pudo subir el archivo. Verificá que el backend esté activo.';
      addMessageToChat(chatId, { role: 'assistant', content: message });
      if (adminSystemStatusVisible) setBrainStatus('error', 'Error al subir archivo');
    }
    renderChat();
  }

  async function sendCurrentMessage(options = {}) {
    if (isSubmitting) return false;

    const source = options.source || 'typed_chat';
    const typedQuestion = coachInput.value.trim();
    const question = typedQuestion || (selectedFiles.length ? 'Analiza los archivos adjuntos.' : '');
    if (!question) return false;

    if (jarvisAssistant && typeof jarvisAssistant.stopSpeech === 'function') {
      jarvisAssistant.stopSpeech();
    }

    isSubmitting = true;
    const filesForMessage = selectedFiles.map(fileMeta);
    const chatId = activeChatId;
    addMessageToChat(chatId, { role: 'user', content: question, uploadedFiles: filesForMessage });
    coachInput.value = '';
    autosizeInput();
    renderChat();
    setComposerLoading(true);

    const loadingMessage = {
      id: createId(),
      role: 'assistant',
      content: chatLoadingText(),
      createdAt: nowIso(),
      loading: true
    };
    const chat = chats.find(item => item.id === chatId);
    chat.messages.push(loadingMessage);
    chat.updatedAt = nowIso();
    persist();
    renderChat();

    try {
      if (source === 'jarvis_voice' && jarvisAssistant) {
        jarvisAssistant.showStatus('Jarvis procesando...', 'info', 0);
      }
      const result = await askTutorBrain(question, chatId, source);
      const answer = result.answer || result.response || 'TUTOR_IA respondiÃ³ sin texto.';
      const showSources = Boolean(result.show_sources || (Array.isArray(result.sources) && result.sources.length));
      updateMessageInChat(chatId, loadingMessage.id, {
        content: answer,
        sources: showSources ? result.sources || [] : [],
        uploadedFiles: result.uploadedFiles || [],
        showSources,
        loading: false
      });
      updateRenderedMessage(loadingMessage.id, answer, {
        sources: showSources ? result.sources || [] : [],
        uploadedFiles: result.uploadedFiles || [],
        showSources
      });
      selectedFiles = [];
      renderAttachments();

      if (source === 'jarvis_voice') {
        notifyJarvisResponse(answer, true);
      }
      return true;
    } catch (error) {
      const answer = fallbackAnswer(error, filesForMessage);
      updateMessageInChat(chatId, loadingMessage.id, {
        content: answer,
        sources: [],
        loading: false
      });
      updateRenderedMessage(loadingMessage.id, answer);

      if (source === 'jarvis_voice') {
        notifyJarvisResponse(answer, false);
      }
      return false;
    } finally {
      isSubmitting = false;
      setComposerLoading(false);
      coachInput.focus();
      renderHistory();
    }
  }

  function setDeepThinkingFromJarvis(enable) {
    const deepThinkingControl = document.getElementById('deepThinkingBtn')
      || document.querySelector('[data-action="deep-thinking"], [data-feature="deep-thinking"], .deep-thinking-btn');

    if (!deepThinkingControl) {
      deepThinkingEnabled = Boolean(enable);
      window.deepThinkingEnabled = deepThinkingEnabled;
      syncAssistantPreferences({ deep_thinking: deepThinkingEnabled });
      return true;
    }

    const isActive = deepThinkingControl.getAttribute('aria-pressed') === 'true'
      || deepThinkingControl.classList.contains('is-active')
      || deepThinkingControl.checked === true;

    if (isActive !== enable) {
      deepThinkingControl.click();
    }

    deepThinkingEnabled = Boolean(enable);
    window.deepThinkingEnabled = deepThinkingEnabled;
    syncAssistantPreferences({ deep_thinking: deepThinkingEnabled });
    return true;
  }

  function getLastAssistantText() {
    const chat = getActiveChat();
    if (!chat || !Array.isArray(chat.messages)) return '';
    const lastAssistant = [...chat.messages]
      .reverse()
      .find(message => message.role === 'assistant' && !message.loading && message.content);
    return lastAssistant ? lastAssistant.content : '';
  }

  function notifyJarvisResponse(answer, ok = true) {
    if (!jarvisAssistant) return;
    jarvisAssistant.showStatus(ok ? 'Jarvis listo.' : 'Jarvis no pudo responder. Puedes escribir tu mensaje.', ok ? 'success' : 'error');
    if (ok) {
      jarvisAssistant.speakResponse(answer);
    }
  }

  async function refreshMarkVoiceStatus(showWhenReady = false) {
    if (!jarvisAssistant) return null;
    if (!JARVIS_MARK_STATUS_ENDPOINT) return null;
    try {
      const response = await fetchWithTimeout(JARVIS_MARK_STATUS_ENDPOINT, { method: 'GET' }, 5000);
      if (!response.ok) return null;
      const data = await response.json();
      const mark = data.mark_xxxix || data;
      if (mark.launch_ready && showWhenReady) {
        jarvisAssistant.showStatus('Mark XXXIX disponible: voz Charon lista.', 'success', 5000);
      }
      if (!mark.launch_ready && showWhenReady) {
        const note = Array.isArray(mark.notes) && mark.notes.length ? mark.notes[0] : 'Mark XXXIX requiere configuración.';
        jarvisAssistant.showStatus(note, 'warning', 7000);
      }
      return mark;
    } catch (error) {
      return null;
    }
  }

  async function launchMarkVoice() {
    if (!jarvisAssistant) return false;
    if (!JARVIS_MARK_LAUNCH_ENDPOINT) return false;
    jarvisAssistant.showStatus('Preparando Mark XXXIX...', 'info', 0);
    try {
      const response = await fetchWithTimeout(JARVIS_MARK_LAUNCH_ENDPOINT, { method: 'POST' }, 10000);
      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.ok === false) {
        const note = data.message
          || data.detail
          || 'Mark XXXIX no está configurado. Se usará voz del navegador.';
        jarvisAssistant.showStatus(note, 'warning', 8000);
        return false;
      }
      jarvisAssistant.showStatus(data.already_running ? 'Mark XXXIX ya está activo.' : 'Mark XXXIX iniciado con voz Charon.', 'success', 7000);
      return true;
    } catch (error) {
      jarvisAssistant.showStatus('No se pudo iniciar Mark XXXIX. Se usará voz del navegador.', 'error', 7000);
      return false;
    }
  }

  function initJarvisIntegration() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    jarvisSupported = Boolean(SpeechRecognition);

    if (!window.JarvisAssistant) {
      if (jarvisVoiceBtn) {
        jarvisVoiceBtn.disabled = true;
        jarvisVoiceBtn.title = 'Voz no disponible en este navegador.';
      }
      if (jarvisStatus) {
        jarvisStatus.textContent = 'Tu navegador no soporta reconocimiento de voz. Probá con Google Chrome o Microsoft Edge.';
        jarvisStatus.className = 'jarvis-status warning';
      }
      return;
    }

    jarvisAssistant = window.JarvisAssistant.create({
      elements: {
        button: jarvisVoiceBtn,
        status: jarvisStatus,
        input: coachInput
      },
      config: {
        readResponses: JARVIS_READ_RESPONSES,
        stt: {
          provider: 'web-speech',
          language: 'es-NI',
          fallbackLanguage: 'es-ES',
          localProvidersReadyForPhase2: ['faster-whisper', 'vosk', 'speechrecognition']
        },
        tts: {
          provider: 'speech-synthesis',
          maxChars: 1300,
          codeNotice: 'La respuesta incluye código. Te recomiendo revisarlo en pantalla.'
        }
      },
      state: {
        isSubmitting: () => isSubmitting
      },
      callbacks: {
        autosizeInput,
        sendMessage: text => {
          syncAssistantPreferences({ jarvis_voice: true });
          coachInput.value = String(text || '').trim();
          autosizeInput();
          return sendCurrentMessage({ source: 'jarvis_voice' });
        },
        clearChat: () => {
          clearHistory();
          coachInput.value = '';
          autosizeInput();
          return true;
        },
        setSmartSearch: enabled => {
          setSmartSearch(Boolean(enabled));
          coachInput.focus();
          return true;
        },
        setDeepThinking: setDeepThinkingFromJarvis,
        launchMarkVoice,
        openFilePicker: () => {
          if (!fileInput || fileInput.disabled) return false;
          fileInput.click();
          return true;
        },
        getLastAssistantText
      }
    });
    window.jarvisAssistant = jarvisAssistant;
    refreshMarkVoiceStatus(false);
  }

  newChatBtn.addEventListener('click', startNewChat);
  clearHistoryBtn.addEventListener('click', clearHistory);
  chatSearchInput.addEventListener('input', renderHistory);
  openSidebarBtn.addEventListener('click', openSidebar);
  closeSidebarBtn.addEventListener('click', closeSidebar);
  sidebarBackdrop.addEventListener('click', closeSidebar);
  coachInput.addEventListener('input', autosizeInput);
  coachInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      coachForm.requestSubmit();
    }
  });

  tutorIABtn.addEventListener('click', () => {
    setTutorIA(!tutorIAEnabled);
    coachInput.focus();
  });

  smartSearchBtn.addEventListener('click', () => {
    setSmartSearch(!smartSearchEnabled);
    coachInput.focus();
  });

  fileInput.addEventListener('change', async event => {
    const files = Array.from(event.target.files || []);
    setSelectedFiles(files);
    await uploadSelectedFiles(files);
    coachInput.focus();
  });

  attachmentPreview.addEventListener('click', event => {
    const removeBtn = event.target.closest('.remove-attachment');
    if (!removeBtn) return;
    removeSelectedFile(Number(removeBtn.dataset.fileIndex));
    coachInput.focus();
  });

  coachMessages.addEventListener('click', async event => {
    const copyBtn = event.target.closest('.copy-code-btn');
    if (!copyBtn) return;
    const code = copyBtn.closest('.code-block')?.querySelector('code')?.textContent || '';
    if (!code) return;

    try {
      await navigator.clipboard.writeText(code);
      copyBtn.textContent = 'Copiado';
      window.setTimeout(() => {
        copyBtn.textContent = 'Copiar';
      }, 1300);
    } catch (error) {
      copyBtn.textContent = 'Error';
      window.setTimeout(() => {
        copyBtn.textContent = 'Copiar';
      }, 1300);
    }
  });

  coachForm.addEventListener('submit', async event => {
    event.preventDefault();
    await sendCurrentMessage({ source: 'typed_chat' });
  });

  window.addEventListener('jah-auth-preferences-changed', event => {
    const preferences = event.detail || {};
    if (Object.prototype.hasOwnProperty.call(preferences, 'use_rag')) {
      const preferredTutorState = hasTutorIaPreference()
        ? readTutorIaPreference(Boolean(preferences.use_rag))
        : Boolean(preferences.use_rag);
      setTutorIA(preferredTutorState, {
        sync: false,
        persist: !hasTutorIaPreference(),
        checkConnection: false
      });
    }
    if (Object.prototype.hasOwnProperty.call(preferences, 'use_web')) {
      setSmartSearch(Boolean(preferences.use_web), { sync: false });
    }
    if (Object.prototype.hasOwnProperty.call(preferences, 'deep_thinking')) {
      deepThinkingEnabled = Boolean(preferences.deep_thinking);
      window.deepThinkingEnabled = deepThinkingEnabled;
    }
  });

  window.addEventListener('jah-auth-session-changed', () => {
    initializeChatState('auth-session-changed');
    if (appInitialized) renderChat();
    refreshAdminTechnicalState();
  });

  window.addEventListener('jah-auth-login', () => {
    refreshAdminTechnicalState();
  });

  window.addEventListener('jah-auth-logout', () => {
    setAdminTechnicalVisibility(false);
    deepThinkingEnabled = false;
    window.deepThinkingEnabled = false;
    historyLoaded = false;
    initializeChatState('auth-logout');
    if (appInitialized) renderChat();
    coachInput.focus();
  });

  setTutorIA(readTutorIaPreference(true), { sync: false, persist: false, checkConnection: false });
  setSmartSearch(false, { sync: false });
  initJarvisIntegration();
  renderAttachments();
  autosizeInput();
  waitForAuthBeforeRender();
});
