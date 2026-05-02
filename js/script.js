// === script.js (versión ajustada para scroll al hash y loader) ===
document.addEventListener('DOMContentLoaded', function() {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ===== CURSOR PERSONALIZADO =====
  const cursor = document.querySelector('.custom-cursor');
  if (cursor) {
    document.addEventListener('mousemove', (e) => {
      cursor.style.left = e.clientX + 'px';
      cursor.style.top = e.clientY + 'px';
    });

    document.querySelectorAll('a, button').forEach(el => {
      el.addEventListener('mouseenter', () => cursor.classList.add('hover'));
      el.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
    });
  }

  // ===== EFECTO DE ESCRITURA DINÁMICA (TYPING) =====
  const typedElement = document.querySelector('.typed');
  if (typedElement) {
    const roles = ['Desarrollo web profesional', 'Dashboards en tiempo real', 'Automatización con Python', 'Integración de APIs', 'Frontend React y Vue', 'Chatbot para empresas'];
    let roleIndex = 0;
    let charIndex = 0;
    let isDeleting = false;

    function typeEffect() {
      const currentRole = roles[roleIndex];
      if (isDeleting) {
        typedElement.textContent = currentRole.substring(0, charIndex - 1);
        charIndex--;
      } else {
        typedElement.textContent = currentRole.substring(0, charIndex + 1);
        charIndex++;
      }

      if (!isDeleting && charIndex === currentRole.length) {
        isDeleting = true;
        setTimeout(typeEffect, 2000);
      } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        roleIndex = (roleIndex + 1) % roles.length;
        setTimeout(typeEffect, 500);
      } else {
        setTimeout(typeEffect, isDeleting ? 50 : 100);
      }
    }
    if (reduceMotion) {
      typedElement.textContent = roles[0];
    } else {
      typeEffect();
    }
  }

  // ===== LOADER (ocultar y luego forzar scroll al hash) =====
  const loader = document.getElementById('loader');
  if (loader) {
    // Ocultar inmediatamente con transición
    loader.style.transition = 'opacity 0.3s ease, visibility 0.3s ease';
    loader.style.opacity = '0';
    loader.style.visibility = 'hidden';
    setTimeout(() => {
      loader.style.display = 'none';
      
      // Después de quitar el loader, hacer scroll al hash si existe
      if (window.location.hash) {
        const targetId = window.location.hash.substring(1);
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
          // Pequeño retraso para asegurar que el DOM está listo
          setTimeout(() => {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 100);
        }
      }
    }, 300); // Tiempo suficiente para la transición de opacidad
  }

  // ===== NAVBAR =====
  const navbar = document.getElementById('navbar');
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('section');
  let lastScroll = 0;

  if (navbar) {
    window.addEventListener('scroll', function() {
      const currentScroll = window.pageYOffset;

      if (currentScroll > lastScroll && currentScroll > 100) {
        navbar.classList.add('hidden');
      } else {
        navbar.classList.remove('hidden');
      }
      lastScroll = currentScroll;

      // Resaltar sección activa
      if (sections.length && navLinks.length) {
        let current = '';
        sections.forEach(section => {
          const sectionTop = section.offsetTop - 100;
          const sectionHeight = section.clientHeight;
          if (pageYOffset >= sectionTop && pageYOffset < sectionTop + sectionHeight) {
            current = section.getAttribute('id');
          }
        });

        navLinks.forEach(link => {
          link.classList.remove('active');
          const href = link.getAttribute('href');
          if (href === `#${current}` || href === `index.html#${current}`) {
            link.classList.add('active');
          }
        });
      }

      // Botón volver arriba
      const backToTop = document.getElementById('backToTop');
      if (backToTop) {
        if (window.pageYOffset > 500) {
          backToTop.classList.add('visible');
        } else {
          backToTop.classList.remove('visible');
        }
      }
    }, { passive: true });
  }

  // ===== SCROLL SUAVE PARA ENLACES INTERNOS =====
  if (navLinks.length) {
    navLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        
        const isInternal = href === '#hero' || href === '#about' || href === '#services' || href === '#skills' || 
                           href === '#projects' || href === '#value' || href === '#contact' ||
                           href.startsWith('index.html#');
        
        if (isInternal) {
          let targetId = href;
          if (href.startsWith('index.html#')) {
            targetId = href.split('#')[1];
          } else {
            targetId = href.substring(1);
          }
          const targetElement = document.getElementById(targetId);
          if (targetElement) {
            e.preventDefault();
            targetElement.scrollIntoView({
              behavior: 'smooth',
              block: 'start'
            });
            // Actualizar hash sin scroll adicional
            history.pushState(null, null, '#' + targetId);
          }
        }
      });
    });
  }

  // Botón volver arriba
  const backToTopBtn = document.getElementById('backToTop');
  if (backToTopBtn) {
    backToTopBtn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ===== CHATBOT DEL PORTAFOLIO =====
  initPortfolioChatbot();
});

