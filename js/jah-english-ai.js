const menuToggle = document.querySelector(".menu-toggle");
      const navLinks = document.querySelector(".nav-links");

      if (menuToggle && navLinks) {
        menuToggle.addEventListener("click", () => {
          const isOpen = navLinks.classList.toggle("open");
          document.body.classList.toggle("menu-open", isOpen);
          menuToggle.setAttribute("aria-expanded", String(isOpen));
        });

        navLinks.querySelectorAll("a").forEach((link) => {
          link.addEventListener("click", () => {
            navLinks.classList.remove("open");
            document.body.classList.remove("menu-open");
            menuToggle.setAttribute("aria-expanded", "false");
          });
        });
      }

      const revealItems = document.querySelectorAll(".reveal");
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("visible");
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12 }
      );

      revealItems.forEach((item) => observer.observe(item));
