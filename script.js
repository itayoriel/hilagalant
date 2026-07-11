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

  document.querySelectorAll('.yt-facade').forEach((el) => {
    el.addEventListener('click', () => {
      const id = el.dataset.id;
      const iframe = document.createElement('iframe');
      iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&modestbranding=1&iv_load_policy=3&playsinline=1`;
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
      iframe.allowFullscreen = true;
      el.innerHTML = '';
      el.appendChild(iframe);
      el.classList.remove('yt-facade');
    });
  });
});