function initPortfolioChatbot() {
  if (document.querySelector('.chatbot-widget')) return;

  const relativeBase = document.querySelector('meta[name="relative-base"]')?.getAttribute('content') || '';
  const pageUrl = (path) => `${relativeBase}${path}`;
  const whatsappBudget = 'https://wa.me/50589871374?text=Hola%20Abraham,%20quiero%20un%20presupuesto%20para%20un%20proyecto';
  const linkedinUrl = 'https://www.linkedin.com/in/abrhamdev/';
  const githubUrl = 'https://github.com/jhernandez30-cpu';
  const instagramUrl = 'https://www.instagram.com/abrhamdev/';
  const youtubeUrl = 'https://www.youtube.com/@abrhamdev';
  const fallbackAnswer = {
    text: `Puedo guiarte por el sitio. Elige una ruta: <a href="${pageUrl('servicios/')}">servicios</a>, <a href="${pageUrl('proyectos/')}">casos de estudio</a>, <a href="${pageUrl('recursos/')}">blog/recursos</a>, <a href="${pageUrl('sobre-mi/')}">perfil profesional</a> o <a href="${pageUrl('contacto.html')}">contacto</a>. Si me dices tu problema, te recomiendo la página correcta.`,
    suggestions: ['Guíame', 'Servicios', 'Proyectos', 'Contacto']
  };
  const answers = [
    {
      keys: ['hola', 'buenas', 'hey', 'saludos', 'inicio', 'empezar', 'ayuda'],
      text: `Hola, soy el asistente virtual de Abraham. Puedo ayudarte a navegar el sitio, elegir un servicio, revisar proyectos, leer recursos o pedir presupuesto. Si no sabes por dónde empezar, dime qué quieres mejorar: ventas, datos, reportes, procesos manuales, APIs, atención al cliente o tu sitio web.`,
      suggestions: ['Guíame', 'Servicios', 'Proyectos', 'Contacto']
    },
    {
      keys: ['guia', 'guiame', 'orientame', 'recomienda', 'recomendacion', 'no se', 'no sé', 'que necesito', 'necesito ayuda', 'ruta'],
      text: `Te guío rápido: si necesitas visibilidad de datos, ve a <a href="${pageUrl('dashboards-tiempo-real/')}">dashboards</a>. Si repites tareas o reportes, ve a <a href="${pageUrl('automatizacion-procesos-python/')}">automatización con Python</a>. Si quieres una web o sistema interno, ve a <a href="${pageUrl('desarrollo-web-a-medida/')}">desarrollo web a medida</a>. Si quieres conectar herramientas, ve a <a href="${pageUrl('integracion-apis/')}">APIs</a>. Si quieres responder leads, ve a <a href="${pageUrl('chatbots-para-web/')}">chatbots</a>.`,
      suggestions: ['Dashboards', 'Automatización', 'Web a medida', 'Contacto']
    },
    {
      keys: ['mapa', 'navegar', 'sitio', 'secciones', 'paginas', 'páginas', 'menu', 'todo el sitio'],
      text: `Mapa del sitio: <a href="${pageUrl('index.html')}">Inicio</a>, <a href="${pageUrl('desarrollador-web-nicaragua/')}">desarrollador web en Nicaragua</a>, <a href="${pageUrl('servicios/')}">servicios</a>, <a href="${pageUrl('proyectos/')}">proyectos</a>, <a href="${pageUrl('recursos/')}">blog/recursos</a>, <a href="${pageUrl('sobre-mi/')}">sobre mí</a>, <a href="${pageUrl('titulos.html')}">títulos</a>, <a href="${pageUrl('interactua.html')}">herramientas IA</a>, <a href="${pageUrl('asistente-programacion.html')}">asistente de programación</a> y <a href="${pageUrl('contacto.html')}">contacto</a>.`,
      suggestions: ['Servicios', 'Proyectos', 'Recursos', 'Contacto']
    },
    {
      keys: ['servicio', 'servicios', 'haces', 'ofreces', 'oferta', 'desarrollo', 'web profesional'],
      text: `Abraham ofrece <a href="${pageUrl('servicios/')}">servicios digitales B2B</a>: <a href="${pageUrl('dashboards-tiempo-real/')}">dashboards en tiempo real</a>, <a href="${pageUrl('automatizacion-procesos-python/')}">automatización con Python</a>, <a href="${pageUrl('desarrollo-web-a-medida/')}">desarrollo web a medida</a>, <a href="${pageUrl('desarrollo-frontend-react-vue/')}">frontend React/Vue</a>, <a href="${pageUrl('integracion-apis/')}">integración de APIs</a> y <a href="${pageUrl('chatbots-para-web/')}">chatbots para web</a>.`,
      suggestions: ['Dashboards', 'Automatización', 'APIs', 'Chatbot']
    },
    {
      keys: ['desarrollador web nicaragua', 'nicaragua', 'local', 'perfil local', 'desarrollador web en nicaragua'],
      text: `La página principal para búsqueda local es <a href="${pageUrl('desarrollador-web-nicaragua/')}">Desarrollador web en Nicaragua</a>. Ahí se explica qué puede construir Abraham, cuándo contratarlo, proceso de trabajo, casos de estudio y formas de contacto.`,
      suggestions: ['Servicios', 'Sobre mí', 'CV', 'Contacto']
    },
    {
      keys: ['dashboard', 'dashboards', 'datos', 'metricas', 'métricas', 'kpi', 'reporte', 'reportes', 'tiempo real', 'alertas', 'websocket', 'socket'],
      text: `Si necesitas ver datos, KPIs o alertas en vivo, revisa <a href="${pageUrl('dashboards-tiempo-real/')}">dashboards en tiempo real</a>. Es ideal para operaciones, ventas, seguridad o soporte cuando el equipo no puede esperar reportes manuales.`,
      suggestions: ['Caso ITSA', 'Dashboard vs reporte', 'APIs', 'Contacto']
    },
    {
      keys: ['automatizacion', 'automatización', 'python', 'excel', 'manual', 'tarea repetitiva', 'tareas repetitivas', 'ahorrar tiempo', 'procesos', 'validacion', 'validación'],
      text: `Si tu equipo repite tareas, copia datos o arma reportes a mano, revisa <a href="${pageUrl('automatizacion-procesos-python/')}">automatización con Python</a>. También te conviene leer <a href="${pageUrl('recursos/que-procesos-automatizar-python/')}">qué procesos puede automatizar una empresa con Python</a>.`,
      suggestions: ['APIs', 'Reportes', 'Presupuesto', 'Recursos']
    },
    {
      keys: ['pagina web', 'página web', 'sitio web', 'sistema web', 'web a medida', 'landing', 'formulario', 'herramienta interna', 'panel interno'],
      text: `Si necesitas una página profesional, sistema interno, formulario o herramienta web propia, revisa <a href="${pageUrl('desarrollo-web-a-medida/')}">desarrollo web a medida</a>. Para enfoque local también puedes visitar <a href="${pageUrl('desarrollador-web-nicaragua/')}">desarrollador web en Nicaragua</a>.`,
      suggestions: ['Frontend', 'Servicios', 'Presupuesto', 'Proyectos']
    },
    {
      keys: ['frontend', 'react', 'vue', 'interfaz', 'interfaces', 'ui', 'producto digital', 'saas', 'panel administrativo'],
      text: `Para interfaces modernas, paneles administrativos, productos digitales o frontend conectado a APIs, revisa <a href="${pageUrl('desarrollo-frontend-react-vue/')}">frontend React y Vue</a>. Abraham trabaja con componentes, responsive, accesibilidad e integración con datos reales.`,
      suggestions: ['APIs', 'Proyectos', 'Tecnologías', 'Contacto']
    },
    {
      keys: ['api', 'apis', 'integracion', 'integración', 'webhook', 'conectar', 'sincronizar', 'crm', 'formularios', 'sistemas'],
      text: `Si necesitas conectar herramientas, formularios, CRM, bases de datos o servicios externos, revisa <a href="${pageUrl('integracion-apis/')}">integración de APIs</a>. También puedes leer <a href="${pageUrl('recursos/api-rest-vs-webhook/')}">API REST vs webhook</a>.`,
      suggestions: ['Automatización', 'APIs', 'Webhook', 'Contacto']
    },
    {
      keys: ['chatbot', 'bot', 'whatsapp', 'leads', 'cliente', 'clientes', 'atencion', 'atención', 'preguntas frecuentes', 'soporte'],
      text: `Si quieres atender consultas, captar leads o derivar usuarios a WhatsApp, revisa <a href="${pageUrl('chatbots-para-web/')}">chatbots para web</a>. Puedes ver el caso <a href="${pageUrl('proyectos/ai-chatbot/')}">AI Chatbot</a> para entender el enfoque.`,
      suggestions: ['AI Chatbot', 'Contacto', 'Servicios', 'IA']
    },
    {
      keys: ['proyecto', 'proyectos', 'portfolio', 'portafolio', 'demo', 'caso', 'casos', 'trabajos'],
      text: `En <a href="${pageUrl('proyectos/')}">Proyectos</a> encuentras casos de estudio: <a href="${pageUrl('proyectos/itsa-segurity/')}">ITSA Segurity</a>, <a href="${pageUrl('proyectos/dashboard-analytics/')}">Dashboard Analytics</a> y <a href="${pageUrl('proyectos/ai-chatbot/')}">AI Chatbot</a>. Cada caso muestra problema, solución, stack y resultado.`,
      suggestions: ['Caso ITSA', 'Dashboard Analytics', 'AI Chatbot', 'Servicios']
    },
    {
      keys: ['itsa', 'segurity', 'seguridad', 'monitoreo', 'incidentes'],
      text: `<a href="${pageUrl('proyectos/itsa-segurity/')}">ITSA Segurity</a> es un caso de dashboard con alertas en tiempo real para seguridad operativa. El stack incluye React, Socket.IO, Node.js y MongoDB, con foco en visibilidad y respuesta rápida.`,
      suggestions: ['Dashboards', 'Proyectos', 'Demo', 'Contacto']
    },
    {
      keys: ['analytics', 'marketing', 'dashboard analytics', 'analitica', 'analítica', 'visualizacion', 'visualización'],
      text: `<a href="${pageUrl('proyectos/dashboard-analytics/')}">Dashboard Analytics</a> muestra cómo convertir datos dispersos en un panel con filtros y KPIs para tomar decisiones de marketing más rápido.`,
      suggestions: ['Dashboards', 'Proyectos', 'Recursos', 'Contacto']
    },
    {
      keys: ['ai chatbot', 'asistente virtual', 'nlp', 'rasa'],
      text: `<a href="${pageUrl('proyectos/ai-chatbot/')}">AI Chatbot</a> es un caso de asistente virtual para responder consultas frecuentes, clasificar solicitudes y escalar a atención humana cuando hace falta.`,
      suggestions: ['Chatbot', 'IA', 'Contacto', 'Proyectos']
    },
    {
      keys: ['recurso', 'recursos', 'blog', 'guia', 'guía', 'articulo', 'artículo', 'leer', 'aprender'],
      text: `En <a href="${pageUrl('recursos/')}">Recursos</a> hay guías sobre automatización con Python, dashboards en tiempo real vs informes automáticos y API REST vs webhook. Es la mejor ruta si todavía estás evaluando qué solución necesitas.`,
      suggestions: ['Python guía', 'Dashboard vs reporte', 'API vs webhook', 'Servicios']
    },
    {
      keys: ['dashboard vs reporte', 'informe automatico', 'informe automático', 'reporte automatico', 'reporte automático'],
      text: `Si dudas entre datos en vivo o reportes programados, lee <a href="${pageUrl('recursos/dashboard-tiempo-real-vs-reporte-automatico/')}">dashboard en tiempo real vs informe automático</a>. Te ayuda a elegir según frecuencia de datos, urgencia y uso del equipo.`,
      suggestions: ['Dashboards', 'Recursos', 'Presupuesto', 'APIs']
    },
    {
      keys: ['api vs webhook', 'rest vs webhook', 'webhooks'],
      text: `La guía <a href="${pageUrl('recursos/api-rest-vs-webhook/')}">API REST vs webhook</a> explica cuándo consultar datos, cuándo recibir eventos y cómo conectar herramientas sin copiar y pegar.`,
      suggestions: ['APIs', 'Automatización', 'Recursos', 'Contacto']
    },
    {
      keys: ['tecnologia', 'tecnologias', 'tecnología', 'tecnologías', 'stack', 'javascript', 'typescript', 'sql', 'node', 'mongodb', 'postgresql', 'git'],
      text: `Stack principal: React, Vue, JavaScript, TypeScript, Python, APIs REST, SQL, WebSockets, Socket.IO, Node.js, bases de datos y Git/GitHub Actions. Para ver cómo se aplica, revisa <a href="${pageUrl('proyectos/')}">proyectos</a> o <a href="${pageUrl('sobre-mi/')}">sobre mí</a>.`,
      suggestions: ['Proyectos', 'Sobre mí', 'Frontend', 'APIs']
    },
    {
      keys: ['sobre mi', 'sobre mí', 'perfil', 'abraham', 'quien eres', 'quién eres', 'experiencia', 'forma de trabajo'],
      text: `En <a href="${pageUrl('sobre-mi/')}">Sobre mí</a> está el perfil profesional de Abraham: especialización, forma de trabajo, tecnologías, áreas donde aporta criterio y CTA para revisar un proyecto.`,
      suggestions: ['CV', 'Títulos', 'Tecnologías', 'Contacto']
    },
    {
      keys: ['titulo', 'titulos', 'título', 'títulos', 'certificacion', 'certificaciones', 'estudios', 'maestria', 'maestría', 'cv', 'curriculum', 'currículum'],
      text: `Puedes ver formación, títulos y certificaciones en <a href="${pageUrl('titulos.html')}">Títulos</a>. También puedes descargar el <a href="${pageUrl('cv.pdf')}">CV en PDF</a> para evaluar el perfil profesional.`,
      suggestions: ['Sobre mí', 'CV', 'Contacto', 'Tecnologías']
    },
    {
      keys: ['ia', 'ai', 'inteligencia artificial', 'agente', 'agentes', 'herramientas ia', 'notebooklm', 'interactua'],
      text: `En <a href="${pageUrl('interactua.html')}">Interactúa</a> hay herramientas IA y recursos para negocio/aprendizaje. También puedes visitar <a href="${pageUrl('asistente-programacion.html')}">Asistente de Programación</a> si quieres aprender o practicar conceptos técnicos.`,
      suggestions: ['Asistente programación', 'Chatbot', 'Recursos', 'Contacto']
    },
    {
      keys: ['asistente programacion', 'asistente programación', 'aprender programacion', 'aprender programación', 'programar', 'curso', 'ejercicios'],
      text: `El <a href="${pageUrl('asistente-programacion.html')}">Asistente de Programación</a> tiene rutas, preguntas, ejercicios, quiz y libros base para aprender programación de forma guiada.`,
      suggestions: ['Interactúa', 'Títulos', 'Recursos', 'Inicio']
    },
    {
      keys: ['contacto', 'correo', 'email', 'cotizar', 'contratar', 'precio', 'costo', 'presupuesto', 'disponible', 'disponibilidad', 'freelance', 'trabajo'],
      text: `Para solicitar presupuesto, escribe por <a href="${whatsappBudget}" target="_blank" rel="noopener">WhatsApp</a> o completa el formulario en <a href="${pageUrl('contacto.html')}">Contacto</a>. Incluye objetivo, proceso actual, herramientas existentes, fecha ideal, presupuesto aproximado y ejemplos de referencia.`,
      suggestions: ['WhatsApp', 'Servicios', 'Proyectos', 'CV']
    },
    {
      keys: ['linkedin', 'github', 'instagram', 'youtube', 'redes', 'social', 'whatsapp'],
      text: `Redes y contacto: <a href="${whatsappBudget}" target="_blank" rel="noopener">WhatsApp</a>, <a href="${linkedinUrl}" target="_blank" rel="noopener">LinkedIn</a>, <a href="${githubUrl}" target="_blank" rel="noopener">GitHub</a>, <a href="${instagramUrl}" target="_blank" rel="noopener">Instagram</a> y <a href="${youtubeUrl}" target="_blank" rel="noopener">YouTube</a>.`,
      suggestions: ['Contacto', 'GitHub', 'LinkedIn', 'CV']
    },
    {
      keys: ['faq', 'preguntas frecuentes', 'google', 'chatgpt', 'seo'],
      text: `La home incluye una sección FAQ para Google y ChatGPT con respuestas sobre servicios, dashboards, automatización, chatbots y presupuesto. También está el archivo <a href="${pageUrl('llms.txt')}">llms.txt</a> para resumir el sitio a sistemas de IA.`,
      suggestions: ['Recursos', 'Servicios', 'Mapa del sitio', 'Contacto']
    }
  ];

  const quickReplies = ['Guíame', 'Servicios', 'Proyectos', 'Recursos', 'Contacto'];
  const widget = document.createElement('div');
  widget.className = 'chatbot-widget';
  widget.innerHTML = `
    <div class="chatbot-panel" role="dialog" aria-label="Chatbot del portafolio" aria-hidden="true">
      <div class="chatbot-header">
        <div class="chatbot-title">
          <div class="chatbot-avatar"><i class="fas fa-robot"></i></div>
          <div>
            <strong>Asistente JAH</strong>
            <span><span class="chatbot-status-dot"></span>Disponible ahora</span>
          </div>
        </div>
        <button class="chatbot-close" type="button" aria-label="Cerrar chat"><i class="fas fa-times"></i></button>
      </div>
      <div class="chatbot-messages" aria-live="polite"></div>
      <div class="chatbot-actions">
        <a href="${pageUrl('contacto.html')}" class="chatbot-action">Contacto</a>
        <a href="https://wa.me/50589871374?text=Hola%20Abraham,%20quiero%20un%20presupuesto%20para%20un%20proyecto" target="_blank" rel="noopener" class="chatbot-action">WhatsApp</a>
      </div>
      <div class="chatbot-quick-replies" aria-label="Preguntas rapidas"></div>
      <form class="chatbot-form">
        <input class="chatbot-input" type="text" placeholder="Escribe tu pregunta..." aria-label="Mensaje para el chatbot" autocomplete="off">
        <button class="chatbot-send" type="submit" aria-label="Enviar mensaje"><i class="fas fa-paper-plane"></i></button>
      </form>
    </div>
    <button class="chatbot-toggle" type="button" aria-label="Abrir chat"><i class="fas fa-comments"></i></button>
  `;

  document.body.appendChild(widget);

  const panel = widget.querySelector('.chatbot-panel');
  const toggle = widget.querySelector('.chatbot-toggle');
  const closeBtn = widget.querySelector('.chatbot-close');
  const messages = widget.querySelector('.chatbot-messages');
  const form = widget.querySelector('.chatbot-form');
  const input = widget.querySelector('.chatbot-input');
  const chips = widget.querySelector('.chatbot-quick-replies');

  function addMessage(content, type) {
    const message = document.createElement('div');
    message.className = `chatbot-message ${type}`;
    message.innerHTML = content;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    const typing = document.createElement('div');
    typing.className = 'chatbot-message bot chatbot-typing';
    typing.setAttribute('aria-label', 'El asistente esta escribiendo');
    typing.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;
    return typing;
  }

  function normalize(text) {
    return text
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  }

  function getAnswer(question) {
    const cleanQuestion = normalize(question);
    const rankedAnswers = answers
      .map(item => ({
        ...item,
        score: item.keys.reduce((score, key) => score + (cleanQuestion.includes(normalize(key)) ? 1 : 0), 0)
      }))
      .sort((a, b) => b.score - a.score);
    const match = rankedAnswers.find(item => item.score > 0);

    if (match) return match;

    return fallbackAnswer;
  }

  function renderQuickReplies(labels = quickReplies) {
    chips.innerHTML = '';
    labels.forEach(label => {
      const chip = document.createElement('button');
      chip.className = 'chatbot-chip';
      chip.type = 'button';
      chip.textContent = label;
      chip.addEventListener('click', () => sendQuestion(label));
      chips.appendChild(chip);
      addHoverEffect(chip);
    });
  }

  function addHoverEffect(element) {
    const cursor = document.querySelector('.custom-cursor');
    if (!cursor) return;
    element.addEventListener('mouseenter', () => cursor.classList.add('hover'));
    element.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
  }

  function sendQuestion(question) {
    const trimmed = question.trim();
    if (!trimmed) return;

    addMessage(trimmed.replace(/[<>&]/g, char => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[char])), 'user');
    input.value = '';
    input.disabled = true;
    const typing = showTyping();

    setTimeout(() => {
      const answer = getAnswer(trimmed);
      typing.remove();
      addMessage(answer.text, 'bot');
      renderQuickReplies(answer.suggestions);
      input.disabled = false;
      input.focus();
    }, 550);
  }

  renderQuickReplies();
  widget.querySelectorAll('a, button').forEach(addHoverEffect);

  toggle.addEventListener('click', () => {
    const isOpen = widget.classList.toggle('open');
    panel.setAttribute('aria-hidden', String(!isOpen));
    toggle.setAttribute('aria-label', isOpen ? 'Cerrar chat' : 'Abrir chat');
    if (isOpen) input.focus();
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && widget.classList.contains('open')) {
      widget.classList.remove('open');
      panel.setAttribute('aria-hidden', 'true');
      toggle.setAttribute('aria-label', 'Abrir chat');
      toggle.focus();
    }
  });

  closeBtn.addEventListener('click', () => {
    widget.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
    toggle.setAttribute('aria-label', 'Abrir chat');
    toggle.focus();
  });

  form.addEventListener('submit', event => {
    event.preventDefault();
    sendQuestion(input.value);
  });

  addMessage('Hola, soy el asistente virtual de Abraham. Puedo guiarte por todo el sitio: servicios, proyectos, recursos, perfil, CV, redes o presupuesto. Escribe tu necesidad o toca una opción.', 'bot');
}
