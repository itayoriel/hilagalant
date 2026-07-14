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

    const setActive = (id) => {
      navLinks.forEach((link) => {
        link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
      });
    };

    const spyObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) setActive(entry.target.id);
      });
    }, { rootMargin: '0px 0px -70% 0px', threshold: 0 });

    sections.forEach((section) => spyObserver.observe(section));
  }

  const siteNav = document.querySelector('.site-nav');
  const hero = document.querySelector('.hero');
  if (siteNav && hero) {
    const navScrollObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        siteNav.classList.toggle('solid', !entry.isIntersecting);
      });
    }, { rootMargin: `-${siteNav.offsetHeight}px 0px 0px 0px`, threshold: 0 });
    navScrollObserver.observe(hero);
  }

  const portraitVideoObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) {
        const vid = entry.target.querySelector('video');
        if (vid && !vid.paused) vid.pause();
      }
    });
  }, { threshold: 0 });

  document.querySelectorAll('.gallery-item.portrait').forEach((el) => portraitVideoObserver.observe(el));

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
