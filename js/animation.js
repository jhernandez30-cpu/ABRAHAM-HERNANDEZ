// === animation.js (Anime.js + GSAP + contadores) ===
document.addEventListener('DOMContentLoaded', () => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const animeApi = window.anime || {};
  const animeAnimate = typeof animeApi.animate === 'function' ? animeApi.animate : null;
  const animeStagger = typeof animeApi.stagger === 'function' ? animeApi.stagger : null;

  if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
    gsap.registerPlugin(ScrollTrigger);
  }

  initMasterclassIntegration(reduceMotion);

  if (!reduceMotion) {
    const heroRan = runAnimeHero(animeAnimate, animeStagger);
    const pageIntroRan = runAnimePageIntro(animeAnimate, animeStagger);
    if (!heroRan && !pageIntroRan) {
      runGsapHeroFallback();
    }
    runGsapScrollReveals();
    initPortraitParallax();
    initAnimeMicroInteractions(animeAnimate);
  }

  animateSkillBars(reduceMotion);
  animateCounters(reduceMotion);
});

function initMasterclassIntegration(reduceMotion) {
  if (shouldSkipMasterclassIntegration()) return;

  document.body.classList.add('masterclass-integrated');
  initMasterclassNavState();
  initMasterclassHeroArchitecture();
  initMasterclassMarquee();
  initMasterclassReveals(reduceMotion);
  initMasterclassCardSpotlight(reduceMotion);
}

function shouldSkipMasterclassIntegration() {
  const path = window.location.pathname.toLowerCase();
  return (
    path.includes('/jah/') ||
    path.endsWith('/jah') ||
    document.body.classList.contains('programming-app-page')
  );
}

function initMasterclassNavState() {
  const nav = document.getElementById('navbar');
  const headerWrap = document.querySelector('#header .header-wrap');
  const targets = [nav, headerWrap].filter(Boolean);
  if (!targets.length) return;

  function updateNavState() {
    const solid = window.scrollY > 80;
    document.body.classList.toggle('premium-nav-solid', solid);
    targets.forEach((target) => target.classList.toggle('solid', solid));
  }

  updateNavState();
  window.addEventListener('scroll', updateNavState, { passive: true });
}

function initMasterclassHeroArchitecture() {
  const hero = findMasterclassHero();
  if (!hero || hero.querySelector('.masterclass-hero-mosaic')) return;

  hero.classList.add('masterclass-hero-host');
  if (getComputedStyle(hero).position === 'static') {
    hero.style.position = 'relative';
  }

  const mosaic = document.createElement('div');
  mosaic.className = 'masterclass-hero-mosaic';
  mosaic.setAttribute('aria-hidden', 'true');

  for (let col = 0; col < 5; col += 1) {
    const column = document.createElement('div');
    column.className = 'masterclass-mosaic-col';
    for (let cell = 0; cell < 2; cell += 1) {
      const tile = document.createElement('div');
      tile.className = 'masterclass-mosaic-cell';
      column.appendChild(tile);
    }
    mosaic.appendChild(column);
  }

  hero.prepend(mosaic);

  if (!hero.querySelector('.portfolio-scroll-indicator')) {
    const scrollIndicator = document.createElement('div');
    scrollIndicator.className = 'portfolio-scroll-indicator';
    scrollIndicator.setAttribute('aria-hidden', 'true');
    scrollIndicator.append(document.createTextNode('Scroll'));
    hero.appendChild(scrollIndicator);
  }
}

function findMasterclassHero() {
  return (
    document.querySelector('#billboard') ||
    document.querySelector('.titles-hero') ||
    document.querySelector('.page-hero') ||
    document.querySelector('#contact-page') ||
    document.querySelector('main > .section:first-of-type') ||
    document.querySelector('main > section:first-of-type')
  );
}

