const DEFAULT_ENDPOINTS = [
  'http://127.0.0.1:8787/api/chat',
  'http://127.0.0.1:8787/api/ask',
  'http://127.0.0.1:8787/ask',
  'http://localhost:8787/api/chat'
];

const STORAGE_KEY = 'tutorIaChatHistory';
const ACTIVE_CHAT_KEY = 'tutorIaActiveChatId';
const DEFAULT_MODE = 'Cerebro Unificado';
const PROJECT_PATH = window.TUTOR_IA_PROJECT_PATH || '';
const BRIDGE_URL = (window.TUTOR_IA_BRIDGE_URL || 'http://127.0.0.1:8787').replace(/\/$/, '');
const CHAT_TIMEOUT_MS = 120000;
const JARVIS_READ_RESPONSES = window.JARVIS_READ_RESPONSES === undefined
  ? true
  : window.JARVIS_READ_RESPONSES === true || window.JARVIS_READ_RESPONSES === 'true';
const JARVIS_RECOGNITION_LANGS = ['es-NI', 'es-ES'];
const JARVIS_UNSUPPORTED_MESSAGE = 'Jarvis no puede acceder al reconocimiento de voz en este navegador. Usa Google Chrome o Microsoft Edge en Windows.';
const ALLOWED_FILE_EXTENSIONS = new Set([
  'png', 'jpg', 'jpeg', 'webp', 'pdf', 'docx', 'txt', 'py', 'js', 'html', 'css', 'json', 'md', 'sql', 'cs'
]);

