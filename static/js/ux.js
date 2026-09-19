/**
 * UX escalable: debounce de filtros, toasts, modal de confirmación, anti doble-submit.
 */
(function () {
  function debounce(fn, wait) {
    var t;
    return function () {
      var ctx = this, args = arguments;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, wait);
    };
  }

  /* Debounce en inputs de búsqueda de formularios .js-filter-form */
  document.querySelectorAll("form.js-filter-form input[name='q']").forEach(function (input) {
    var form = input.form;
    if (!form) return;
    input.addEventListener("input", debounce(function () {
      var pageInput = form.querySelector("input[name='page']");
      if (pageInput) pageInput.value = "1";
      form.requestSubmit ? form.requestSubmit() : form.submit();
    }, 350));
  });

  /* Toast helper global */
  window.showAppToast = function (message, type) {
    var container = document.getElementById("toast-container");
    if (!container || typeof bootstrap === "undefined") return;
    type = type || "success";
    var el = document.createElement("div");
    el.className = "toast align-items-center text-bg-" + (type === "danger" ? "danger" : type === "warning" ? "warning" : "success") + " border-0";
    el.setAttribute("role", "alert");
    el.innerHTML = '<div class="d-flex"><div class="toast-body">' + message + '</div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    container.appendChild(el);
    var toast = new bootstrap.Toast(el, { delay: 2800 });
    toast.show();
    el.addEventListener("hidden.bs.toast", function () { el.remove(); });
  };

  /* Modal de confirmación genérico */
  var modalEl = document.getElementById("modalConfirmacion");
  var pendingForm = null;
  if (modalEl) {
    modalEl.addEventListener("show.bs.modal", function (event) {
      var btn = event.relatedTarget;
      if (!btn) return;
      document.getElementById("modalConfirmacionLabel").textContent =
        btn.getAttribute("data-confirm-title") || "Confirmar acción";
      document.getElementById("modalConfirmacionBody").textContent =
        btn.getAttribute("data-confirm-body") || "¿Desea continuar?";
      var formId = btn.getAttribute("data-confirm-form");
      pendingForm = formId ? document.getElementById(formId) : btn.closest("form");
    });
    document.getElementById("modalConfirmacionSubmit").addEventListener("click", function () {
      if (pendingForm) pendingForm.submit();
      var instance = bootstrap.Modal.getInstance(modalEl);
      if (instance) instance.hide();
    });
  }

  /* Deshabilitar botones submit al enviar (anti doble clic) */
  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.hasAttribute("data-allow-resubmit")) return;
    var btn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    if (btn.tagName === "BUTTON" && !btn.querySelector(".spinner-border")) {
      var spin = document.createElement("span");
      spin.className = "spinner-border spinner-border-sm me-2";
      spin.setAttribute("role", "status");
      spin.setAttribute("aria-hidden", "true");
      btn.prepend(spin);
    }
    /* Descargas: la página no navega; reactivar el botón tras el envío */
    if (form.hasAttribute("data-download")) {
      setTimeout(function () {
        btn.disabled = false;
        var spinEl = btn.querySelector(".spinner-border");
        if (spinEl) spinEl.remove();
      }, 2500);
    }
  });

  /* Mostrar / ocultar contraseña — un icono (mismo estilo Heroicons del menú) */
  var ICON_EYE_OFF =
    '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">' +
    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
    'd="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>' +
    "</svg>";
  var ICON_EYE =
    '<svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">' +
    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
    'd="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>' +
    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
    'd="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>' +
    "</svg>";

  document.querySelectorAll("[data-password-toggle]").forEach(function (btn) {
    var field = btn.closest(".password-field");
    var input = field ? field.querySelector("input.form-control") : null;
    if (!input) return;
    btn.addEventListener("click", function () {
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.setAttribute("aria-pressed", show ? "true" : "false");
      btn.setAttribute("aria-label", show ? "Ocultar contraseña" : "Mostrar contraseña");
      btn.innerHTML = show ? ICON_EYE : ICON_EYE_OFF;
    });
  });
})();
