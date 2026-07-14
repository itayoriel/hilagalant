document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.fade-in-load').forEach((el, i) => {
    setTimeout(() => el.classList.add('visible'), 150 + i * 120);
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.gallery .fade-in, .stills .fade-in, .about.fade-in').forEach((el) => observer.observe(el));

  document.querySelectorAll('.video-facade').forEach((el) => {
    el.addEventListener('click', () => {
      if (!el.classList.contains('video-facade')) return;
      const src = el.dataset.src;
      const video = document.createElement('video');
      video.controls = true;
      video.setAttribute('playsinline', '');
      video.setAttribute('webkit-playsinline', '');
      const source = document.createElement('source');
      source.src = src;
      source.type = 'video/mp4';
      video.appendChild(source);
      el.innerHTML = '';
      el.appendChild(video);
      el.classList.remove('video-facade');
      video.play().catch(() => {});
    }, { once: true });
  });

  const navLinks = document.querySelectorAll('.site-nav nav a[href^="#"]');
  if (navLinks.length) {
    const sections = Array.from(navLinks)
      .map((link) => document.querySelector(link.getAttribute('href')))
      .filter(Boolean);

    const updateActiveNav = () => {
      const line = window.innerHeight * 0.45;
      let current = null;
      sections.forEach((section) => {
        if (section.getBoundingClientRect().top <= line) current = section;
      });
      navLinks.forEach((link) => {
        link.classList.toggle('active', !!current && link.getAttribute('href') === `#${current.id}`);
      });
    };

    window.addEventListener('scroll', updateActiveNav, { passive: true });
    updateActiveNav();
  }

  const portraitItems = document.querySelectorAll('.gallery-item.portrait');
  const pauseOffscreenShorts = () => {
    portraitItems.forEach((el) => {
      const vid = el.querySelector('video');
      if (!vid || vid.paused) return;
      const rect = el.getBoundingClientRect();
      const fullyOffscreen = rect.bottom <= 0 || rect.top >= window.innerHeight;
      if (fullyOffscreen) vid.pause();
    });
  };
  window.addEventListener('scroll', pauseOffscreenShorts, { passive: true });

  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightbox-img');
  if (lightbox && lightboxImg) {
    document.querySelectorAll('.still').forEach((img) => {
      img.addEventListener('click', () => {
        lightboxImg.src = img.src;
        lightbox.classList.add('open');
      });
    });

    const closeLightbox = () => {
      lightbox.classList.remove('open');
      lightboxImg.src = '';
    };

    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox || e.target.closest('.lightbox-close')) closeLightbox();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeLightbox();
    });
  }
});
