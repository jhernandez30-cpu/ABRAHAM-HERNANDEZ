// === animation.js (GSAP) ===
document.addEventListener('DOMContentLoaded', () => {
  // Hero título animado
  gsap.from('.hero-title', {
    duration: 1.5,
    y: 100,
    opacity: 0,
    ease: 'power4.out'
  });

  gsap.from('.dynamic-text', {
    duration: 1.5,
    y: 50,
    opacity: 0,
    delay: 0.3,
    ease: 'power4.out'
  });

  gsap.from('.profile-img', {
    duration: 1.5,
    scale: 0.5,
    opacity: 0,
    delay: 0.6,
    ease: 'elastic.out(1, 0.5)'
  });

  gsap.from('.hero-buttons a', {
    duration: 1,
    y: 30,
    opacity: 0,
    stagger: 0.2,
    delay: 1,
    ease: 'power3.out'
  });

  // ScrollTrigger para títulos de secciones (excepto hero)
  gsap.utils.toArray('section:not(#hero)').forEach(section => {
    gsap.from(section.querySelector('h2'), {
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
  });

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

  // Animación de contadores en estadísticas
  const stats = document.querySelectorAll('.stat-number');
  stats.forEach(stat => {
    const target = parseInt(stat.getAttribute('data-target'));
    gsap.to(stat, {
      scrollTrigger: {
        trigger: stat,
        start: 'top 80%',
      },
      duration: 2,
      innerText: target,
      snap: { innerText: 1 },
      ease: 'power2.out'
    });
  });

  // Animación de entrada para tarjetas de servicios
  gsap.from('.glass-card', {
    scrollTrigger: {
      trigger: '#experience',
      start: 'top 80%',
    },
    y: 50,
    opacity: 0,
    duration: 0.8,
    stagger: 0.2,
    ease: 'back.out(1.2)'
  });
});
