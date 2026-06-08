(() => {
  const body = document.body;
  if (!body || !body.classList.contains("eventually-redesign")) return;

  window.addEventListener("load", () => {
    window.setTimeout(() => {
      body.classList.remove("is-preload");
    }, 100);
  });

  const targets = document.querySelectorAll(
    ".page-hero, .page-section, .case-card, .hero-panel, .cta-band, .info-card, .contact-form-container, #text-container > *"
  );

  targets.forEach((element) => element.classList.add("eventually-reveal"));

  if (!("IntersectionObserver" in window)) {
    targets.forEach((element) => element.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
  );

  targets.forEach((element) => observer.observe(element));
})();
