/**
 * Navegación móvil: offcanvas Bootstrap + cierre al elegir opción.
 */
(function () {
  var sidebar = document.getElementById("app-sidebar");
  if (!sidebar || typeof bootstrap === "undefined") return;

  function closeSidebar() {
    var instance = bootstrap.Offcanvas.getInstance(sidebar);
    if (instance) instance.hide();
  }

  sidebar.querySelectorAll(".nav-link").forEach(function (link) {
    link.addEventListener("click", function () {
      if (window.matchMedia("(max-width: 991.98px)").matches) {
        closeSidebar();
      }
    });
  });
})();