document.addEventListener('DOMContentLoaded', () => {
  const chatMain = document.querySelector('.chat-main');
  const coachMessages = document.getElementById('coachMessages');
  const emptyChatState = document.getElementById('emptyChatState');
  const coachForm = document.getElementById('coachForm');
  const coachInput = document.getElementById('coachInput');
  const brainStatus = document.getElementById('brainStatus');
  const brainStatusText = document.getElementById('brainStatusText');
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
  const jarvisStatusText = document.getElementById('jarvisStatusText');
  const endpointCandidates = normalizeEndpoints(window.TUTOR_IA_ENDPOINTS || DEFAULT_ENDPOINTS);

  let activeTutorEndpoint = '';
  let tutorIAEnabled = true;
  let smartSearchEnabled = false;
  let selectedFiles = [];
  let isSubmitting = false;
  let jarvisRecognition = null;
  let jarvisListening = false;
  let jarvisSupported = false;
  let jarvisLangIndex = 0;
  let jarvisStatusTimer = null;
  let chats = loadChats();
  let activeChatId = loadActiveChatId();

  window.tutorIAEnabled = tutorIAEnabled;
  window.smartSearchEnabled = smartSearchEnabled;

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

  function loadChats() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      return Array.isArray(parsed) ? parsed.filter(chat => chat && chat.id) : [];
    } catch (error) {
      return [];
    }
  }

  function loadActiveChatId() {
    try {
      return localStorage.getItem(ACTIVE_CHAT_KEY) || '';
    } catch (error) {
      return '';
    }
  }

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
      localStorage.setItem(ACTIVE_CHAT_KEY, activeChatId);
    } catch (error) {
      setBrainStatus('error', 'No se pudo guardar historial');
    }
  }

  function persistActiveChat() {
    try {
      localStorage.setItem(ACTIVE_CHAT_KEY, activeChatId);
    } catch (error) {
      return false;
    }
    return true;
  }

  function getActiveChat() {
    return chats.find(chat => chat.id === activeChatId) || chats[0];
  }

  function setBrainStatus(state, text) {
    if (!brainStatus || !brainStatusText) return;
    brainStatus.dataset.state = state;
    brainStatusText.textContent = text;
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
    if (!endpointCandidates.length) {
      setBrainStatus('offline', 'TUTOR_IA sin endpoint');
      return;
    }

    setBrainStatus('checking', 'Conectando con TUTOR_IA');

    for (const endpoint of endpointCandidates) {
      for (const healthUrl of endpointHealthUrls(endpoint)) {
        try {
          const response = await fetchWithTimeout(healthUrl, { method: 'GET' }, 3500);
          if (!response.ok) continue;
          const data = await response.json();
          const health = normalizeHealthPayload(data);
          if (!health.ok) continue;
          activeTutorEndpoint = endpoint;

          const contextParts = [`${health.fragments} fragmentos`];
          if (health.tutorConnected) contextParts.unshift('tutor_ia OK');
          if (health.obsidianNotes) contextParts.push(`${health.obsidianNotes} notas Obsidian`);
          if (health.agencyAgents) contextParts.push(`${health.agencyAgents} agentes`);
          if (health.jarvisProfiles) contextParts.push(`${health.jarvisProfiles} perfiles Jarvis`);
          if (health.anthropicConfigured) contextParts.push('Claude listo');
          const modelText = health.model ? ` - ${health.model}` : '';

          setBrainStatus('ready', `TUTOR_IA conectado - ${contextParts.join(' + ')}${modelText}`);
          return;
        } catch (error) {
          continue;
        }
      }
    }

    setBrainStatus('offline', 'TUTOR_IA sin conexion local');
  }

  function buildChatFormData(question, chatId, source = 'typed_chat') {
    const formData = new FormData();
    formData.append('message', question);
    formData.append('question', question);
    formData.append('mode', DEFAULT_MODE);
    formData.append('tutorIA', String(tutorIAEnabled));
    formData.append('smartSearch', String(smartSearchEnabled));
    formData.append('session_id', chatId);
    formData.append('client', 'abraham-programming-assistant');
    formData.append('source', source);
    formData.append('input_source', source);
    formData.append('response_profile', 'web_fast');
    formData.append('local_first', 'true');
    formData.append('fast_mode', 'true');
    formData.append('deep_thinking', 'false');
    formData.append('bridge_api', 'true');
    formData.append('bridge_api_url', BRIDGE_URL);
    formData.append('anthropic', 'true');
    formData.append('brain_root', 'C:\\Users\\herna\\Documents\\tutor_ia');
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

  async function askTutorBrain(question, chatId, source = 'typed_chat') {
    const endpoints = activeTutorEndpoint
      ? [activeTutorEndpoint]
      : endpointCandidates;
    let lastError = null;
    const triedHosts = new Set();

    for (const endpoint of endpoints) {
      const hostKey = endpointHostKey(endpoint);
      if (triedHosts.has(hostKey)) continue;
      triedHosts.add(hostKey);
      try {
        setBrainStatus('checking', `TUTOR_IA pensando (max ${Math.round(CHAT_TIMEOUT_MS / 1000)}s)`);
        const response = await fetchWithTimeout(endpoint, {
          method: 'POST',
          body: buildChatFormData(question, chatId, source)
        }, CHAT_TIMEOUT_MS);

        if (!response.ok) {
          let detail = '';
          try {
            const errorPayload = await response.json();
            detail = errorPayload && errorPayload.error ? `: ${errorPayload.error}` : '';
          } catch (error) {
            detail = '';
          }
          throw new Error(`HTTP ${response.status}${detail}`);
        }

        const data = await response.json();
        if (data && data.ok === false) {
          throw new Error(data.error || 'TUTOR_IA respondio con error.');
        }
        activeTutorEndpoint = endpoint;
        const sourceNames = Array.isArray(data.sources_used) && data.sources_used.length
          ? data.sources_used.slice(0, 4)
          : [];
        const brainParts = Array.isArray(data.brain_parts) && data.brain_parts.length
          ? ` - ${data.brain_parts.slice(0, 4).join(' + ')}`
          : sourceNames.length
            ? ` - ${sourceNames.join(' + ')}`
          : '';
        setBrainStatus('ready', `TUTOR_IA conectado${brainParts}`);
        return data;
      } catch (error) {
        lastError = error;
        if (error && error.name === 'AbortError') break;
      }
    }

    const timedOut = lastError && lastError.name === 'AbortError';
    setBrainStatus(timedOut ? 'error' : 'offline', timedOut ? 'TUTOR_IA no respondio a tiempo' : 'TUTOR_IA sin conexion local');
    throw lastError || new Error('No se pudo conectar con TUTOR_IA.');
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
    let language = 'código';
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
    return metadata.title || metadata.source || '';
  }

  function renderSourceSummary(sources, showSources = false) {
    if (!showSources) return '';
    const titles = (sources || [])
      .map(sourceTitle)
      .filter(Boolean)
      .slice(0, 3);

    if (!titles.length) return '';

    return `<div class="message-sources"><strong>Contexto:</strong> ${titles.map(escapeHtml).join(' - ')}</div>`;
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
      empty.textContent = query ? 'No encontré chats con esa búsqueda.' : 'Tus chats aparecerán aquí.';
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
      jarvisVoiceBtn.disabled = isLoading;
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

  function setTutorIA(enabled) {
    tutorIAEnabled = Boolean(enabled);
    window.tutorIAEnabled = tutorIAEnabled;
    tutorIABtn.classList.toggle('is-active', tutorIAEnabled);
    tutorIABtn.setAttribute('aria-pressed', String(tutorIAEnabled));
  }

  function setSmartSearch(enabled) {
    smartSearchEnabled = Boolean(enabled);
    window.smartSearchEnabled = smartSearchEnabled;
    smartSearchBtn.classList.toggle('is-active', smartSearchEnabled);
    smartSearchBtn.setAttribute('aria-pressed', String(smartSearchEnabled));
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

  function setJarvisStatus(text, state = 'idle', autoHideMs = 4200) {
    if (!jarvisStatus || !jarvisStatusText) return;
    window.clearTimeout(jarvisStatusTimer);
    jarvisStatus.hidden = false;
    jarvisStatus.dataset.state = state;
    jarvisStatusText.textContent = text;

    if (autoHideMs > 0) {
      jarvisStatusTimer = window.setTimeout(() => {
        if (jarvisListening) return;
        jarvisStatus.hidden = true;
      }, autoHideMs);
    }
  }

  function setJarvisListening(isListening) {
    jarvisListening = Boolean(isListening);
    if (!jarvisVoiceBtn) return;
    const label = jarvisVoiceBtn.querySelector('.jarvis-voice-label');
    jarvisVoiceBtn.classList.toggle('listening', jarvisListening);
    jarvisVoiceBtn.setAttribute('aria-pressed', String(jarvisListening));
    jarvisVoiceBtn.setAttribute('title', jarvisListening ? 'Detener escucha de Jarvis' : 'Hablar con Jarvis');
    if (label) label.textContent = jarvisListening ? 'Escuchando' : 'Jarvis';
  }

  function shortenJarvisText(text, maxLength = 84) {
    const clean = String(text || '').replace(/\s+/g, ' ').trim();
    return clean.length > maxLength ? `${clean.slice(0, maxLength - 1).trim()}...` : clean;
  }

  function normalizeJarvisCommand(text) {
    return String(text || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[¿?¡!.,;:]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function showJarvisUnavailableFeature() {
    setJarvisStatus('Esa función todavía no está disponible en esta interfaz.', 'error', 5200);
  }

  function toggleDeepThinkingFromJarvis(enable) {
    const deepThinkingControl = document.getElementById('deepThinkingBtn')
      || document.querySelector('[data-action="deep-thinking"], [data-feature="deep-thinking"], .deep-thinking-btn');

    if (!deepThinkingControl) {
      showJarvisUnavailableFeature();
      return;
    }

    const isActive = deepThinkingControl.getAttribute('aria-pressed') === 'true'
      || deepThinkingControl.classList.contains('is-active')
      || deepThinkingControl.checked === true;

    if (isActive !== enable) {
      deepThinkingControl.click();
    }

    setJarvisStatus(enable ? 'Pensamiento profundo activado.' : 'Pensamiento profundo desactivado.', 'idle', 3200);
  }

  function handleJarvisCommand(transcript) {
    const command = normalizeJarvisCommand(transcript);
    if (!command.startsWith('jarvis')) return false;

    if (command.includes('limpia el chat') || command.includes('limpiar el chat') || command.includes('limpia chat')) {
      clearHistory();
      coachInput.value = '';
      autosizeInput();
      setJarvisStatus('Chat limpio.', 'idle', 3000);
      return true;
    }

    if (command.includes('detener voz') || command.includes('para la voz') || command.includes('callate')) {
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      setJarvisStatus('Voz de Jarvis detenida.', 'idle', 3000);
      return true;
    }

    if (command.includes('adjuntar archivo') || command.includes('adjunta archivo')) {
      if (fileInput && !fileInput.disabled) {
        fileInput.click();
        setJarvisStatus('Selecciona el archivo para adjuntarlo.', 'idle', 4200);
      } else {
        showJarvisUnavailableFeature();
      }
      return true;
    }

    if (command.includes('desactiva busqueda inteligente')) {
      if (smartSearchBtn) {
        setSmartSearch(false);
        setJarvisStatus('Búsqueda inteligente desactivada.', 'idle', 3200);
      } else {
        showJarvisUnavailableFeature();
      }
      return true;
    }

    if (command.includes('activa busqueda inteligente')) {
      if (smartSearchBtn) {
        setSmartSearch(true);
        setJarvisStatus('Búsqueda inteligente activada.', 'idle', 3200);
      } else {
        showJarvisUnavailableFeature();
      }
      return true;
    }

    if (command.includes('desactiva pensamiento profundo')) {
      toggleDeepThinkingFromJarvis(false);
      return true;
    }

    if (command.includes('activa pensamiento profundo')) {
      toggleDeepThinkingFromJarvis(true);
      return true;
    }

    return false;
  }

  function cleanTextForSpeech(text) {
    return String(text || '')
      .replace(/```[\s\S]*?```/g, ' bloque de código disponible en pantalla. ')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/[#*_>\[\]{}()]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function speakJarvisResponse(text) {
    if (!JARVIS_READ_RESPONSES || !window.speechSynthesis || !window.SpeechSynthesisUtterance) return;
    const clean = cleanTextForSpeech(text);
    if (!clean) return;

    const speechText = clean.length > 1500
      ? `${clean.slice(0, 1500).trim()}. La respuesta completa está en pantalla.`
      : clean;
    const utterance = new SpeechSynthesisUtterance(speechText);
    const voices = window.speechSynthesis.getVoices ? window.speechSynthesis.getVoices() : [];
    const preferredVoice = voices.find(voice => /^es[-_]?NI/i.test(voice.lang))
      || voices.find(voice => /^es[-_]?ES/i.test(voice.lang))
      || voices.find(voice => /^es[-_]?MX/i.test(voice.lang))
      || voices.find(voice => /^es/i.test(voice.lang));

    if (preferredVoice) {
      utterance.voice = preferredVoice;
      utterance.lang = preferredVoice.lang;
    } else {
      utterance.lang = 'es-ES';
    }

    utterance.rate = 1;
    utterance.pitch = 0.9;
    utterance.volume = 1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  async function sendCurrentMessage(options = {}) {
    if (isSubmitting) return false;

    const source = options.source || 'typed_chat';
    const typedQuestion = coachInput.value.trim();
    const question = typedQuestion || (selectedFiles.length ? 'Analiza los archivos adjuntos.' : '');
    if (!question) return false;

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
      content: 'Pensando...',
      createdAt: nowIso(),
      loading: true
    };
    const chat = chats.find(item => item.id === chatId);
    chat.messages.push(loadingMessage);
    chat.updatedAt = nowIso();
    persist();
    renderChat();

    try {
      const result = await askTutorBrain(question, chatId, source);
      const answer = result.answer || result.response || 'TUTOR_IA respondió sin texto.';
      const showSources = Boolean(result.show_sources);
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
        setJarvisStatus('Respuesta lista.', 'idle', 3600);
        speakJarvisResponse(answer);
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
        setJarvisStatus('Jarvis no pudo completar la respuesta.', 'error', 6200);
        speakJarvisResponse(answer);
      }
      return false;
    } finally {
      isSubmitting = false;
      setComposerLoading(false);
      coachInput.focus();
      renderHistory();
    }
  }

  function sendMessageFromVoice(text) {
    coachInput.value = String(text || '').trim();
    autosizeInput();
    setJarvisStatus('Jarvis está pensando...', 'thinking', 0);
    return sendCurrentMessage({ source: 'jarvis_voice' });
  }

  function handleJarvisResult(transcript) {
    const text = String(transcript || '').trim();
    if (!text) {
      setJarvisStatus('No pude escuchar correctamente. Intenta de nuevo.', 'error', 5200);
      return;
    }

    coachInput.value = text;
    autosizeInput();
    coachInput.focus();
    setJarvisStatus(`Entendido: ${shortenJarvisText(text)}`, 'idle', 2600);

    if (handleJarvisCommand(text)) return;
    sendMessageFromVoice(text);
  }

  function handleJarvisError(event) {
    const code = event && event.error ? event.error : '';

    if (code === 'language-not-supported' && jarvisLangIndex < JARVIS_RECOGNITION_LANGS.length - 1) {
      jarvisLangIndex += 1;
      jarvisRecognition = createJarvisRecognition(JARVIS_RECOGNITION_LANGS[jarvisLangIndex]);
      window.setTimeout(startJarvisListening, 120);
      return;
    }

    const messages = {
      'not-allowed': 'Permiso de micrófono denegado. Actívalo en el navegador y vuelve a intentar.',
      'service-not-allowed': 'El navegador bloqueó el servicio de voz. Usa Google Chrome o Microsoft Edge en Windows.',
      'audio-capture': 'No encuentro un micrófono disponible en Windows.',
      'no-speech': 'No pude escuchar correctamente. Intenta de nuevo.',
      network: 'Jarvis no pudo usar el reconocimiento de voz. Revisa tu conexión o intenta de nuevo.'
    };
    setJarvisListening(false);
    setJarvisStatus(messages[code] || 'No pude escuchar correctamente. Intenta de nuevo.', 'error', 6200);
  }

  function createJarvisRecognition(lang) {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Recognition();
    recognition.lang = lang;
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setJarvisListening(true);
      setJarvisStatus('Jarvis escuchando...', 'listening', 0);
    };

    recognition.onresult = event => {
      const result = event.results && event.results[0] && event.results[0][0];
      handleJarvisResult(result ? result.transcript : '');
    };

    recognition.onerror = handleJarvisError;
    recognition.onend = () => {
      setJarvisListening(false);
    };

    return recognition;
  }

  function startJarvisListening() {
    if (!jarvisSupported) {
      setJarvisStatus(JARVIS_UNSUPPORTED_MESSAGE, 'error', 8000);
      return;
    }

    if (isSubmitting) {
      setJarvisStatus('Espera a que termine la respuesta actual.', 'thinking', 3600);
      return;
    }

    if (!jarvisRecognition) {
      jarvisRecognition = createJarvisRecognition(JARVIS_RECOGNITION_LANGS[jarvisLangIndex]);
    }

    try {
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      jarvisRecognition.start();
    } catch (error) {
      setJarvisStatus('Jarvis ya está escuchando o el navegador no liberó el micrófono todavía.', 'error', 5200);
    }
  }

  function stopJarvisListening() {
    if (!jarvisRecognition) return;
    try {
      jarvisRecognition.stop();
    } catch (error) {
      // El navegador puede lanzar error si la escucha ya terminó.
    }
    setJarvisListening(false);
    setJarvisStatus('Escucha detenida.', 'idle', 2400);
  }

  function initJarvisVoice() {
    if (!jarvisVoiceBtn) return;
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    jarvisSupported = Boolean(Recognition);

    if (!jarvisSupported) {
      jarvisVoiceBtn.disabled = false;
      jarvisVoiceBtn.classList.add('jarvis-disabled');
      jarvisVoiceBtn.setAttribute('aria-disabled', 'true');
      jarvisVoiceBtn.addEventListener('click', () => {
        setJarvisStatus(JARVIS_UNSUPPORTED_MESSAGE, 'error', 8000);
      });
      return;
    }

    jarvisVoiceBtn.classList.remove('jarvis-disabled');
    jarvisVoiceBtn.setAttribute('aria-disabled', 'false');
    jarvisVoiceBtn.disabled = false;
    jarvisRecognition = createJarvisRecognition(JARVIS_RECOGNITION_LANGS[jarvisLangIndex]);
    jarvisVoiceBtn.addEventListener('click', () => {
      if (jarvisListening) {
        stopJarvisListening();
      } else {
        startJarvisListening();
      }
    });

    if (window.speechSynthesis && window.speechSynthesis.getVoices) {
      window.speechSynthesis.getVoices();
    }
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

  fileInput.addEventListener('change', event => {
    setSelectedFiles(event.target.files);
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

  sortChats();
  setTutorIA(true);
  setSmartSearch(false);
  initJarvisVoice();
  renderAttachments();
  renderChat();
  autosizeInput();
  detectTutorBrain();
});
