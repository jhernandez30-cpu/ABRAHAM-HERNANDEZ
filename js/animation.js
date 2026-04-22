// === animation.js (GSAP + Intersection Observer para contadores) ===
document.addEventListener('DOMContentLoaded', () => {
  // Verificar si GSAP está disponible antes de usarlo
  if (typeof gsap !== 'undefined') {
    // Hero título animado (solo si existen los elementos)
    if (document.querySelector('.hero-title')) {
      gsap.from('.hero-title', {
        duration: 1.5,
        y: 100,
        opacity: 0,
        ease: 'power4.out'
      });
    }

    if (document.querySelector('.dynamic-text')) {
      gsap.from('.dynamic-text', {
        duration: 1.5,
        y: 50,
        opacity: 0,
        delay: 0.3,
        ease: 'power4.out'
      });
    }

    if (document.querySelector('.profile-img')) {
      gsap.from('.profile-img', {
        duration: 1.5,
        scale: 0.5,
        opacity: 0,
        delay: 0.6,
        ease: 'elastic.out(1, 0.5)'
      });
    }

    // ScrollTrigger para títulos de secciones (solo si ScrollTrigger existe)
    if (typeof ScrollTrigger !== 'undefined') {
      gsap.utils.toArray('section:not(#hero)').forEach(section => {
        const h2 = section.querySelector('h2');
        if (h2) {
          gsap.from(h2, {
            scrollTrigger: {
              trigger: section,
              start: 'top 80%',
              toggleActions: 'play none none reverse'
            },
            y: 60,
            opacity: 0,
            duration: 1,
            ease: 'power3.out'
          });
        }
      });
    }

    // Animación de barras de progreso en habilidades
    gsap.utils.toArray('.skill-progress').forEach(bar => {
      const width = bar.dataset.width || '0';
      gsap.to(bar, {
        scrollTrigger: {
          trigger: bar,
          start: 'top 90%',
        },
        width: width + '%',
        duration: 1.5,
        ease: 'power2.out'
      });
    });
  }

  // ===== CONTADORES ANIMADOS (Intersection Observer) =====
  const counters = document.querySelectorAll('.stat-number');
  if (counters.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = parseInt(el.getAttribute('data-target'));
          let current = 0;
          const increment = target / 60;
          const updateCounter = () => {
            current += increment;
            if (current < target) {
              el.innerText = Math.ceil(current);
              requestAnimationFrame(updateCounter);
            } else {
              el.innerText = target;
              observer.unobserve(el);
            }
          };
          updateCounter();
          observer.unobserve(el);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(c => observer.observe(c));
  }
});
