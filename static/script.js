(function(){
  const urlInput = document.getElementById("url");
  const btn = document.getElementById("btnDescargar");
  const log = document.getElementById("log");
  const status = document.getElementById("status");
  const monitorSwitch = document.getElementById("monitorSwitch");

  function addLog(text){
    const p = document.createElement("div");
    p.textContent = text;
    log.prepend(p);
  }

  btn.addEventListener("click", async ()=>{
    const url = urlInput.value.trim();
    if(!url){ addLog("Ingresa una URL"); return; }
    addLog("Enviando descarga: " + url);
    status.textContent = "Descargando...";
    try{
      const res = await fetch("/descargar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({url})});
      const j = await res.json();
      if(j.status === "ok"){
        addLog("Descargado: " + j.title + " → " + j.file);
        status.textContent = "Completado";
      } else {
        addLog("Error: " + (j.error || "desconocido"));
        status.textContent = "Error";
      }
    }catch(e){
      addLog("Error de red: " + e.message);
      status.textContent = "Error de red";
    }
  });

  // WebSocket monitor
  let ws;
  function setupWS(){
    ws = new WebSocket((location.protocol==="https:"?"wss://":"ws://") + location.host + "/monitor_ws");
    ws.addEventListener("open", ()=>{
      addLog("Conectado al monitor WebSocket");
      ws.send(JSON.stringify({cmd:"status"}));
    });
    ws.addEventListener("message", (ev)=>{
      try{
        const data = JSON.parse(ev.data);
        if(data.type === "detected"){
          addLog("Enlace detectado en portapapeles: " + data.url);
          // Auto solicitar descarga
          fetch("/descargar", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({url: data.url})});
          status.textContent = "Descargando (monitor)";
        } else if(data.type === "done"){
          addLog("Descarga completa: " + data.file + " (" + (data.title||"") + ")");
          status.textContent = "Completado";
        } else if(data.type === "error"){
          addLog("Error monitor: " + data.error);
          status.textContent = "Error";
        } else if(data.type === "status"){
          addLog("Estado monitor: " + JSON.stringify(data));
        }
      }catch(e){
        console.warn(e);
      }
    });
    ws.addEventListener("close", ()=>{
      addLog("WebSocket cerrado, reintentando en 2s...");
      setTimeout(setupWS, 2000);
    });
  }
  setupWS();

  // Toggle monitor on server by toggling a request (server reads global flag via pyperclip polling)
  monitorSwitch.addEventListener("change", ()=>{
    const on = monitorSwitch.checked;
    addLog("Modo Monitor " + (on ? "activado" : "desactivado") + " (local server)");
    // send a local POST to toggle the server side flag (server reads pyperclip globally).
    fetch("/toggle_monitor", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({enabled: on})})
      .catch(e => addLog("No se pudo cambiar modo monitor: " + e.message));
  });
})();
