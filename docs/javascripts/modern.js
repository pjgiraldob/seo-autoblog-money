(function () {
  const qs = (s, p = document) => p.querySelector(s);

  function revealOnScroll() {
    const nodes = document.querySelectorAll('.reveal');
    if (!nodes.length) return;

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    nodes.forEach((n) => io.observe(n));
  }

  function readingProgress() {
    const bar = qs('.reading-progress__bar');
    if (!bar) return;

    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const val = max > 0 ? Math.min((window.scrollY / max) * 100, 100) : 0;
      bar.style.width = val + '%';
    };

    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
  }

  function enhanceArticlePage() {
    if (!window.location.pathname.includes('/posts/')) return;

    const content = qs('.md-content__inner');
    if (!content) return;
    if (qs('.share-row', content)) return;

    const share = document.createElement('div');
    share.className = 'share-row reveal';

    const title = document.title;
    const url = window.location.href;

    share.innerHTML = [
      '<strong>Share:</strong>',
      `<a href="https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}" target="_blank" rel="noopener">X</a>`,
      `<a href="https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}" target="_blank" rel="noopener">LinkedIn</a>`,
      `<a href="https://www.reddit.com/submit?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}" target="_blank" rel="noopener">Reddit</a>`
    ].join('');

    content.appendChild(share);
  }

  function newsletterFormRouting() {
    const form = qs('.newsletter-form');
    if (!form) return;

    form.addEventListener('submit', function () {
      const input = qs('input[type="email"]', form);
      if (!input || !input.value) return;
    });
  }

  function languageSwitcher() {
    const links = document.querySelectorAll('[data-lang-switch]');
    if (!links.length) return;

    const currentUrl = window.location.href;
    links.forEach((link) => {
      const lang = (link.getAttribute('data-lang-switch') || 'es').toLowerCase();
      if (lang === 'es') {
        link.setAttribute('href', currentUrl);
        link.removeAttribute('target');
        link.removeAttribute('rel');
        return;
      }
      const translated = `https://translate.google.com/translate?sl=es&tl=${encodeURIComponent(lang)}&u=${encodeURIComponent(currentUrl)}`;
      link.setAttribute('href', translated);
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
    });
  }

  function init() {
    revealOnScroll();
    readingProgress();
    enhanceArticlePage();
    newsletterFormRouting();
    languageSwitcher();
  }

  document.addEventListener('DOMContentLoaded', init);
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(init);
  }
})();
