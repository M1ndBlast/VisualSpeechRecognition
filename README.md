# Reconocimiento Visual del Habla

## Descripción
Este proyecto integra tecnologías de Node.js y Python para implementar un sistema de reconocimiento visual del habla. La arquitectura del proyecto se divide en dos componentes principales: una interfaz de usuario basada en Node.js alojada en la carpeta `cliente/` y un servidor en Python ubicado en la carpeta `server/`.

## Estructura del Proyecto
- **Carpeta Cliente (`cliente/`):**
  - `index.js`: Archivo principal de Node.js para la interfaz del usuario.
  - `mConsole.js`: Módulo personalizado para la consola del cliente.
  - `whatsapp.js`: Módulo para integrar funcionalidades de WhatsApp.
  - `package.json`: Archivo de configuración de Node.js que incluye dependencias y metadatos del proyecto.
- **Carpeta Servidor (`server/`):**
  - `index.py`: Archivo principal del servidor Python.
  - `face_landmarker.py`: Módulo Python para el reconocimiento facial y análisis de marcas faciales.

## Dependencias
- Node.js (v20.9.0)
- Python (3.10.13)
- Bibliotecas de Python especificadas en los archivos de requerimientos del servidor.
- Dependencias de Node.js especificadas en `package.json`:
  - `qrcode-terminal`: ^0.12.0
  - `socket.io`: ^4.6.1
  - `socket.io-client`: ^4.6.1
  - `uuid`: ^9.0.0
  - `whatsapp-web.js`: ^1.20.0

## Instalación y Configuración
1. Clonar el repositorio desde [GitHub](https://github.com/M1ndBlast/VisualSpeechRecognition).
2. Instalar las dependencias de Node.js:
   ```
   cd client/
   npm install
   ```
3. Instalar las dependencias de Python:
   ```
   cd server/
   pip install -r requirements.txt
   ```
4. Iniciar el servidor y el cliente según las instrucciones específicas en los archivos README de cada carpeta.

## Uso

Una vez completadas la instalación y configuración, sigue estos pasos para iniciar el sistema:

- **Para el Módulo Cliente:**
  1. Navega a la carpeta `cliente/` desde la línea de comandos.
  2. Ejecuta el siguiente comando para iniciar la interfaz de usuario de Node.js:
     ```bash
     npm start
     ```

- **Para el Servidor:**
  1. Navega a la carpeta `server/` desde la línea de comandos.
  2. Ejecuta el siguiente comando para iniciar el servidor Python:
     ```bash
     python index.py
     ```

Asegúrate de que el servidor esté corriendo antes de iniciar el módulo cliente para garantizar una conexión exitosa entre ambos componentes.

### Solución de Problemas

#### Error al Iniciar el Servidor: Falta libGL.so.1

Si al intentar iniciar el servidor con `python index.py` encuentras un error similar a:

```
ImportError: libGL.so.1: cannot open shared object file: No such file or directory
```

Esto se debe a la falta de la biblioteca `libGL`, que es necesaria para que OpenCV funcione correctamente. Para resolver este problema, instala la biblioteca faltante utilizando el siguiente comando en sistemas basados en Debian o Ubuntu:

```bash
sudo apt-get update -y
sudo apt-get install libgl1-mesa-glx -y
```

Después de instalar esta biblioteca, intenta nuevamente iniciar el servidor.

## Contribución
Las contribuciones al proyecto son bienvenidas. Por favor, revise las [pautas de contribución](https://github.com/M1ndBlast/VisualSpeechRecognition#contributing) y abra un 'issue' o 'pull request' en GitHub.

## Licencia
Este proyecto está licenciado bajo la Licencia ISC. Para más detalles, consulte el archivo `LICENSE` en el repositorio.

---

**Autor:** m1ndblast  
**Repositorio GitHub:** [VisualSpeechRecognition](https://github.com/M1ndBlast/VisualSpeechRecognition)  
**Informes de Errores:** [Issues](https://github.com/M1ndBlast/VisualSpeechRecognition/issues)  
**Página de Inicio:** [GitHub Page](https://github.com/M1ndBlast/VisualSpeechRecognition#readme)