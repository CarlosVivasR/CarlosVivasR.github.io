// ─── Highlight active nav link on scroll ───────────────────────
const sections = document.querySelectorAll('section[id], header[id]');
const navLinks = document.querySelectorAll('nav ul a');

const navObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(link => {
        link.classList.toggle(
          'active',
          link.getAttribute('href') === `#${entry.target.id}`
        );
      });
    }
  });
}, { rootMargin: '-40% 0px -55% 0px' });

sections.forEach(s => navObserver.observe(s));

// ─── Mobile hamburger menu ─────────────────────────────────────
const toggle = document.querySelector('.nav-toggle');
const navUl = document.querySelector('nav ul');

if (toggle) {
  toggle.addEventListener('click', () => {
    navUl.classList.toggle('open');
  });

  // Close menu when a link is clicked
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      navUl.classList.remove('open');
    });
  });
}

// Animations handled via CSS @keyframes — no JS needed
