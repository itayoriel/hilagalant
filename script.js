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
      const src = el.dataset.src;
      const video = document.createElement('video');
      video.controls = true;
      video.loop = true;
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
    });
  });

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
