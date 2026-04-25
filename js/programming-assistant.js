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
  const bookGrid = document.getElementById('bookGrid');
  let progress = Number(localStorage.getItem('programmingAssistantProgress') || 0);

  function normalize(text) {
    return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function renderTrack(trackKey) {
    const track = tracks[trackKey];
    lessonTitle.textContent = track.title;
    lessonDescription.textContent = track.description;
    exerciseTitle.textContent = track.exerciseTitle;
    exercisePrompt.textContent = track.exercisePrompt;
    dailyChallenge.textContent = track.challenge;
    exerciseAnswer.value = '';
    exerciseFeedback.textContent = '';
    quizResult.textContent = '';

    conceptList.innerHTML = track.concepts.map(concept => `<span>${concept}</span>`).join('');
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
        quizResult.textContent = isCorrect ? 'Correcto. Vas construyendo una buena base.' : `Casi. La respuesta correcta es: ${track.quiz.answer}.`;
        if (isCorrect) updateProgress(10);
      });
      quizOptions.appendChild(button);
    });
  }

  function renderBooks(recommendedIds = []) {
    bookGrid.innerHTML = books.map(book => {
      const recommended = recommendedIds.includes(book.id) ? '<span class="book-badge">Recomendado</span>' : '';
      return `
        <article class="book-card glass-card">
          ${recommended}
          <i class="${book.icon}"></i>
          <h3>${book.title}</h3>
          <p>${book.topics.join(' · ')}</p>
          <a href="${book.url}" target="_blank" rel="noopener" class="btn btn-outline">Abrir libro</a>
        </article>
      `;
    }).join('');
  }

  function updateProgress(points) {
    progress = Math.min(100, progress + points);
    localStorage.setItem('programmingAssistantProgress', String(progress));
    progressValue.textContent = `${progress}%`;
    progressBar.style.width = `${progress}%`;
  }

  function addCoachMessage(text, type = 'bot') {
    const message = document.createElement('div');
    message.className = `coach-message ${type}`;
    message.innerHTML = text;
    coachMessages.appendChild(message);
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

  trackSelect.addEventListener('change', () => renderTrack(trackSelect.value));

  document.getElementById('hintBtn').addEventListener('click', () => {
    exerciseFeedback.textContent = tracks[trackSelect.value].hint;
  });

  document.getElementById('checkExerciseBtn').addEventListener('click', () => {
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

  document.getElementById('completeLessonBtn').addEventListener('click', () => updateProgress(20));

  coachForm.addEventListener('submit', event => {
    event.preventDefault();
    const question = coachInput.value.trim();
    if (!question) return;

    addCoachMessage(question, 'user');
    coachInput.value = '';

    const book = recommendBook(question);
    addCoachMessage(`Para esa duda te recomiendo empezar con <strong>${book.title}</strong>. Abre el libro, estudia el tema relacionado y vuelve aquí para practicar con un ejercicio. <a href="${book.url}" target="_blank" rel="noopener">Abrir recurso</a>.`);
  });

  updateProgress(0);
  renderTrack(trackSelect.value);
  addCoachMessage('Hola. Dime qué quieres aprender: variables, Python, SQL, C#, web, automatización o seguridad. Te recomendaré el libro base y una forma de practicar.');
});
