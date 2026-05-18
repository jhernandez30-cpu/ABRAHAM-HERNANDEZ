(() => {
  const header = document.querySelector('[data-header]');
  const nav = document.querySelector('[data-nav]');
  const navToggle = document.querySelector('[data-nav-toggle]');
  const year = document.getElementById('currentYear');
  const heroBg = document.querySelector('.hero-bg img');
  const revealItems = document.querySelectorAll('.reveal');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (year) {
    year.textContent = String(new Date().getFullYear());
  }

  function setScrolledState() {
    if (!header) return;
    header.classList.toggle('is-scrolled', window.scrollY > 12);
  }

  function closeNav() {
    if (!nav || !navToggle) return;
    nav.classList.remove('is-open');
    navToggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('nav-open');
  }

  navToggle?.addEventListener('click', () => {
    if (!nav) return;
    const isOpen = nav.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
    document.body.classList.toggle('nav-open', isOpen);
  });

  nav?.addEventListener('click', event => {
    if (event.target.closest('a')) closeNav();
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeNav();
  });

  if ('IntersectionObserver' in window && revealItems.length) {
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.14, rootMargin: '0px 0px -40px 0px' }
    );
    revealItems.forEach(item => observer.observe(item));
  } else {
    revealItems.forEach(item => item.classList.add('is-visible'));
  }

  function updateHeroParallax() {
    if (!heroBg || prefersReducedMotion) return;
    const offset = Math.min(window.scrollY * 0.08, 42);
    heroBg.style.transform = `translateY(${offset}px) scale(1.04)`;
  }

  let ticking = false;
  window.addEventListener(
    'scroll',
    () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        setScrolledState();
        updateHeroParallax();
        ticking = false;
      });
    },
    { passive: true }
  );

  setScrolledState();
  updateHeroParallax();
})();
