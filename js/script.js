// === script.js (versión ajustada para scroll al hash y loader) ===
document.addEventListener('DOMContentLoaded', function() {
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
    const roles = ['Dashboards en tiempo real', 'Automatización con Python', 'Frontend React/Vue', 'Integración de APIs'];
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
    typeEffect();
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
    });
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

  const storageKey = 'jah-chatbot-history';
  const relativeBase = document.querySelector('meta[name="relative-base"]')?.getAttribute('content') || '';
  const pageUrl = (path) => `${relativeBase}${path}`;
  const fallbackAnswer = {
    text: `Puedo ayudarte con servicios, proyectos, tecnologías, títulos, disponibilidad o contacto. Si necesitas una respuesta humana, escribe por <a href="https://wa.me/50589871374?text=Hola%20Abraham,%20quiero%20hablar%20sobre%20un%20proyecto" target="_blank" rel="noopener">WhatsApp</a>.`,
    suggestions: ['Servicios', 'Cotizar', 'Contacto']
  };
  const answers = [
    {
      keys: ['hola', 'buenas', 'hey', 'saludos', 'inicio'],
      text: 'Hola, soy el asistente virtual de Abraham. Puedo orientarte sobre servicios, proyectos, tecnologías, disponibilidad y formas de contacto.',
      suggestions: ['Servicios', 'Proyectos', 'Cotizar']
    },
    {
      keys: ['servicio', 'servicios', 'haces', 'ofreces', 'desarrollo', 'web', 'pagina', 'sitio', 'sistema'],
      text: `Abraham puede ayudarte con <a href="${pageUrl('dashboards-tiempo-real/')}">dashboards en tiempo real</a>, <a href="${pageUrl('automatizacion-procesos-python/')}">automatización con Python</a>, <a href="${pageUrl('desarrollo-frontend-react-vue/')}">frontend React/Vue</a>, <a href="${pageUrl('integracion-apis/')}">integración de APIs</a> y <a href="${pageUrl('chatbots-para-web/')}">chatbots para web</a>.`,
      suggestions: ['Cotizar', 'Tecnologías', 'Proyectos']
    },
    {
      keys: ['proyecto', 'proyectos', 'portfolio', 'portafolio', 'demo'],
      text: `En el portafolio destacan ITSA Segurity, Dashboard Analytics y AI Chatbot. Puedes revisar <a href="${pageUrl('proyectos/')}">Proyectos</a> para ver casos y resultados.`,
      suggestions: ['Servicios', 'IA', 'Contacto']
    },
    {
      keys: ['tecnologia', 'tecnologias', 'stack', 'vue', 'react', 'python', 'api', 'socket', 'javascript', 'typescript'],
      text: 'Su stack principal incluye Vue, React, JavaScript, TypeScript, Python, APIs REST, SQL, WebSockets, Socket.IO, Git y GitHub Actions.',
      suggestions: ['Proyectos', 'Servicios', 'Cotizar']
    },
    {
      keys: ['contacto', 'whatsapp', 'correo', 'email', 'cotizar', 'contratar', 'precio', 'costo', 'presupuesto'],
      text: `Para cotizar, escribe por <a href="https://wa.me/50589871374?text=Hola%20Abraham,%20quiero%20cotizar%20un%20proyecto" target="_blank" rel="noopener">WhatsApp</a> o completa el formulario en <a href="${pageUrl('contacto.html')}">Contacto</a>. Incluye objetivo, fecha ideal, presupuesto aproximado y ejemplos de referencia.`,
      suggestions: ['Servicios', 'Disponibilidad', 'Proyectos']
    },
    {
      keys: ['disponible', 'disponibilidad', 'freelance', 'trabajo'],
      text: 'Actualmente el portafolio indica disponibilidad para proyectos freelance y colaboraciones. Lo ideal es enviar un resumen del proyecto para recibir una respuesta clara en menos de 24 horas.',
      suggestions: ['Cotizar', 'Contacto', 'Servicios']
    },
    {
      keys: ['titulo', 'certificacion', 'certificaciones', 'estudios', 'maestria'],
      text: `Puedes ver formación, títulos y certificaciones en la página de <a href="${pageUrl('titulos.html')}">Títulos</a>.`,
      suggestions: ['Tecnologías', 'Proyectos', 'Contacto']
    },
    {
      keys: ['ia', 'ai', 'chatbot', 'automatizacion', 'agente'],
      text: `Abraham trabaja con automatización, agentes y herramientas de IA. También hay recursos interactivos en <a href="${pageUrl('interactua.html')}">Interactúa</a> y puede crear asistentes para responder preguntas frecuentes o captar prospectos.`,
      suggestions: ['Cotizar', 'Servicios', 'Tecnologías']
    }
  ];

  const quickReplies = ['Servicios', 'Proyectos', 'Tecnologías', 'Cotizar'];
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
        <a href="https://wa.me/50589871374?text=Hola%20Abraham,%20quiero%20cotizar%20un%20proyecto" target="_blank" rel="noopener" class="chatbot-action">WhatsApp</a>
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
  let chatHistory = loadHistory();

  function saveHistory() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(chatHistory.slice(-16)));
    } catch (error) {
      chatHistory = chatHistory.slice(-16);
    }
  }

  function addMessage(content, type, shouldSave = true) {
    const message = document.createElement('div');
    message.className = `chatbot-message ${type}`;
    message.innerHTML = content;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;

    if (shouldSave) {
      chatHistory.push({ content, type });
      saveHistory();
    }
  }

  function loadHistory() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || '[]');
      return Array.isArray(saved) ? saved : [];
    } catch (error) {
      return [];
    }
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

  if (chatHistory.length) {
    chatHistory.forEach(item => addMessage(item.content, item.type, false));
  } else {
    addMessage('Hola, soy el asistente virtual de Abraham. Pregúntame por servicios, proyectos, tecnologías o cómo cotizar.', 'bot');
  }
}