function initMasterclassMarquee() {
  if (document.querySelector('.portfolio-marquee-bar')) return;

  const hero = findMasterclassHero();
  if (!hero || !hero.parentNode) return;

  const items = [
    'Desarrollo web',
    'Automatización',
    'Dashboards',
    'APIs',
    'Ciberseguridad',
    'Inteligencia artificial',
    'Soluciones digitales',
    'Tecnología empresarial'
  ];

  const marquee = document.createElement('div');
  marquee.className = 'portfolio-marquee-bar';
  marquee.setAttribute('aria-label', 'Áreas profesionales destacadas');

  const track = document.createElement('div');
  track.className = 'portfolio-marquee-track';

  [...items, ...items].forEach((item) => {
    const label = document.createElement('span');
    label.className = 'portfolio-marquee-item';
    label.append(document.createTextNode(item));

    const dot = document.createElement('span');
    dot.className = 'portfolio-marquee-dot';
    dot.setAttribute('aria-hidden', 'true');
    dot.textContent = '◆';
    label.appendChild(dot);

    track.appendChild(label);
  });

  marquee.appendChild(track);
  hero.insertAdjacentElement('afterend', marquee);
}

function initMasterclassReveals(reduceMotion) {
  const selectors = [
    '#billboard .banner-content > *',
    '#billboard .socila-links a',
    '.page-hero .container > *',
    '.titles-hero .container > *',
    '#contact-page .container > *',
    '.section-header',
    '.section-heading',
    '.section-title',
    '.section-description',
    '.section-subtitle',
    '.section-lede',
    '.hero-lede',
    '.hero-actions',
    '.hero-panel',
    '.home-copy-section .container > *',
    '.site-link-card',
    '#services .column',
    '.value-card',
    '.cta-band',
    '.tab-content .tab-element',
    '.technology-item',
    '#about-profile .review-item',
    '.seo-card',
    '.service-card',
    '.case-card',
    '.metric-card',
    '.step-card',
    '.faq-card',
    '.card',
    '.skill-card',
    '.cert-item',
    '.credential-card',
    '.formation-card',
    '.experience-item',
    '.indicator-card',
    '.info-card',
    '.form-card',
    '.contact-item',
    '.contact-option',
    '.contact-followup-card',
    '.social-btn',
    'footer .footer-logo',
    'footer .site-footer-links',
    'footer p'
  ];

  const elements = collectUniqueElements(selectors).filter((element) => {
    return (
      element instanceof HTMLElement &&
      !element.closest('.chatbot-widget') &&
      !element.closest('script, style, noscript')
    );
  });

  elements.forEach((element, index) => {
    element.classList.add('reveal');
    element.dataset.masterclassReveal = 'true';

    if (!/(^|\s)reveal-d[1-4](\s|$)/.test(element.className)) {
      const delay = index % 5;
      if (delay) element.classList.add(`reveal-d${delay}`);
    }
  });

  document.querySelectorAll('main section, .page-section, .content-section, #contact-page, #achievement').forEach((section) => {
    if (section instanceof HTMLElement && !section.closest('.chatbot-widget')) {
      section.classList.add('premium-section-shell');
    }
  });

  if (reduceMotion || typeof IntersectionObserver === 'undefined') {
    elements.forEach((element) => element.classList.add('in-view'));
    return;
  }

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in-view');
      revealObserver.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' });

  elements.forEach((element) => revealObserver.observe(element));
}

function initMasterclassCardSpotlight(reduceMotion) {
  if (reduceMotion || !window.matchMedia('(pointer: fine)').matches) return;

  const selectors = [
    '.site-link-card',
    '#services .column',
    '.tab-content .tab-element figure',
    '.seo-card',
    '.service-card',
    '.case-card',
    '.metric-card',
    '.step-card',
    '.faq-card',
    '.card',
    '.skill-card',
    '.cert-item',
    '.credential-card',
    '.formation-card',
    '.experience-item',
    '.indicator-card',
    '.info-card',
    '.form-card',
    '.contact-option',
    '.contact-followup-card'
  ];

  collectUniqueElements(selectors).forEach((card) => {
    if (!(card instanceof HTMLElement) || card.closest('.chatbot-widget')) return;
    card.classList.add('premium-interactive');

    card.addEventListener('pointermove', (event) => {
      const rect = card.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 100;
      const y = ((event.clientY - rect.top) / rect.height) * 100;
      card.style.setProperty('--spotlight-x', `${x.toFixed(2)}%`);
      card.style.setProperty('--spotlight-y', `${y.toFixed(2)}%`);
    });
  });
}

