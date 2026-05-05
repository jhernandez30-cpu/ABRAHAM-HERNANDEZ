const books = [
  {
    id: 'programming',
    title: 'Libro Programación',
    icon: 'fas fa-code',
    topics: ['algoritmos', 'variables', 'condicionales', 'bucles', 'funciones'],
    url: 'https://notebooklm.google.com/notebook/f3754505-88f8-41eb-81d4-16f9a155d004'
  },
  {
    id: 'python',
    title: 'Libro Python',
    icon: 'fab fa-python',
    topics: ['python', 'automatización', 'scripts', 'listas', 'diccionarios'],
    url: 'https://notebooklm.google.com/notebook/9246f385-75de-45a9-b534-d004a8e0077e'
  },
  {
    id: 'csharp',
    title: 'Libro C#',
    icon: 'fab fa-microsoft',
    topics: ['c#', 'dotnet', 'poo', 'linq', 'clases'],
    url: 'https://notebooklm.google.com/notebook/e51149dd-27bb-4c93-bf26-005d1c4451c6'
  },
  {
    id: 'database',
    title: 'Libro Base de Datos',
    icon: 'fas fa-database',
    topics: ['sql', 'tablas', 'consultas', 'joins', 'normalización'],
    url: 'https://notebooklm.google.com/notebook/06b7e20f-444a-4c27-a110-4af367550ed0'
  },
  {
    id: 'powerbi',
    title: 'Libro Power BI',
    icon: 'fas fa-chart-pie',
    topics: ['power bi', 'dashboards', 'datos', 'visualización', 'reportes'],
    url: 'https://notebooklm.google.com/notebook/5947016f-b96e-4d82-b48c-9d8bce6f87f6'
  },
  {
    id: 'security',
    title: 'Libro Ciberseguridad',
    icon: 'fas fa-shield-alt',
    topics: ['seguridad', 'vulnerabilidades', 'buenas prácticas', 'owasp'],
    url: 'https://notebooklm.google.com/notebook/f3754505-88f8-41eb-81d4-16f9a155d004'
  },
  {
    id: 'n8n',
    title: 'Libro Agente N8N',
    icon: 'fas fa-robot',
    topics: ['n8n', 'automatización', 'flujos', 'agentes', 'webhooks'],
    url: 'https://notebooklm.google.com/notebook/c8749429-c45f-4d68-972e-a2266f74964f'
  }
];

