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

## Cómo subir a GitHub (ejemplo)
```bash
git init
git add .
git commit -m "Proyecto descargador YouTube a MP3"
git branch -M main
git remote add origin https://github.com/khanacademygood634-oss/descagardor-de-musica.git
git push -u origin main
```

