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
    const roles = ['Web Developer', 'Software Engineer', 'Freelancer', 'AI Enthusiast'];
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
        
        const isInternal = href === '#hero' || href === '#about' || href === '#skills' || 
                           href === '#projects' || href === '#value' || href === '#contact' ||
                           href.startsWith('index.html#');
        
        if (isInternal) {
          e.preventDefault();
          let targetId = href;
          if (href.startsWith('index.html#')) {
            targetId = href.split('#')[1];
          } else {
            targetId = href.substring(1);
          }
          const targetElement = document.getElementById(targetId);
          if (targetElement) {
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
});
