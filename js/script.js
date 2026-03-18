// Preloader
window.addEventListener('load', () => {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        preloader.classList.add('hidden');
        setTimeout(() => {
            preloader.style.display = 'none';
        }, 500);
    }
});

// Fondo de partículas (canvas)
const canvas = document.getElementById('particles-canvas');
const ctx = canvas.getContext('2d');
let particles = [];

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();

class Particle {
    constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 2 + 1;
        this.speedX = Math.random() * 1 - 0.5;
        this.speedY = Math.random() * 1 - 0.5;
        this.color = `rgba(0, 170, 255, ${Math.random() * 0.3})`;
    }
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        if (this.x > canvas.width) this.x = 0;
        if (this.x < 0) this.x = canvas.width;
        if (this.y > canvas.height) this.y = 0;
        if (this.y < 0) this.y = canvas.height;
    }
    draw() {
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

function initParticles() {
    particles = [];
    for (let i = 0; i < 100; i++) {
        particles.push(new Particle());
    }
}
initParticles();

function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
        p.update();
        p.draw();
    });
    requestAnimationFrame(animateParticles);
}
animateParticles();

window.addEventListener('resize', () => {
    resizeCanvas();
    initParticles();
});

// Typing effect
const typingElement = document.getElementById('typing');
const phrases = ['Desarrollador Web & Software', 'Creador de soluciones digitales', 'Experto en seguridad TI'];
let phraseIndex = 0;
let charIndex = 0;
let isDeleting = false;

function typeEffect() {
    const currentPhrase = phrases[phraseIndex];
    if (isDeleting) {
        typingElement.textContent = currentPhrase.substring(0, charIndex - 1);
        charIndex--;
    } else {
        typingElement.textContent = currentPhrase.substring(0, charIndex + 1);
        charIndex++;
    }

    if (!isDeleting && charIndex === currentPhrase.length) {
        isDeleting = true;
        setTimeout(typeEffect, 2000);
    } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        phraseIndex = (phraseIndex + 1) % phrases.length;
        setTimeout(typeEffect, 500);
    } else {
        setTimeout(typeEffect, isDeleting ? 50 : 100);
    }
}
typeEffect();

// GSAP Animations
gsap.registerPlugin(ScrollTrigger);

// Hero entrance
gsap.from('.hero-text', {
    duration: 1.5,
    y: 100,
    opacity: 0,
    ease: 'power3.out'
});
gsap.from('.hero-image', {
    duration: 1.5,
    scale: 0.8,
    opacity: 0,
    ease: 'back.out(1.7)',
    delay: 0.3
});

// About section
gsap.from('.about-content', {
    scrollTrigger: {
        trigger: '.about',
        start: 'top 80%',
        toggleActions: 'play none none reverse'
    },
    y: 50,
    opacity: 0,
    duration: 1,
    ease: 'power2.out'
});

// Skills - stagger
gsap.from('.skill-item', {
    scrollTrigger: {
        trigger: '.skills',
        start: 'top 80%'
    },
    y: 50,
    opacity: 0,
    duration: 0.8,
    stagger: 0.1,
    ease: 'back.out(1.2)'
});

// Skills progress bars animation
gsap.utils.toArray('.skill-progress').forEach(bar => {
    const width = bar.style.width; // guardamos el ancho objetivo
    bar.style.width = '0%'; // reset para animar
    gsap.to(bar, {
        scrollTrigger: {
            trigger: bar,
            start: 'top 90%',
            toggleActions: 'play none none reverse'
        },
        width: width,
        duration: 1.5,
        ease: 'power2.inOut'
    });
});

// Projects stagger
gsap.from('.project-card', {
    scrollTrigger: {
        trigger: '.projects',
        start: 'top 80%'
    },
    y: 60,
    opacity: 0,
    duration: 1,
    stagger: 0.2,
    ease: 'power3.out'
});

// Timeline items
gsap.from('.timeline-item', {
    scrollTrigger: {
        trigger: '.experience',
        start: 'top 80%'
    },
    x: -50,
    opacity: 0,
    duration: 1,
    stagger: 0.3,
    ease: 'power2.out'
});

// Contact form
gsap.from('.contact-content', {
    scrollTrigger: {
        trigger: '.contact',
        start: 'top 80%'
    },
    scale: 0.95,
    opacity: 0,
    duration: 1,
    ease: 'power2.out'
});

// Counters animation
const counters = document.querySelectorAll('.stat-number');
counters.forEach(counter => {
    const updateCount = () => {
        const target = +counter.getAttribute('data-count');
        const count = +counter.innerText;
        const increment = target / 50;
        if (count < target) {
            counter.innerText = Math.ceil(count + increment);
            setTimeout(updateCount, 20);
        } else {
            counter.innerText = target;
        }
    };
    ScrollTrigger.create({
        trigger: counter,
        start: 'top 90%',
        onEnter: updateCount
    });
});

// Smooth scroll for internal links (opcional)
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            gsap.to(window, { duration: 1, scrollTo: { y: target, offsetY: 50 }, ease: 'power2.inOut' });
        }
    });
});