function runAnimeHero(animate, stagger) {
  if (!animate) return false;

  let hadTargets = false;
  const textTargets = '.hero-title, .dynamic-text, .hero-copy, .hero-social-link';
  if (document.querySelector(textTargets)) {
    hadTargets = true;
    animate(textTargets, {
      opacity: [0, 1],
      y: [32, 0],
      duration: 900,
      delay: stagger ? stagger(85) : 0,
      ease: 'outExpo'
    });
  }

  if (document.querySelector('.hero-portrait')) {
    hadTargets = true;
    animate('.hero-portrait', {
      opacity: [0, 1],
      duration: 900,
      delay: stagger ? stagger(140, { start: 260 }) : 260,
      ease: 'outExpo'
    });

    animate('.hero-portrait-inner', {
      y: [72, 0],
      scale: [1.08, 1],
      duration: 1300,
      delay: stagger ? stagger(140, { start: 260 }) : 260,
      ease: 'outElastic(1, .72)'
    });
  }

  if (document.querySelector('.portrait-scanline')) {
    hadTargets = true;
    animate('.portrait-scanline', {
      x: ['-130%', '240%'],
      opacity: [0, 0.5, 0],
      duration: 2800,
      delay: 1200,
      loop: true,
      loopDelay: 1800,
      ease: 'inOutQuad'
    });
  }

  return hadTargets;
}

function runAnimePageIntro(animate, stagger) {
  if (!animate) return false;

  const targets = collectUniqueElements([
    '.section:first-of-type h2',
    '.section:first-of-type .section-description',
    '.section:first-of-type .card',
    '.content-section > h2',
    '.content-section > .skills-grid:first-of-type .skill-card',
    '#contact-page .section-title',
    '#contact-page .section-subtitle',
    '#contact-page .form-card',
    '#contact-page .info-card'
  ]).filter((element) => !element.dataset.masterclassReveal);

  if (!targets.length) return false;

  targets.forEach((element) => {
    element.dataset.animeIntro = 'true';
  });

  animate(targets, {
    opacity: [0, 1],
    y: [36, 0],
    scale: [0.98, 1],
    duration: 880,
    delay: stagger ? stagger(90, { start: 120 }) : 120,
    ease: 'outExpo'
  });

  return true;
}

function runGsapHeroFallback() {
  if (typeof gsap === 'undefined') return;

  gsap.from('.hero-title, .dynamic-text, .hero-copy, .hero-social-link', {
    y: 32,
    opacity: 0,
    duration: 0.9,
    stagger: 0.08,
    ease: 'power3.out'
  });

  gsap.from('.hero-portrait', {
    opacity: 0,
    y: 72,
    scale: 0.94,
    duration: 1.2,
    stagger: 0.12,
    delay: 0.25,
    ease: 'elastic.out(1, 0.72)'
  });
}

function runGsapScrollReveals() {
  if (typeof gsap === 'undefined') return;

  const selectors = [
    'section:not(#hero) h2',
    '.section-description',
    '.section-subtitle',
    '.stat-item',
    '.skill-card',
    '.cert-item',
    '.card',
    '.seo-card',
    '.service-card',
    '.case-card',
    '.step-card',
    '.faq-card',
    '.conversion-card',
    '.project-card',
    '.assistant-copy > *',
    '.assistant-preview',
    '.form-card',
    '.info-card',
    '.contact-item',
    '.social-btn',
    '.availability-note',
    '.cita-biblica',
    'footer'
  ];

  const revealed = new Set();
  selectors.forEach((selector) => {
    gsap.utils.toArray(selector).forEach((element) => {
      if (revealed.has(element) || element.dataset.animeIntro === 'true' || element.dataset.masterclassReveal === 'true') return;
      revealed.add(element);

      const animation = {
        y: 44,
        opacity: 0,
        duration: 0.85,
        ease: 'power3.out'
      };

      if (typeof ScrollTrigger !== 'undefined') {
        animation.scrollTrigger = {
          trigger: element,
          start: 'top 88%',
          once: true,
          toggleActions: 'play none none none'
        };
      }

      gsap.from(element, animation);
    });
  });
}

