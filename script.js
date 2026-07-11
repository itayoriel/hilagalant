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

  document.querySelectorAll('.gallery .fade-in').forEach((el) => observer.observe(el));

  document.querySelectorAll('.video-facade').forEach((el) => {
    el.addEventListener('click', () => {
      const src = el.dataset.src;
      const video = document.createElement('video');
      video.src = src;
      video.controls = true;
      video.autoplay = true;
      video.playsInline = true;
      el.innerHTML = '';
      el.appendChild(video);
      el.classList.remove('video-facade');
    });
  });
});
