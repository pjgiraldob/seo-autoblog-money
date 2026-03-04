(function () {
  const revealElements = () => {
    const nodes = document.querySelectorAll('.reveal');
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    nodes.forEach((node) => observer.observe(node));
  };

  const readingProgress = () => {
    const bar = document.querySelector('.reading-progress__bar');
    if (!bar) return;

    const update = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) : 0;
      bar.style.width = progress + '%';
    };

    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
  };

  const styleArticlePage = () => {
    if (window.location.pathname.includes('/posts/')) {
      document.body.classList.add('page-post');
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    revealElements();
    readingProgress();
    styleArticlePage();
  });
})();
