// === script.js (funcionalidades adicionales) ===
document.addEventListener('DOMContentLoaded', function() {
  // ===== CURSOR PERSONALIZADO =====
  const cursor = document.querySelector('.custom-cursor');
  document.addEventListener('mousemove', (e) => {
    cursor.style.left = e.clientX + 'px';
    cursor.style.top = e.clientY + 'px';
  });

  document.querySelectorAll('a, button').forEach(el => {
    el.addEventListener('mouseenter', () => cursor.classList.add('hover'));
    el.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
  });

  // ===== EFECTO DE ESCRITURA DINÁMICA (TYPING) =====
  const typedElement = document.querySelector('.typed');
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

  // ===== LOADER (ocultar inmediatamente) =====
  const loader = document.getElementById('loader');
  if (loader) {
    loader.style.opacity = '0';
    loader.style.visibility = 'hidden';
    setTimeout(() => {
      loader.style.display = 'none';
    }, 100); // Reducido a 100ms para que desaparezca rápido
  }

  // ===== NAVBAR =====
  const navbar = document.getElementById('navbar');
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('section');
  let lastScroll = 0;

  window.addEventListener('scroll', function() {
    const currentScroll = window.pageYOffset;

    if (currentScroll > lastScroll && currentScroll > 100) {
      navbar.classList.add('hidden');
    } else {
      navbar.classList.remove('hidden');
    }
    lastScroll = currentScroll;

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
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });

    const backToTop = document.getElementById('backToTop');
    if (window.pageYOffset > 500) {
      backToTop.classList.add('visible');
    } else {
      backToTop.classList.remove('visible');
    }
  });

  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      document.querySelector(targetId).scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    });
  });

  document.getElementById('backToTop').addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // ===== VALIDACIÓN DEL FORMULARIO DE CONTACTO =====
  const form = document.getElementById('contactForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      let isValid = true;
      const name = document.getElementById('name');
      const email = document.getElementById('email');
      const message = document.getElementById('message');
      const nameError = name.nextElementSibling;
      const emailError = email.nextElementSibling;
      const messageError = message.nextElementSibling;

      [nameError, emailError, messageError].forEach(err => err.style.display = 'none');
      name.style.borderColor = 'var(--glass-border)';
      email.style.borderColor = 'var(--glass-border)';
      message.style.borderColor = 'var(--glass-border)';

      if (name.value.trim() === '') {
        nameError.textContent = 'El nombre es obligatorio';
        nameError.style.display = 'block';
        name.style.borderColor = '#ff4444';
        isValid = false;
      }
      if (email.value.trim() === '') {
        emailError.textContent = 'El email es obligatorio';
        emailError.style.display = 'block';
        email.style.borderColor = '#ff4444';
        isValid = false;
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        emailError.textContent = 'Email no válido';
        emailError.style.display = 'block';
        email.style.borderColor = '#ff4444';
        isValid = false;
      }
      if (message.value.trim() === '') {
        messageError.textContent = 'El mensaje es obligatorio';
        messageError.style.display = 'block';
        message.style.borderColor = '#ff4444';
        isValid = false;
      }

      if (isValid) {
        document.getElementById('formSuccess').style.display = 'block';
        form.reset();
        setTimeout(() => {
          document.getElementById('formSuccess').style.display = 'none';
        }, 3000);
      }
    });
  }
});
