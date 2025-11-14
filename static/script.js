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
  monitorSwitch.addEventListener("change", async ()=>{
    const on = monitorSwitch.checked;
    if(on){
      // Solicitar permiso de portapapeles
      try{
        const permission = await navigator.permissions.query({name: "clipboard-read"});
        if(permission.state === "denied"){
          addLog("❌ Permiso de portapapeles denegado");
          monitorSwitch.checked = false;
          return;
        }
        if(permission.state === "prompt"){
          addLog("📋 Solicita permiso para acceder al portapapeles...");
        }
      }catch(e){
        addLog("⚠️ Permisos de portapapeles no soportados en este navegador");
      }
      addLog("✅ Modo Monitor activado");
    } else {
      addLog("❌ Modo Monitor desactivado");
    }
    
    // send a local POST to toggle the server side flag (server reads pyperclip globally).
    fetch("/toggle_monitor", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({enabled: on})})
      .catch(e => addLog("No se pudo cambiar modo monitor: " + e.message));
    
    // Si se activa el monitor, comenzar a monitorear portapapeles
    if(on){
      monitorClipboard();
    }
  });
  
  // Monitorear portapapeles periódicamente
  let lastClipboard = "";
  async function monitorClipboard(){
    if(!monitorSwitch.checked) return;
    
    try{
      const text = await navigator.clipboard.readText();
      if(text && text !== lastClipboard){
        lastClipboard = text;
        // Enviar URL al servidor
        fetch("/check_clipboard_url", {
          method:"POST", 
          headers:{"Content-Type":"application/json"}, 
          body: JSON.stringify({url: text})
        }).catch(e => console.error(e));
      }
    }catch(e){
      // Permiso denegado o API no disponible
      if(e.name === "NotAllowedError"){
        addLog("❌ Permiso de portapapeles denegado");
        monitorSwitch.checked = false;
      }
    }
    
    setTimeout(monitorClipboard, 2000);
  }

  // Cookies UI: show/hide panel and upload cookies to server
  const btnCookies = document.getElementById("btnCookies");
  const cookiesPanel = document.getElementById("cookiesPanel");
  const btnUploadCookies = document.getElementById("btnUploadCookies");
  const cookiesText = document.getElementById("cookiesText");
  const cookiesSecret = document.getElementById("cookiesSecret");

  if(btnCookies){
    btnCookies.addEventListener("click", ()=>{
      if(!cookiesPanel) return;
      cookiesPanel.style.display = (cookiesPanel.style.display === "none" || cookiesPanel.style.display === "") ? "block" : "none";
    });
  }

  if(btnUploadCookies){
    btnUploadCookies.addEventListener("click", async ()=>{
      const cookies = cookiesText ? cookiesText.value.trim() : "";
      const secret = cookiesSecret ? cookiesSecret.value.trim() : undefined;
      if(!cookies){ addLog("Pega el contenido de cookies.txt antes de subir"); return; }
      addLog("Subiendo cookies...");
      try{
        const res = await fetch("/upload_cookies", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({cookies, secret})});
        const j = await res.json();
        if(res.ok && j.status === "ok"){
          addLog("Cookies subidas correctamente");
        } else {
          addLog("Error subiendo cookies: " + (j.error || res.statusText));
        }
      }catch(e){
        addLog("Error de red al subir cookies: " + e.message);
      }
    });
  }
})();
