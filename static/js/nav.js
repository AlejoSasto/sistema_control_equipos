(function () {
  var sidebar = document.getElementById('app-sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  var toggle = document.getElementById('nav-toggle');
  if (!sidebar || !overlay || !toggle) return;

  function openNav() {
    sidebar.classList.add('is-open');
    overlay.classList.add('is-visible');
    document.body.classList.add('nav-open');
    toggle.setAttribute('aria-expanded', 'true');
  }

  function closeNav() {
    sidebar.classList.remove('is-open');
    overlay.classList.remove('is-visible');
    document.body.classList.remove('nav-open');
    toggle.setAttribute('aria-expanded', 'false');
  }

  function toggleNav() {
    if (sidebar.classList.contains('is-open')) {
      closeNav();
    } else {
      openNav();
    }
  }

  toggle.addEventListener('click', toggleNav);
  overlay.addEventListener('click', closeNav);

  sidebar.querySelectorAll('.nav-link').forEach(function (link) {
    link.addEventListener('click', closeNav);
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeNav();
  });

  window.addEventListener('resize', function () {
    if (window.innerWidth >= 1024) closeNav();
  });
})();
