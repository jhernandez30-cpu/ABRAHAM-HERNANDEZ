const DEFAULT_ENDPOINTS = [
  'http://127.0.0.1:8787/api/chat',
  'http://localhost:8787/api/chat'
];

const STORAGE_KEY = 'tutorIaChatHistory';
const ACTIVE_CHAT_KEY = 'tutorIaActiveChatId';
const DEFAULT_MODE = 'Cerebro Unificado';
const PROJECT_PATH = window.TUTOR_IA_PROJECT_PATH || '';
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
  const endpointCandidates = normalizeEndpoints(window.TUTOR_IA_ENDPOINTS || DEFAULT_ENDPOINTS);

  let activeTutorEndpoint = '';
  let tutorIAEnabled = true;
  let smartSearchEnabled = false;
  let selectedFiles = [];
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

  function endpointHealthUrl(endpoint) {
    return endpoint.replace(/\/api\/chat$/, '/api/health');
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
      try {
        const response = await fetchWithTimeout(endpointHealthUrl(endpoint), { method: 'GET' }, 3500);
        if (!response.ok) continue;
        const data = await response.json();
        activeTutorEndpoint = endpoint;

        const fragments = Number(data.fragments || 0);
        const obsidianNotes = Number(data.obsidian && data.obsidian.notes ? data.obsidian.notes : 0);
        const agencyAgents = Number(data.agency && data.agency.count ? data.agency.count : 0);
        const jarvisProfiles = Number(data.jarvis && data.jarvis.detected_profiles ? data.jarvis.detected_profiles : 0);
        const contextParts = [`${fragments} fragmentos`];
        if (obsidianNotes) contextParts.push(`${obsidianNotes} notas Obsidian`);
        if (agencyAgents) contextParts.push(`${agencyAgents} agentes`);
        if (jarvisProfiles) contextParts.push(`${jarvisProfiles} perfiles Jarvis`);
        const modelText = data.model ? ` - ${data.model}` : '';

        setBrainStatus('ready', `TUTOR_IA conectado - ${contextParts.join(' + ')}${modelText}`);
        return;
      } catch (error) {
        continue;
      }
    }

    setBrainStatus('offline', 'TUTOR_IA sin conexión local');
  }

  function buildChatFormData(question, chatId) {
    const formData = new FormData();
    formData.append('message', question);
    formData.append('question', question);
    formData.append('mode', DEFAULT_MODE);
    formData.append('tutorIA', String(tutorIAEnabled));
    formData.append('smartSearch', String(smartSearchEnabled));
    formData.append('session_id', chatId);
    formData.append('client', 'abraham-programming-assistant');
    formData.append('response_profile', 'fast_smart');
    formData.append('include_obsidian', String(tutorIAEnabled));
    formData.append('agency_enabled', String(tutorIAEnabled));
    formData.append('jarvis_profile', 'unified');
    formData.append('obsidian_top_k', '2');
    formData.append('show_sources', 'false');
    if (PROJECT_PATH) {
      formData.append('project_path', PROJECT_PATH);
      formData.append('workspace_path', PROJECT_PATH);
    }
    selectedFiles.forEach(file => formData.append('files', file, file.name));
    return formData;
  }

  async function askTutorBrain(question, chatId) {
    const endpoints = activeTutorEndpoint
      ? [activeTutorEndpoint, ...endpointCandidates.filter(endpoint => endpoint !== activeTutorEndpoint)]
      : endpointCandidates;
    let lastError = null;

    for (const endpoint of endpoints) {
      try {
        const response = await fetchWithTimeout(endpoint, {
          method: 'POST',
          body: buildChatFormData(question, chatId)
        }, 180000);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        activeTutorEndpoint = endpoint;
        const brainParts = Array.isArray(data.brain_parts) && data.brain_parts.length
          ? ` - ${data.brain_parts.slice(0, 4).join(' + ')}`
          : '';
        setBrainStatus('ready', `TUTOR_IA conectado${brainParts}`);
        return data;
      } catch (error) {
        lastError = error;
      }
    }

    setBrainStatus('offline', 'TUTOR_IA sin conexión local');
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
  }

  function fallbackAnswer() {
    return 'No logré conectar con TUTOR_IA en este momento. Abre el puente local en tu PC y vuelve a intentarlo: `http://127.0.0.1:8787/api/health`.';
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
    const typedQuestion = coachInput.value.trim();
    const question = typedQuestion || (selectedFiles.length ? 'Analiza los archivos adjuntos.' : '');
    if (!question) return;

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
      const result = await askTutorBrain(question, chatId);
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
    } catch (error) {
      const answer = fallbackAnswer();
      updateMessageInChat(chatId, loadingMessage.id, {
        content: answer,
        sources: [],
        loading: false
      });
      updateRenderedMessage(loadingMessage.id, answer);
    } finally {
      setComposerLoading(false);
      coachInput.focus();
      renderHistory();
    }
  });

  sortChats();
  setTutorIA(true);
  setSmartSearch(false);
  renderAttachments();
  renderChat();
  autosizeInput();
  detectTutorBrain();
});