function initAnimeMicroInteractions(animate) {
  if (!animate) return;

  const icons = document.querySelectorAll(
    '.card-icon, .skill-icon, .cert-icon, .contact-item i, .social-btn i, .seo-card i, .service-card i, .case-card i, .conversion-card i'
  );

  icons.forEach((icon) => {
    const trigger = icon.closest('a, .card, .skill-card, .cert-item, .contact-item, .social-btn, .seo-card, .service-card, .case-card, .conversion-card');
    if (!trigger) return;

    trigger.addEventListener('mouseenter', () => {
      animate(icon, {
        scale: [1, 1.18, 1],
        rotate: [0, -5, 5, 0],
        duration: 520,
        ease: 'outBack'
      });
    });
  });
}

function collectUniqueElements(selectors) {
  const seen = new Set();
  const elements = [];

  selectors.forEach((selector) => {
    document.querySelectorAll(selector).forEach((element) => {
      if (seen.has(element)) return;
      seen.add(element);
      elements.push(element);
    });
  });

  return elements;
}

function initPortraitParallax() {
  if (typeof gsap === 'undefined') return;
  if (!window.matchMedia('(pointer: fine)').matches) return;

  const stage = document.querySelector('.portrait-stage');
  const portraits = document.querySelectorAll('.hero-portrait');
  if (!stage || !portraits.length) return;

  stage.addEventListener('pointermove', (event) => {
    const rect = stage.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;

    portraits.forEach((portrait) => {
      const depth = Number(portrait.dataset.depth || 0.08);
      gsap.to(portrait, {
        x: x * depth * 90,
        y: y * depth * 70,
        rotateX: y * -5,
        rotateY: x * 6,
        duration: 0.7,
        ease: 'power3.out'
      });
    });
  });

  stage.addEventListener('pointerleave', () => {
    portraits.forEach((portrait) => {
      gsap.to(portrait, {
        x: 0,
        y: 0,
        rotateX: 0,
        rotateY: 0,
        duration: 0.8,
        ease: 'power3.out'
      });
    });
  });
}

function animateSkillBars(reduceMotion) {
  const bars = document.querySelectorAll('.skill-progress');
  if (!bars.length) return;

  bars.forEach((bar) => {
    const width = `${bar.dataset.width || 0}%`;

    if (reduceMotion || typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
      bar.style.width = width;
      return;
    }

    gsap.to(bar, {
      scrollTrigger: {
        trigger: bar,
        start: 'top 90%'
      },
      width,
      duration: 1.25,
      ease: 'power2.out'
    });
  });
}

function animateCounters(reduceMotion) {
  const counters = document.querySelectorAll('.stat-number');
  if (!counters.length) return;

  if (reduceMotion || typeof IntersectionObserver === 'undefined') {
    counters.forEach((counter) => {
      counter.innerText = counter.getAttribute('data-target') || '0';
    });
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;

      const el = entry.target;
      const target = parseInt(el.getAttribute('data-target') || '0', 10);
      const duration = 1100;
      const start = performance.now();

      function updateCounter(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.innerText = Math.round(target * eased);

        if (progress < 1) {
          requestAnimationFrame(updateCounter);
        } else {
          el.innerText = target;
        }
      }

      requestAnimationFrame(updateCounter);
      observer.unobserve(el);
    });
  }, { threshold: 0.45 });

  counters.forEach((counter) => observer.observe(counter));
}
