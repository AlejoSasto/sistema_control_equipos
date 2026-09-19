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
  });
})();
