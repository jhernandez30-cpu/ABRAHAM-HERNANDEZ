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
  const jahAvatarUrl = pageUrl('assets/img/jah-avatar.png');
  const fallbackAnswer = {
    text: `Puedo guiarte por el sitio. Elige una ruta: <a href="${pageUrl('servicios/')}">servicios</a>, <a href="${pageUrl('proyectos/')}">casos de estudio</a>, <a href="${pageUrl('recursos/')}">blog/recursos</a>, <a href="${pageUrl('sobre-mi/')}">perfil profesional</a> o <a href="${pageUrl('contacto.html')}">contacto</a>. Si me dices tu problema, te recomiendo la página correcta.`,
    suggestions: ['Mapa del sitio', 'Servicios', 'Proyectos', 'Contacto']
  };
  const answers = [
    {
      keys: ['hola', 'buenas', 'hey', 'saludos', 'inicio', 'empezar', 'ayuda'],
      text: `Hola, soy JAH, el asistente virtual de Abraham. Puedo ayudarte a navegar el sitio, elegir un servicio, revisar proyectos, conocer títulos y experiencia, ver recursos o pedir presupuesto. Si no sabes por dónde empezar, dime qué quieres mejorar: ventas, datos, reportes, procesos manuales, APIs, atención al cliente o tu sitio web.`,
      suggestions: ['Guíame', 'Servicios', 'Proyectos', 'Contacto']
    },
    {
      keys: ['jah', 'joshue', 'josue', 'josué', 'abraham hernandez', 'abraham hernández', 'quien es', 'quién es', 'perfil profesional', 'ingeniero en sistemas'],
      text: `Josué Abraham Hernández es Ingeniero en Sistemas y desarrollador web en Nicaragua. Su perfil combina desarrollo web, software, bases de datos, ciberseguridad e inteligencia artificial para crear soluciones digitales empresariales: sitios profesionales, dashboards, automatizaciones, APIs y chatbots.`,
      suggestions: ['Sobre mí', 'Servicios', 'Títulos', 'Contacto']
    },
    {
      keys: ['guia', 'guiame', 'orientame', 'recomienda', 'recomendacion', 'no se', 'no sé', 'que necesito', 'necesito ayuda', 'ruta'],
      text: `Te guío rápido: si necesitas visibilidad de datos, ve a <a href="${pageUrl('dashboards-tiempo-real/')}">dashboards</a>. Si repites tareas o reportes, ve a <a href="${pageUrl('automatizacion-procesos-python/')}">automatización con Python</a>. Si quieres una web o sistema interno, ve a <a href="${pageUrl('desarrollo-web-a-medida/')}">desarrollo web a medida</a>. Si quieres conectar herramientas, ve a <a href="${pageUrl('integracion-apis/')}">APIs</a>. Si quieres responder leads, ve a <a href="${pageUrl('chatbots-para-web/')}">chatbots</a>.`,
      suggestions: ['Dashboards', 'Automatización', 'Web a medida', 'Contacto']
    },
    {
      keys: ['mapa', 'navegar', 'sitio', 'secciones', 'paginas', 'páginas', 'menu', 'todo el sitio'],
      text: `Mapa del sitio: <a href="${pageUrl('index.html')}">Inicio</a>, <a href="${pageUrl('desarrollador-web-nicaragua/')}">desarrollador web en Nicaragua</a>, <a href="${pageUrl('servicios/')}">servicios</a>, <a href="${pageUrl('proyectos/')}">proyectos</a>, <a href="${pageUrl('recursos/')}">blog/recursos</a>, <a href="${pageUrl('sobre-mi/')}">sobre mí</a>, <a href="${pageUrl('titulos.html')}">títulos y experiencia</a>, <a href="${pageUrl('interactua.html')}">herramientas IA</a>, <a href="${pageUrl('asistente-programacion.html')}">asistente de programación</a>, <a href="${pageUrl('jah/')}">Marca JAH</a> y <a href="${pageUrl('contacto.html')}">contacto</a>.`,
      suggestions: ['Servicios', 'Proyectos', 'Recursos', 'Contacto']
    },
    {
      keys: ['servicio', 'servicios', 'haces', 'ofreces', 'oferta', 'desarrollo', 'web profesional'],
      text: `Abraham ofrece <a href="${pageUrl('servicios/')}">servicios digitales B2B</a>: <a href="${pageUrl('dashboards-tiempo-real/')}">dashboards en tiempo real</a>, <a href="${pageUrl('automatizacion-procesos-python/')}">automatización con Python</a>, <a href="${pageUrl('desarrollo-web-a-medida/')}">desarrollo web a medida</a>, <a href="${pageUrl('desarrollo-frontend-react-vue/')}">frontend React/Vue</a>, <a href="${pageUrl('integracion-apis/')}">integración de APIs</a> y <a href="${pageUrl('chatbots-para-web/')}">chatbots para web</a>.`,
      suggestions: ['Dashboards', 'Automatización', 'APIs', 'Chatbot']
    },
    {
      keys: ['habilidades', 'skills', 'html', 'css', 'javascript', 'python', 'c#', 'c sharp', 'sql', 'power bi', 'ciberseguridad', 'bases de datos', 'desarrollo web', 'inteligencia artificial'],
      text: `Habilidades destacadas del sitio: HTML, CSS, JavaScript, Python, C#, SQL, Power BI, bases de datos, desarrollo web, APIs, automatización, ciberseguridad e inteligencia artificial. En la home también aparece la sección de tecnologías y áreas de especialidad.`,
      suggestions: ['Tecnologías', 'Servicios', 'Proyectos', 'Títulos']
    },
    {
      keys: ['desarrollador web nicaragua', 'nicaragua', 'local', 'perfil local', 'desarrollador web en nicaragua'],
      text: `La página principal para búsqueda local es <a href="${pageUrl('desarrollador-web-nicaragua/')}">Desarrollador web en Nicaragua</a>. Ahí se explica qué puede construir Abraham, cuándo contratarlo, proceso de trabajo, casos de estudio y formas de contacto.`,
      suggestions: ['Servicios', 'Sobre mí', 'CV', 'Contacto']
    },
    {
      keys: ['dashboard', 'dashboards', 'datos', 'metricas', 'métricas', 'kpi', 'reporte', 'reportes', 'tiempo real', 'alertas', 'websocket', 'socket'],
      text: `Si necesitas ver datos, KPIs o alertas en vivo, revisa <a href="${pageUrl('dashboards-tiempo-real/')}">dashboards en tiempo real</a>. Es ideal para operaciones, ventas, seguridad o soporte cuando el equipo no puede esperar reportes manuales.`,
      suggestions: ['ITSA Segurity', 'Dashboard vs reporte', 'APIs', 'Contacto']
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
      text: `En <a href="${pageUrl('proyectos/')}">Proyectos</a> aparecen proyectos reales como <a href="https://jhernandez30-cpu.github.io/ciencia-sociales/museo-sandino.html" target="_blank" rel="noopener">Mural Interactivo Sandino</a>, <a href="${pageUrl('proyectos/dashboard-analytics/')}">Dashboard Analytics</a>, <a href="${pageUrl('proyectos/ai-chatbot/')}">AI Chatbot</a>, <a href="${pageUrl('jah/')}">Marca JAH</a> y <a href="https://jhernandez30-cpu.github.io/Variedades-Nora/" target="_blank" rel="noopener">Variedades Nora</a>. <a href="${pageUrl('proyectos/itsa-segurity/')}">ITSA Segurity</a> queda conectado como mi empresa, no como proyecto de portafolio.`,
      suggestions: ['Sandino', 'Variedades Nora', 'ITSA Segurity', 'Servicios']
    },
    {
      keys: ['itsa', 'segurity', 'seguridad', 'monitoreo', 'incidentes', 'empresa', 'mi empresa'],
      text: `<a href="${pageUrl('proyectos/itsa-segurity/')}">ITSA Segurity</a> es mi empresa, conectada al portafolio como marca empresarial orientada a seguridad, monitoreo, tecnología y soluciones digitales. También puedes abrir el <a href="https://jhernandez30-cpu.github.io/ITSA-Segurity/" target="_blank" rel="noopener">sitio público de ITSA Segurity</a> o escribirme para hablar de una solución relacionada.`,
      suggestions: ['Dashboards', 'Empresa', 'Contacto', 'Servicios']
    },
    {
      keys: ['analytics', 'marketing', 'dashboard analytics', 'analitica', 'analítica', 'visualizacion', 'visualización'],
      text: `<a href="${pageUrl('proyectos/dashboard-analytics/')}">Dashboard Analytics</a> muestra cómo convertir datos dispersos en un panel con filtros y KPIs para tomar decisiones de marketing más rápido.`,
      suggestions: ['Dashboards', 'Proyectos', 'Recursos', 'Contacto']
    },
    {
      keys: ['sandino', 'mural sandino', 'museo sandino', 'museo digital', 'ciencia sociales', 'ciencias sociales', 'augusto sandino'],
      text: `El <a href="https://jhernandez30-cpu.github.io/ciencia-sociales/museo-sandino.html" target="_blank" rel="noopener">Mural Interactivo Sandino</a> es un proyecto educativo/museo digital sobre el General Augusto Nicolás Calderón Sandino. Está integrado en el portafolio como proyecto real con enlace público.`,
      suggestions: ['Proyectos', 'Recursos', 'Servicios', 'Contacto']
    },
    {
      keys: ['variedades nora', 'nora', 'ecommerce', 'e-commerce', 'tienda', 'tienda online'],
      text: `<a href="https://jhernandez30-cpu.github.io/Variedades-Nora/" target="_blank" rel="noopener">Variedades Nora</a> aparece como proyecto de e-commerce/tienda online dentro del portafolio. Puedes verlo desde la sección de proyectos de la home.`,
      suggestions: ['Proyectos', 'Web a medida', 'Contacto', 'Servicios']
    },
    {
      keys: ['marca jah', 'jah marca', 'logo jah', 'ropa jah', 'tienda jah', 'marca'],
      text: `<a href="${pageUrl('jah/')}">Marca JAH</a> es una página visual de marca con estética deportiva/premium. En el portafolio aparece como proyecto de marca y experiencia visual.`,
      suggestions: ['Proyectos', 'Inicio', 'Contacto', 'Servicios']
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
      text: `Stack y áreas del sitio: React, Vue, JavaScript, TypeScript, Python, APIs REST, SQL, WebSockets, Socket.IO, Node.js, bases de datos, Power BI, ciberseguridad y Git/GitHub Actions. Para ver cómo se aplica, revisa <a href="${pageUrl('proyectos/')}">proyectos</a> o <a href="${pageUrl('sobre-mi/')}">sobre mí</a>.`,
      suggestions: ['Proyectos', 'Sobre mí', 'Frontend', 'APIs']
    },
    {
      keys: ['sobre mi', 'sobre mí', 'perfil', 'abraham', 'quien eres', 'quién eres', 'experiencia', 'forma de trabajo'],
      text: `En <a href="${pageUrl('sobre-mi/')}">Sobre mí</a> está el perfil profesional de Abraham: especialización, forma de trabajo, tecnologías, áreas donde aporta criterio y CTA para revisar un proyecto.`,
      suggestions: ['CV', 'Títulos', 'Tecnologías', 'Contacto']
    },
    {
      keys: ['titulo', 'titulos', 'título', 'títulos', 'certificacion', 'certificaciones', 'estudios', 'maestria', 'maestría', 'cv', 'curriculum', 'currículum'],
      text: `Puedes ver <a href="${pageUrl('titulos.html')}">Títulos, formación y experiencia</a>: Ingeniero en Sistema de Informática por la Universidad Nacional Héroes de San José de las Mulas, Máster en Desarrollo con IA, Máster en Ciberseguridad, Power BI, Data Science, Marketing Digital con IA y SEO para IA y Google. También puedes descargar el <a href="${pageUrl('cv.pdf')}">CV en PDF</a>.`,
      suggestions: ['Sobre mí', 'CV', 'Contacto', 'Tecnologías']
    },
    {
      keys: ['indicadores', 'años', 'anos', 'practica tecnica', 'práctica técnica', 'areas de servicio', 'demos'],
      text: `La home muestra indicadores reales: 5 años de práctica técnica, 15 proyectos y demos, y 5 áreas de servicio. No se usan estadísticas falsas de clientes, premios o ventas.`,
      suggestions: ['Proyectos', 'Servicios', 'Sobre mí', 'Contacto']
    },
    {
      keys: ['ia', 'ai', 'inteligencia artificial', 'agente', 'agentes', 'herramientas ia', 'notebooklm', 'interactua'],
      text: `En <a href="${pageUrl('interactua.html')}">Interactúa</a> hay herramientas IA para captación de cliente, análisis de competencia, estrategia, seguridad, desarrollo, bases de datos y C#. También incluye libros NotebookLM de programación, Python, C#, bases de datos, Power BI, ciberseguridad y agente N8N. Para practicar código, abre <a href="${pageUrl('asistente-programacion.html')}">Asistente de Programación</a>.`,
      suggestions: ['Asistente programación', 'Chatbot', 'Recursos', 'Contacto']
    },
    {
      keys: ['asistente programacion', 'asistente programación', 'aprender programacion', 'aprender programación', 'programar', 'curso', 'ejercicios'],
      text: `El <a href="${pageUrl('asistente-programacion.html')}">Asistente de Programación</a> tiene rutas, preguntas, ejercicios, quiz y libros base para aprender programación de forma guiada.`,
      suggestions: ['Interactúa', 'Títulos', 'Recursos', 'Inicio']
    },
    {
      keys: ['contacto', 'correo', 'email', 'cotizar', 'contratar', 'precio', 'costo', 'presupuesto', 'disponible', 'disponibilidad', 'freelance', 'trabajo'],
      text: `Para solicitar presupuesto, escribe por <a href="${whatsappBudget}" target="_blank" rel="noopener">WhatsApp al +505 8987 1374</a> o completa el formulario en <a href="${pageUrl('contacto.html')}">Contacto</a>. Incluye objetivo, proceso actual, herramientas existentes, fecha ideal, presupuesto aproximado y ejemplos de referencia.`,
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

  const quickReplies = ['Mapa del sitio', 'Servicios', 'Proyectos', 'Títulos', 'Contacto'];
  const widget = document.createElement('div');
  widget.className = 'chatbot-widget';
  widget.innerHTML = `
    <div class="chatbot-panel" role="dialog" aria-label="Chatbot del portafolio" aria-hidden="true">
      <div class="chatbot-header">
        <div class="chatbot-title">
          <div class="chatbot-avatar">
            <img class="jah-header-avatar" src="${jahAvatarUrl}" alt="Avatar de JAH" loading="lazy" decoding="async">
          </div>
          <div>
            <strong>JAH</strong>
            <span><span class="chatbot-status-dot"></span>Asistente virtual</span>
          </div>
        </div>
        <button class="chatbot-close" type="button" aria-label="Cerrar chat"><i class="fas fa-times"></i></button>
      </div>
      <div class="chatbot-messages" aria-live="polite"></div>
      <div class="chatbot-menu">
        <button class="chatbot-menu-toggle" type="button" aria-expanded="false">
          <span><i class="fas fa-list"></i> Menú de JAH</span>
          <i class="fas fa-chevron-down" aria-hidden="true"></i>
        </button>
        <div class="chatbot-menu-panel" hidden>
          <div class="chatbot-menu-section">
            <span class="chatbot-menu-label">Preguntas sugeridas</span>
            <div class="chatbot-menu-options" aria-label="Preguntas sugeridas"></div>
          </div>
          <div class="chatbot-menu-section">
            <span class="chatbot-menu-label">Enlaces rápidos</span>
            <a href="${pageUrl('index.html')}" class="chatbot-menu-link">Inicio</a>
            <a href="${pageUrl('sobre-mi/')}" class="chatbot-menu-link">Sobre mí</a>
            <a href="${pageUrl('servicios/')}" class="chatbot-menu-link">Servicios</a>
            <a href="${pageUrl('proyectos/')}" class="chatbot-menu-link">Proyectos</a>
            <a href="${pageUrl('recursos/')}" class="chatbot-menu-link">Recursos</a>
            <a href="${pageUrl('titulos.html')}" class="chatbot-menu-link">Títulos y experiencia</a>
            <a href="${pageUrl('interactua.html')}" class="chatbot-menu-link">Interactúa</a>
            <a href="${pageUrl('asistente-programacion.html')}" class="chatbot-menu-link">Asistente programación</a>
            <a href="${pageUrl('cv.pdf')}" class="chatbot-menu-link" download>Descargar CV</a>
            <a href="${pageUrl('contacto.html')}" class="chatbot-menu-link">Contacto</a>
            <a href="https://wa.me/50589871374?text=Hola%20Abraham,%20quiero%20un%20presupuesto%20para%20un%20proyecto" target="_blank" rel="noopener" class="chatbot-menu-link">WhatsApp</a>
            <a href="${linkedinUrl}" target="_blank" rel="noopener" class="chatbot-menu-link">LinkedIn</a>
            <a href="${githubUrl}" target="_blank" rel="noopener" class="chatbot-menu-link">GitHub</a>
          </div>
        </div>
      </div>
      <form class="chatbot-form">
        <input class="chatbot-input" type="text" placeholder="Escribe tu pregunta..." aria-label="Mensaje para el chatbot" autocomplete="off">
        <button class="chatbot-send" type="submit" aria-label="Enviar mensaje"><i class="fas fa-paper-plane"></i></button>
      </form>
    </div>
    <button class="chatbot-toggle" type="button" aria-label="Abrir chat">
      <img class="jah-floating-avatar" src="${jahAvatarUrl}" alt="Abrir chatbot JAH" loading="lazy" decoding="async">
    </button>
  `;

  document.body.appendChild(widget);

  const panel = widget.querySelector('.chatbot-panel');
  const toggle = widget.querySelector('.chatbot-toggle');
  const closeBtn = widget.querySelector('.chatbot-close');
  const messages = widget.querySelector('.chatbot-messages');
  const form = widget.querySelector('.chatbot-form');
  const input = widget.querySelector('.chatbot-input');
  const menuToggle = widget.querySelector('.chatbot-menu-toggle');
  const menuPanel = widget.querySelector('.chatbot-menu-panel');
  const menuOptions = widget.querySelector('.chatbot-menu-options');

  function addMessage(content, type) {
    const message = document.createElement('div');
    message.className = `chatbot-message ${type}`;
    message.innerHTML = content;
    if (type === 'bot') {
      const row = document.createElement('div');
      row.className = 'chatbot-message-row bot';
      const avatar = document.createElement('img');
      avatar.className = 'jah-bot-avatar';
      avatar.src = jahAvatarUrl;
      avatar.alt = 'JAH';
      avatar.loading = 'lazy';
      avatar.decoding = 'async';
      row.appendChild(avatar);
      row.appendChild(message);
      messages.appendChild(row);
    } else {
      messages.appendChild(message);
    }
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
    menuOptions.innerHTML = '';
    labels.forEach(label => {
      const option = document.createElement('button');
      option.className = 'chatbot-menu-item';
      option.type = 'button';
      option.textContent = label;
      option.addEventListener('click', () => {
        setMenuOpen(false);
        sendQuestion(label);
      });
      menuOptions.appendChild(option);
      addHoverEffect(option);
    });
  }

  function setMenuOpen(open) {
    menuToggle.setAttribute('aria-expanded', String(open));
    menuPanel.hidden = !open;
    widget.classList.toggle('menu-open', open);
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

  menuToggle.addEventListener('click', () => {
    setMenuOpen(menuPanel.hidden);
  });

  toggle.addEventListener('click', () => {
    const isOpen = widget.classList.toggle('open');
    panel.setAttribute('aria-hidden', String(!isOpen));
    toggle.setAttribute('aria-label', isOpen ? 'Cerrar chat' : 'Abrir chat');
    if (isOpen) input.focus();
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !menuPanel.hidden) {
      setMenuOpen(false);
      menuToggle.focus();
      return;
    }
    if (event.key === 'Escape' && widget.classList.contains('open')) {
      widget.classList.remove('open');
      panel.setAttribute('aria-hidden', 'true');
      toggle.setAttribute('aria-label', 'Abrir chat');
      toggle.focus();
    }
  });

  closeBtn.addEventListener('click', () => {
    setMenuOpen(false);
    widget.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
    toggle.setAttribute('aria-label', 'Abrir chat');
    toggle.focus();
  });

  form.addEventListener('submit', event => {
    event.preventDefault();
    setMenuOpen(false);
    sendQuestion(input.value);
  });

  addMessage('Hola, soy JAH, el asistente virtual de Abraham. Puedo guiarte por todo el sitio: servicios, proyectos, recursos, perfil, títulos, experiencia, CV, redes o presupuesto. Escribe tu necesidad o abre el menú desplegable.', 'bot');
}