const tracks = {
  fundamentos: {
    title: 'Fundamentos de programación',
    description: 'Empieza por la lógica: variables, tipos de datos, condicionales, bucles, funciones y resolución de problemas.',
    concepts: ['Variables y tipos de datos', 'Condicionales if/else', 'Bucles for y while', 'Funciones reutilizables', 'Pensamiento algorítmico'],
    exerciseTitle: 'Calculadora de promedio',
    exercisePrompt: 'Crea un algoritmo que reciba tres notas, calcule el promedio y muestre si el estudiante aprobó con 70 o más.',
    hint: 'Divide el problema en entrada, proceso y salida. Usa una condición para comparar el promedio.',
    keywords: ['promedio', 'nota', 'if', 'aprob', '70', 'variable'],
    challenge: 'Escribe 5 ejemplos de variables reales y define qué tipo de dato usarías en cada una.',
    books: ['programming'],
    quiz: {
      question: '¿Qué estructura usarías para repetir una acción varias veces?',
      options: ['Un bucle', 'Una imagen', 'Un comentario'],
      answer: 'Un bucle'
    }
  },
  web: {
    title: 'Desarrollo web',
    description: 'Aprende cómo se construye una interfaz web con HTML, CSS, JavaScript, eventos y componentes interactivos.',
    concepts: ['HTML semántico', 'CSS responsive', 'DOM y eventos', 'Formularios', 'Buenas prácticas de interfaz'],
    exerciseTitle: 'Formulario interactivo',
    exercisePrompt: 'Diseña un formulario con nombre, correo y mensaje. Luego describe cómo validarías que ningún campo esté vacío.',
    hint: 'Piensa en etiquetas input, evento submit y validación antes de enviar.',
    keywords: ['form', 'input', 'submit', 'valid', 'html', 'css', 'javascript'],
    challenge: 'Crea una tarjeta HTML para presentar un proyecto con título, descripción y botón.',
    books: ['programming', 'python'],
    quiz: {
      question: '¿Qué lenguaje se usa principalmente para dar estilos a una página web?',
      options: ['CSS', 'SQL', 'C#'],
      answer: 'CSS'
    }
  },
  python: {
    title: 'Python y automatización',
    description: 'Usa Python para resolver problemas, manipular datos, crear scripts y automatizar tareas repetitivas.',
    concepts: ['Sintaxis de Python', 'Listas y diccionarios', 'Funciones', 'Archivos', 'Automatización con scripts'],
    exerciseTitle: 'Organizador de tareas',
    exercisePrompt: 'Escribe pseudocódigo o Python para guardar tareas en una lista y mostrar solo las tareas pendientes.',
    hint: 'Una lista de diccionarios puede guardar nombre y estado de cada tarea.',
    keywords: ['lista', 'tarea', 'pendiente', 'for', 'python', 'diccionario'],
    challenge: 'Haz un script que reciba una lista de números y muestre el mayor.',
    books: ['python', 'n8n'],
    quiz: {
      question: '¿Qué estructura de Python permite guardar varios valores ordenados?',
      options: ['Lista', 'Firewall', 'Tabla CSS'],
      answer: 'Lista'
    }
  },
  database: {
    title: 'Bases de datos SQL',
    description: 'Aprende a modelar información, consultar datos, filtrar resultados y relacionar tablas.',
    concepts: ['Tablas y columnas', 'SELECT y WHERE', 'INSERT/UPDATE/DELETE', 'JOIN entre tablas', 'Diseño relacional'],
    exerciseTitle: 'Consulta de clientes',
    exercisePrompt: 'Imagina una tabla clientes con nombre, ciudad y total_compras. Escribe una consulta para ver clientes de Managua con compras mayores a 100.',
    hint: 'Usa SELECT, FROM y WHERE con dos condiciones.',
    keywords: ['select', 'from', 'where', 'managua', '100', 'clientes'],
    challenge: 'Diseña dos tablas relacionadas para pedidos y clientes.',
    books: ['database'],
    quiz: {
      question: '¿Qué palabra clave se usa para filtrar resultados en SQL?',
      options: ['WHERE', 'STYLE', 'PRINT'],
      answer: 'WHERE'
    }
  },
  csharp: {
    title: 'C# y .NET',
    description: 'Construye bases sólidas en programación orientada a objetos con clases, métodos, propiedades y colecciones.',
    concepts: ['Clases y objetos', 'Métodos', 'Propiedades', 'Listas', 'LINQ básico'],
    exerciseTitle: 'Clase Producto',
    exercisePrompt: 'Define una clase Producto con nombre, precio y un método que calcule el precio con impuesto.',
    hint: 'Piensa en propiedades para guardar datos y un método que retorne precio * 1.15.',
    keywords: ['class', 'producto', 'precio', 'metodo', 'return', 'impuesto'],
    challenge: 'Crea una lista de productos y calcula el total usando un ciclo.',
    books: ['csharp', 'programming'],
    quiz: {
      question: '¿Qué representa una clase en programación orientada a objetos?',
      options: ['Un molde para crear objetos', 'Un color de CSS', 'Una consulta SQL'],
      answer: 'Un molde para crear objetos'
    }
  }
};

const DEFAULT_ENDPOINTS = [
  'http://127.0.0.1:8787/api/chat',
  'http://localhost:8787/api/chat'
];

