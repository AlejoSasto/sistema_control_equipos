/**
 * Dashboard admin: Chart.js + refresco tras HTMX.
 * Los canvas viven dentro de .dashboard-chart-box (altura fija) para evitar
 * el bucle de crecimiento con maintainAspectRatio: false.
 */
(function () {
  "use strict";

  var charts = {
    linea: null,
    dona: null,
    sedes: null,
    top_alertas: null,
    motivos_alerta: null,
  };

  var COLOR_PRIMARY = "#007B3E";
  var COLOR_DANGER = "#C62828";
  var COLOR_MUTED = "#5B615D";

  var baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    layout: { padding: { top: 4, right: 8, bottom: 4, left: 4 } },
  };

  function axisTicks() {
    return { maxTicksLimit: 8, font: { size: 11 } };
  }

  function destroyAll() {
    Object.keys(charts).forEach(function (key) {
      if (charts[key]) {
        charts[key].destroy();
        charts[key] = null;
      }
    });
  }

  function setEmpty(name, isEmpty) {
    var emptyEl = document.querySelector('.js-chart-empty[data-chart="' + name + '"]');
    var canvasIds = {
      linea: "chart-linea",
      dona: "chart-dona",
      sedes: "chart-sedes",
      top_alertas: "chart-top-alertas",
      motivos_alerta: "chart-motivos-alerta",
    };
    var canvas = document.getElementById(canvasIds[name] || "");
    if (emptyEl) emptyEl.hidden = !isEmpty;
    if (canvas) canvas.style.display = isEmpty ? "none" : "block";
  }

  function buildQueryFromForm() {
    var form = document.getElementById("dashboard-filtros");
    if (!form) return "";
    var fd = new FormData(form);
    var params = new URLSearchParams();
    fd.forEach(function (value, key) {
      if (value !== null && value !== "") params.append(key, value);
    });
    return params.toString();
  }

  function datosUrl() {
    var container = document.getElementById("dashboard-contenido");
    var base =
      (container && container.dataset.datosUrl) ||
      "/panel/dashboard/datos-grafico/";
    var qs = buildQueryFromForm();
    return qs ? base + (base.indexOf("?") >= 0 ? "&" : "?") + qs : base;
  }

  function renderCharts(data) {
    if (typeof Chart === "undefined") return;
    destroyAll();

    setEmpty("linea", !!(data.linea && data.linea.vacio));
    setEmpty("dona", !!(data.dona && data.dona.vacio));
    setEmpty("sedes", !!(data.sedes && data.sedes.vacio));
    setEmpty("top_alertas", !!(data.top_alertas && data.top_alertas.vacio));
    setEmpty("motivos_alerta", !!(data.motivos_alerta && data.motivos_alerta.vacio));

    var elLinea = document.getElementById("chart-linea");
    if (elLinea && data.linea && !data.linea.vacio) {
      charts.linea = new Chart(elLinea, {
        type: "line",
        data: {
          labels: data.linea.labels,
          datasets: [
            {
              label: "Movimientos",
              data: data.linea.values,
              borderColor: COLOR_PRIMARY,
              backgroundColor: "rgba(0,123,62,0.12)",
              tension: 0.25,
              fill: true,
            },
          ],
        },
        options: Object.assign({}, baseOptions, {
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: axisTicks() },
            y: { beginAtZero: true, ticks: axisTicks() },
          },
        }),
      });
    }

    var elDona = document.getElementById("chart-dona");
    if (elDona && data.dona && !data.dona.vacio) {
      charts.dona = new Chart(elDona, {
        type: "doughnut",
        data: {
          labels: data.dona.labels,
          datasets: [
            {
              data: data.dona.values,
              backgroundColor: data.dona.colors || [
                COLOR_PRIMARY,
                COLOR_DANGER,
                COLOR_MUTED,
              ],
            },
          ],
        },
        options: Object.assign({}, baseOptions, {
          cutout: "55%",
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 12, font: { size: 11 } },
            },
          },
        }),
      });
    }

    var elSedes = document.getElementById("chart-sedes");
    if (elSedes && data.sedes && !data.sedes.vacio) {
      charts.sedes = new Chart(elSedes, {
        type: "bar",
        data: {
          labels: data.sedes.labels,
          datasets: [
            {
              label: "Movimientos",
              data: data.sedes.values,
              backgroundColor: COLOR_PRIMARY,
            },
          ],
        },
        options: Object.assign({}, baseOptions, {
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: axisTicks() },
            y: { beginAtZero: true, ticks: axisTicks() },
          },
        }),
      });
    }

    var elTop = document.getElementById("chart-top-alertas");
    if (elTop && data.top_alertas && !data.top_alertas.vacio) {
      charts.top_alertas = new Chart(elTop, {
        type: "bar",
        data: {
          labels: data.top_alertas.labels,
          datasets: [
            {
              label: "Alertas",
              data: data.top_alertas.values,
              backgroundColor: COLOR_DANGER,
            },
          ],
        },
        options: Object.assign({}, baseOptions, {
          indexAxis: "y",
          plugins: { legend: { display: false } },
          scales: {
            x: { beginAtZero: true, ticks: axisTicks() },
            y: { ticks: axisTicks() },
          },
        }),
      });
    }

    var elMotivos = document.getElementById("chart-motivos-alerta");
    if (elMotivos && data.motivos_alerta && !data.motivos_alerta.vacio) {
      charts.motivos_alerta = new Chart(elMotivos, {
        type: "bar",
        data: {
          labels: data.motivos_alerta.labels,
          datasets: [
            {
              label: "Alertas",
              data: data.motivos_alerta.values,
              backgroundColor: COLOR_DANGER,
            },
          ],
        },
        options: Object.assign({}, baseOptions, {
          indexAxis: "y",
          plugins: { legend: { display: false } },
          scales: {
            x: { beginAtZero: true, ticks: axisTicks() },
            y: { ticks: axisTicks() },
          },
        }),
      });
    }
  }

  function loadCharts() {
    var container = document.getElementById("dashboard-contenido");
    if (!container) return;
    fetch(datosUrl(), { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (r) {
        if (!r.ok) throw new Error("Error al cargar gráficos");
        return r.json();
      })
      .then(renderCharts)
      .catch(function () {
        setEmpty("linea", true);
        setEmpty("dona", true);
        setEmpty("sedes", true);
        setEmpty("top_alertas", true);
        setEmpty("motivos_alerta", true);
      });
  }

  function toggleCustomDates() {
    var preset = document.getElementById("preset");
    var blocks = document.querySelectorAll(".js-custom-dates");
    if (!preset || !blocks.length) return;
    var show = preset.value === "custom";
    blocks.forEach(function (el) {
      el.style.display = show ? "" : "none";
    });
  }

  function syncPushUrl() {
    var form = document.getElementById("dashboard-filtros");
    if (!form || !window.history || !window.history.replaceState) return;
    var qs = buildQueryFromForm();
    var base = form.getAttribute("hx-push-url") || "/panel/dashboard/";
    window.history.replaceState(null, "", qs ? base + "?" + qs : base);
  }

  document.addEventListener("DOMContentLoaded", function () {
    toggleCustomDates();
    loadCharts();
    var preset = document.getElementById("preset");
    if (preset) {
      preset.addEventListener("change", toggleCustomDates);
    }
  });

  document.body.addEventListener("htmx:afterSwap", function (evt) {
    if (evt.detail && evt.detail.target && evt.detail.target.id === "dashboard-contenido") {
      syncPushUrl();
      loadCharts();
    }
  });
})();
