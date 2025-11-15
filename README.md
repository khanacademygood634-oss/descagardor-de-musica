# Descargador de música - YouTube a MP3

Proyecto generado automáticamente.
**Advertencia importante**: Cuando se despliega en un *servidor remoto* (Render, Heroku, etc.), el servicio **no** podrá acceder al portapapeles del usuario final — el monitoreo del portapapeles funciona cuando corres esta aplicación **localmente** en tu máquina (Windows, Linux, Mac o Termux en Android).

## Estructura
```
/descargador-musica-youtube
│── app.py
│── requirements.txt
│── render.yaml
│── README.md
│── static/
│     ├── style.css
│     └── script.js
└── templates/
      └── index.html
```

## Requisitos
- Python 3.9+
- ffmpeg (para convertir a mp3) instalado en el sistema y accesible en PATH.
- pip install -r requirements.txt

## Uso local rápido
1. Clona el repositorio o coloca los archivos en una carpeta.
2. Instala dependencias: `pip install -r requirements.txt`
3. Asegúrate de tener `ffmpeg` instalado.
4. Ejecuta: `python app.py`
5. Abre `http://127.0.0.1:5000` en el navegador.

### Modo Monitor (Local)
- En la interfaz activa el switch **Modo Monitor**. La app revisa el portapapeles cada 1.5s y si detecta una URL de YouTube la descargará automáticamente a la carpeta **Descargas** de tu sistema.

### Despliegue en Render
- Sube los archivos al repositorio: `https://github.com/khanacademygood634-oss/descagardor-de-musica`
- En Render, crea un nuevo servicio web vinculado a ese repo. El `render.yaml` incluido tiene comandos básicos para instalar y ejecutar.
- Nota: el modo monitor NO funcionará en Render ya que el servidor no tiene acceso al portapapeles de tus dispositivos clientes.

## Autenticación de YouTube (Cookies)
YouTube puede solicitar iniciar sesión para descargar ciertos videos. Para resolverlo, necesitas proporcionar un archivo `cookies.txt`.

### Opción 1: Subir cookies desde la UI (Recomendado para Render)
1. **Exporta cookies desde tu navegador**:
   - Instala una extensión de navegador como "Get cookies.txt" (Chrome Web Store, Firefox Add-ons).
   - Abre YouTube en una pestaña y asegúrate de estar **conectado** a tu cuenta.
   - Usa la extensión para exportar cookies a un archivo `cookies.txt`.
   - Copia el contenido completo del archivo.

2. **Sube las cookies desde la interfaz web**:
   - Abre tu aplicación en `https://descagardor-de-musica.onrender.com/` (o tu URL en Render).
   - Haz clic en el botón **"Configuración de cookies"**.
   - Pega el contenido de `cookies.txt` en el área de texto.
   - (Opcional) Si configuraste `YTDLP_UPLOAD_SECRET`, pega el secreto en el campo correspondiente.
   - Haz clic en **"Subir cookies"**.
   - La app guardará las cookies y las usará en próximas descargas.

### Opción 2: Usar variable de entorno en Render (Alternativa)
1. Exporta cookies como se describe arriba.
2. En el dashboard de Render → tu servicio → **Environment**:
   - Haz clic en **"Add Secret"**.
   - Key: `YTDLP_COOKIES_CONTENT`
   - Value: (pega el contenido completo de `cookies.txt`).
3. Guarda. Render redeploy automáticamente.
4. La app leerá la variable y usará esas cookies automáticamente.

### Opción 3: Ejecutar localmente con cookies
1. Exporta `cookies.txt` como se describe.
2. Desde PowerShell en la carpeta del proyecto:
   ```powershell
   $env:YTDLP_COOKIES_CONTENT = Get-Content .\cookies.txt -Raw
   python app.py
   ```
3. La app usará las cookies en la sesión actual.

### Proteger el endpoint con secreto (Seguridad)
Si usas la **Opción 1** (UI), es recomendable proteger el endpoint `/upload_cookies`:
1. En Render, añade un nuevo secret:
   - Key: `YTDLP_UPLOAD_SECRET`
   - Value: (una contraseña aleatoria, ej: `abc123xyz`).
2. Guarda y Render redeploy.
3. Desde ahora, al subir cookies por la UI, la app pedirá el secreto. Pégalo en el campo "Secret (si usas YTDLP_UPLOAD_SECRET)".

### Notas de seguridad
- Las cookies contienen tu sesión de Google/YouTube. Trátalas como información sensible.
- Usa `YTDLP_UPLOAD_SECRET` para evitar que desconocidos suban cookies malintencionadas si tu app es pública.
- Si necesitas cambiar/actualizar las cookies, repite el proceso: sube nuevas cookies y sobrescribirá las anteriores.

### Más información
- Guía oficial de yt-dlp sobre cookies: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp
- Exportar cookies desde el navegador: https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies

## Cómo subir a GitHub (ejemplo)
```bash
git init
git add .
git commit -m "Proyecto descargador YouTube a MP3"
git branch -M main
git remote add origin https://github.com/khanacademygood634-oss/descagardor-de-musica.git
git push -u origin main
```

