const DEFAULT_ENDPOINTS = [
  'http://127.0.0.1:8787/api/chat',
  'http://localhost:8787/api/chat'
];

const STORAGE_KEY = 'tutorIaChatHistory';
const ACTIVE_CHAT_KEY = 'tutorIaActiveChatId';

document.addEventListener('DOMContentLoaded', () => {
  const coachMessages = document.getElementById('coachMessages');
  const emptyChatState = document.getElementById('emptyChatState');
  const coachForm = document.getElementById('coachForm');
  const coachInput = document.getElementById('coachInput');
  const assistantMode = document.getElementById('assistantMode');
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
  const micBtn = document.getElementById('micBtn');
  const sendButton = coachForm ? coachForm.querySelector('.send-orb') : null;
  const endpointCandidates = normalizeEndpoints(window.TUTOR_IA_ENDPOINTS || DEFAULT_ENDPOINTS);
  let activeTutorEndpoint = '';
  let chats = loadChats();
  let activeChatId = loadActiveChatId();

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

    for (const endpoint of endpointCandidates) {
      try {
        const response = await fetchWithTimeout(endpointHealthUrl(endpoint), { method: 'GET' }, 3500);
        if (!response.ok) continue;
        const data = await response.json();
        activeTutorEndpoint = endpoint;
        const fragments = Number(data.fragments || 0);
        const obsidianNotes = Number(data.obsidian && data.obsidian.notes ? data.obsidian.notes : 0);
        const contextParts = [`${fragments} fragmentos`];
        if (obsidianNotes) contextParts.push(`${obsidianNotes} notas Obsidian`);
        const modelText = data.model ? ` - ${data.model}` : '';
        setBrainStatus('ready', `TUTOR_IA conectado - ${contextParts.join(' + ')}${modelText}`);
        return;
      } catch (error) {
        continue;
      }
    }

    setBrainStatus('offline', 'TUTOR_IA sin conexión local');
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
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question,
            mode: assistantMode ? assistantMode.value : 'study',
            session_id: chatId,
            agency_enabled: assistantMode ? assistantMode.value === 'agency' : false,
            client: 'abraham-programming-assistant',
            response_profile: 'fast_smart',
            include_obsidian: true,
            obsidian_top_k: 2,
            show_sources: false
          })
        }, 180000);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        activeTutorEndpoint = endpoint;
        setBrainStatus('ready', 'TUTOR_IA conectado');
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

  function formatAssistantText(text) {
    const escaped = escapeHtml(text);
    const withLinks = escaped.replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );
    return withLinks.replace(/\n/g, '<br>');
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

  function titleFromQuestion(question) {
    const clean = String(question || '').replace(/\s+/g, ' ').trim();
    if (!clean) return 'Nuevo chat';
    return clean.length > 42 ? `${clean.slice(0, 41).trim()}…` : clean;
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
    bubble.innerHTML = `${formatAssistantText(message.content)}${renderSourceSummary(message.sources, message.showSources)}`;
    row.appendChild(bubble);
    return row;
  }

  function updateRenderedMessage(messageId, content, options = {}) {
    const row = coachMessages.querySelector(`[data-message-id="${messageId}"]`);
    if (!row) return;
    const bubble = row.querySelector('.message-bubble');
    if (!bubble) return;
    bubble.classList.toggle('loading', Boolean(options.loading));
    bubble.innerHTML = `${formatAssistantText(content)}${renderSourceSummary(options.sources, options.showSources)}`;
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
  }

  function fallbackAnswer() {
    return 'No logré conectar con TUTOR_IA en este momento. Abre el puente local en tu PC y vuelve a intentarlo: `http://127.0.0.1:8787/api/health`.';
  }

  function autosizeInput() {
    coachInput.style.height = 'auto';
    coachInput.style.height = `${Math.min(coachInput.scrollHeight, 160)}px`;
  }

  function openSidebar() {
    chatSidebar.classList.add('open');
    sidebarBackdrop.hidden = false;
  }

  function closeSidebar() {
    chatSidebar.classList.remove('open');
    sidebarBackdrop.hidden = true;
  }

  function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      micBtn.disabled = true;
      micBtn.title = 'Dictado no disponible en este navegador';
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    micBtn.addEventListener('click', () => {
      recognition.start();
    });

    recognition.addEventListener('result', event => {
      coachInput.value = event.results[0][0].transcript;
      autosizeInput();
      coachInput.focus();
    });
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

  coachForm.addEventListener('submit', async event => {
    event.preventDefault();
    const question = coachInput.value.trim();
    if (!question) return;

    const chatId = activeChatId;
    addMessageToChat(chatId, { role: 'user', content: question });
    coachInput.value = '';
    autosizeInput();
    renderChat();
    setComposerLoading(true);

    const loadingMessage = {
      id: createId(),
      role: 'assistant',
      content: 'Consultando TUTOR_IA...',
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
        showSources,
        loading: false
      });
      updateRenderedMessage(loadingMessage.id, answer, { sources: showSources ? result.sources || [] : [], showSources });
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
  renderChat();
  setupSpeechRecognition();
  detectTutorBrain();
});