document.addEventListener('DOMContentLoaded', () => {
  const trackSelect = document.getElementById('trackSelect');
  const lessonTitle = document.getElementById('lessonTitle');
  const lessonDescription = document.getElementById('lessonDescription');
  const conceptList = document.getElementById('conceptList');
  const exerciseTitle = document.getElementById('exerciseTitle');
  const exercisePrompt = document.getElementById('exercisePrompt');
  const exerciseAnswer = document.getElementById('exerciseAnswer');
  const exerciseFeedback = document.getElementById('exerciseFeedback');
  const progressValue = document.getElementById('progressValue');
  const progressBar = document.getElementById('progressBar');
  const dailyChallenge = document.getElementById('dailyChallenge');
  const quizQuestion = document.getElementById('quizQuestion');
  const quizOptions = document.getElementById('quizOptions');
  const quizResult = document.getElementById('quizResult');
  const coachMessages = document.getElementById('coachMessages');
  const coachForm = document.getElementById('coachForm');
  const coachInput = document.getElementById('coachInput');
  const assistantMode = document.getElementById('assistantMode');
  const bookGrid = document.getElementById('bookGrid');
  const brainStatus = document.getElementById('brainStatus');
  const brainStatusText = document.getElementById('brainStatusText');
  const promptMenuBtn = document.getElementById('promptMenuBtn');
  const assistantSuggestions = document.getElementById('assistantSuggestions');
  const micBtn = document.getElementById('micBtn');
  const sendButton = coachForm ? coachForm.querySelector('.send-orb') : null;
  const endpointCandidates = normalizeEndpoints(window.TUTOR_IA_ENDPOINTS || DEFAULT_ENDPOINTS);
  let activeTutorEndpoint = '';
  let progress = readStoredNumber('programmingAssistantProgress', 0);
  let sessionId = getSessionId();

  function normalize(text) {
    return String(text || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function readStoredNumber(key, fallback) {
    try {
      return Number(localStorage.getItem(key) || fallback);
    } catch (error) {
      return fallback;
    }
  }

  function writeStoredValue(key, value) {
    try {
      localStorage.setItem(key, String(value));
    } catch (error) {
      return false;
    }
    return true;
  }

  function getSessionId() {
    try {
      const stored = sessionStorage.getItem('tutorIaSessionId');
      if (stored) return stored;
      const next = `web-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      sessionStorage.setItem('tutorIaSessionId', next);
      return next;
    } catch (error) {
      return `web-${Date.now()}`;
    }
  }

  function normalizeEndpoints(endpoints) {
    return [...new Set(endpoints.filter(Boolean).map(endpoint => endpoint.replace(/\/$/, '')))];
  }

  function endpointHealthUrl(endpoint) {
    return endpoint.replace(/\/api\/chat$/, '/api/health');
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
        const modelText = data.model ? ` · ${data.model}` : '';
        setBrainStatus('ready', `TUTOR_IA conectado · ${fragments} fuentes${modelText}`);
        return;
      } catch (error) {
        continue;
      }
    }

    setBrainStatus('offline', 'TUTOR_IA sin conexión local');
  }

  async function askTutorBrain(question) {
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
            session_id: sessionId,
            agency_enabled: assistantMode ? assistantMode.value === 'agency' : false
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

  function renderSourceSummary(sources) {
    const titles = (sources || [])
      .map(sourceTitle)
      .filter(Boolean)
      .slice(0, 3);

    if (!titles.length) return '';

    return `<br><br><strong>Fuentes:</strong> ${titles.map(escapeHtml).join(' · ')}`;
  }

  function addCoachMessage(text, type = 'bot', options = {}) {
    const message = document.createElement('div');
    message.className = `assistant-message ${type}${options.loading ? ' loading' : ''}`;
    message.innerHTML = options.raw ? text : formatAssistantText(text);
    coachMessages.appendChild(message);
    coachMessages.scrollTop = coachMessages.scrollHeight;
    return message;
  }

  function updateCoachMessage(message, text, options = {}) {
    if (!message) return;
    message.classList.remove('loading');
    message.innerHTML = options.raw ? text : formatAssistantText(text);
    coachMessages.scrollTop = coachMessages.scrollHeight;
  }

  function recommendBook(question) {
    const cleanQuestion = normalize(question);
    const scored = books
      .map(book => ({
        ...book,
        score: book.topics.reduce((total, topic) => total + (cleanQuestion.includes(normalize(topic)) ? 1 : 0), 0)
      }))
      .sort((a, b) => b.score - a.score);

    return scored[0].score > 0 ? scored[0] : books[0];
  }

  function localFallbackAnswer(question) {
    const book = recommendBook(question);
    return `
      No logré conectar con TUTOR_IA en este momento. Mientras levantas el puente local, te recomiendo empezar con
      <strong>${escapeHtml(book.title)}</strong> y practicar con una pregunta concreta sobre ${escapeHtml(book.topics.slice(0, 3).join(', '))}.
      <br><br>
      <a href="${book.url}" target="_blank" rel="noopener">Abrir recurso</a>
    `;
  }

  function renderTrack(trackKey) {
    const track = tracks[trackKey];
    if (!track) return;

    lessonTitle.textContent = track.title;
    lessonDescription.textContent = track.description;
    exerciseTitle.textContent = track.exerciseTitle;
    exercisePrompt.textContent = track.exercisePrompt;
    dailyChallenge.textContent = track.challenge;
    exerciseAnswer.value = '';
    exerciseFeedback.textContent = '';
    quizResult.textContent = '';

    conceptList.innerHTML = track.concepts.map(concept => `<span>${escapeHtml(concept)}</span>`).join('');
    renderQuiz(track);
    renderBooks(track.books);
  }

  function renderQuiz(track) {
    quizQuestion.textContent = track.quiz.question;
    quizOptions.innerHTML = '';
    track.quiz.options.forEach(option => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = option;
      button.addEventListener('click', () => {
        const isCorrect = option === track.quiz.answer;
        quizResult.textContent = isCorrect
          ? 'Correcto. Vas construyendo una buena base.'
          : `Casi. La respuesta correcta es: ${track.quiz.answer}.`;
        if (isCorrect) updateProgress(10);
      });
      quizOptions.appendChild(button);
    });
  }

  function renderBooks(recommendedIds = []) {
    bookGrid.innerHTML = books.map(book => {
      const recommended = recommendedIds.includes(book.id) ? '<span class="book-badge">Recomendado</span>' : '';
      return `
        <article class="book-card">
          ${recommended}
          <i class="${book.icon}" aria-hidden="true"></i>
          <h3>${escapeHtml(book.title)}</h3>
          <p>${book.topics.map(escapeHtml).join(' · ')}</p>
          <a href="${book.url}" target="_blank" rel="noopener" class="btn btn-outline">Abrir libro</a>
        </article>
      `;
    }).join('');
  }

  function updateProgress(points) {
    progress = Math.min(100, progress + points);
    writeStoredValue('programmingAssistantProgress', progress);
    progressValue.textContent = `${progress}%`;
    progressBar.style.width = `${progress}%`;
  }

  function setComposerLoading(isLoading) {
    if (sendButton) sendButton.disabled = isLoading;
    if (coachInput) coachInput.disabled = isLoading;
  }

  function inferTrackFromQuestion(question) {
    const cleanQuestion = normalize(question);
    const entries = [
      ['python', ['python', 'automatizacion', 'script', 'lista', 'diccionario']],
      ['database', ['sql', 'base de datos', 'tabla', 'select', 'join']],
      ['csharp', ['c#', 'csharp', 'dotnet', 'clase', 'objeto']],
      ['web', ['html', 'css', 'javascript', 'web', 'formulario']],
      ['fundamentos', ['variable', 'bucle', 'condicional', 'algoritmo', 'funcion']]
    ];
    const match = entries.find(([, keywords]) => keywords.some(keyword => cleanQuestion.includes(keyword)));
    return match ? match[0] : '';
  }

  if (trackSelect) {
    trackSelect.addEventListener('change', () => renderTrack(trackSelect.value));
  }

  const hintBtn = document.getElementById('hintBtn');
  if (hintBtn) {
    hintBtn.addEventListener('click', () => {
      exerciseFeedback.textContent = tracks[trackSelect.value].hint;
    });
  }

  const checkExerciseBtn = document.getElementById('checkExerciseBtn');
  if (checkExerciseBtn) {
    checkExerciseBtn.addEventListener('click', () => {
      const track = tracks[trackSelect.value];
      const answer = normalize(exerciseAnswer.value);
      const hits = track.keywords.filter(keyword => answer.includes(normalize(keyword))).length;

      if (answer.length < 25) {
        exerciseFeedback.textContent = 'Escribe un poco más: intenta mostrar entradas, proceso y salida.';
        return;
      }

      if (hits >= 2) {
        exerciseFeedback.textContent = 'Buen trabajo. Tu respuesta incluye elementos clave del ejercicio.';
        updateProgress(15);
      } else {
        exerciseFeedback.textContent = 'La idea va tomando forma. Agrega más palabras clave del problema y explica la lógica paso a paso.';
      }
    });
  }

  const completeLessonBtn = document.getElementById('completeLessonBtn');
  if (completeLessonBtn) {
    completeLessonBtn.addEventListener('click', () => updateProgress(20));
  }

  if (promptMenuBtn && assistantSuggestions) {
    promptMenuBtn.addEventListener('click', () => {
      assistantSuggestions.hidden = !assistantSuggestions.hidden;
    });

    assistantSuggestions.addEventListener('click', event => {
      const button = event.target.closest('button[data-prompt]');
      if (!button) return;
      coachInput.value = button.dataset.prompt;
      assistantSuggestions.hidden = true;
      coachInput.focus();
    });
  }

  if (micBtn) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      micBtn.disabled = true;
      micBtn.title = 'Dictado no disponible en este navegador';
    } else {
      const recognition = new SpeechRecognition();
      recognition.lang = 'es-ES';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      micBtn.addEventListener('click', () => {
        recognition.start();
      });

      recognition.addEventListener('result', event => {
        const transcript = event.results[0][0].transcript;
        coachInput.value = transcript;
        coachInput.focus();
      });
    }
  }

  if (coachForm) {
    coachForm.addEventListener('submit', async event => {
      event.preventDefault();
      const question = coachInput.value.trim();
      if (!question) return;

      addCoachMessage(question, 'user');
      coachInput.value = '';
      setComposerLoading(true);

      const inferredTrack = inferTrackFromQuestion(question);
      if (inferredTrack && trackSelect && trackSelect.value !== inferredTrack) {
        trackSelect.value = inferredTrack;
        renderTrack(inferredTrack);
      }

      const loadingMessage = addCoachMessage('Consultando TUTOR_IA...', 'bot', { loading: true });
      try {
        const result = await askTutorBrain(question);
        const answer = result.answer || result.response || 'TUTOR_IA respondió sin texto.';
        updateCoachMessage(
          loadingMessage,
          `${formatAssistantText(answer)}${renderSourceSummary(result.sources)}`,
          { raw: true }
        );
      } catch (error) {
        updateCoachMessage(loadingMessage, localFallbackAnswer(question), { raw: true });
      } finally {
        setComposerLoading(false);
        coachInput.focus();
      }
    });
  }

  updateProgress(0);
  if (trackSelect) renderTrack(trackSelect.value);
  detectTutorBrain();
});
