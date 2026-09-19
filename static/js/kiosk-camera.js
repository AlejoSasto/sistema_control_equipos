/**
 * Escaneo QR por cámara en el kiosco de portería.
 * Al leer un código: cierra la cámara, rellena #scanner-input y dispara
 * una sola vez el mismo submit HTMX que pistola / teclado.
 */
(function () {
  var form = document.getElementById("form-scanner");
  var input = document.getElementById("scanner-input");
  var btn = document.getElementById("btn-toggle-camera");
  var btnLabel = document.getElementById("btn-toggle-camera-label");
  var wrap = document.getElementById("qr-reader-wrap");
  var statusEl = document.getElementById("kiosk-camera-status");
  var readerId = "qr-reader";

  if (!form || !input || !btn || !wrap) return;

  var scanner = null;
  var running = false;
  var handling = false;

  function setStatus(message, kind) {
    if (!statusEl) return;
    if (!message) {
      statusEl.hidden = true;
      statusEl.textContent = "";
      statusEl.className = "kiosk-camera-status";
      return;
    }
    statusEl.hidden = false;
    statusEl.textContent = message;
    statusEl.className = "kiosk-camera-status" + (kind ? " is-" + kind : "");
  }

  function isSecureContextOk() {
    return window.isSecureContext || location.hostname === "localhost" || location.hostname === "127.0.0.1";
  }

  function setUiRunning(isOn) {
    running = isOn;
    wrap.hidden = !isOn;
    btn.setAttribute("aria-pressed", isOn ? "true" : "false");
    if (btnLabel) btnLabel.textContent = isOn ? "Cerrar cámara" : "Usar cámara";
  }

  function submitCodigo(texto) {
    var codigo = (texto || "").trim();
    if (!codigo) return;
    input.value = codigo;
    if (typeof htmx !== "undefined") {
      htmx.trigger(form, "submit");
    } else {
      form.requestSubmit ? form.requestSubmit() : form.submit();
    }
  }

  function stopCamera() {
    if (!scanner) {
      setUiRunning(false);
      return Promise.resolve();
    }
    return scanner
      .stop()
      .catch(function () { /* ya detenido */ })
      .then(function () {
        try {
          scanner.clear();
        } catch (e) { /* ignore */ }
        scanner = null;
        setUiRunning(false);
        setStatus("");
        if (input) input.focus();
      });
  }

  function onScanSuccess(decodedText) {
    if (!running || handling) return;
    handling = true;
    var codigo = (decodedText || "").trim();
    stopCamera().then(function () {
      if (codigo) submitCodigo(codigo);
      handling = false;
    });
  }

  function startCamera() {
    if (typeof Html5Qrcode === "undefined") {
      setStatus("No se pudo cargar la librería de cámara. Use pistola o teclado.", "error");
      return;
    }
    if (!isSecureContextOk()) {
      setStatus("La cámara requiere HTTPS (o localhost). Use pistola o escriba el código.", "error");
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("Este dispositivo no permite acceso a la cámara. Use pistola o teclado.", "error");
      return;
    }

    handling = false;
    setStatus("Solicitando permiso de cámara…", "ok");
    setUiRunning(true);

    scanner = new Html5Qrcode(readerId, { verbose: false });
    var config = {
      fps: 8,
      qrbox: function (viewfinderWidth, viewfinderHeight) {
        var edge = Math.floor(Math.min(viewfinderWidth, viewfinderHeight) * 0.72);
        return { width: edge, height: edge };
      },
      aspectRatio: 1.0,
    };

    var cameraConfig = { facingMode: "environment" };

    scanner
      .start(cameraConfig, config, onScanSuccess, function () { /* frame sin QR */ })
      .then(function () {
        setStatus("Cámara activa — apunte al QR del titular.", "ok");
      })
      .catch(function (err) {
        var msg = (err && err.name === "NotAllowedError")
          ? "Permiso de cámara denegado. Active el permiso o use pistola/teclado."
          : "No se pudo abrir la cámara. Use pistola o escriba el código manualmente.";
        setStatus(msg, "error");
        return stopCamera();
      });
  }

  btn.addEventListener("click", function () {
    if (running) {
      stopCamera();
    } else {
      startCamera();
    }
  });

  window.addEventListener("pagehide", function () {
    if (running) stopCamera();
  });
  window.addEventListener("beforeunload", function () {
    if (running && scanner) {
      try { scanner.stop(); } catch (e) { /* ignore */ }
    }
  });
})();
