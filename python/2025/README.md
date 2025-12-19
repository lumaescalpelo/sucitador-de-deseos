# Preparación de Raspberry Pi OS Bookworm (64‑bit)

Este documento describe **todo lo necesario antes de correr el programa** en una Raspberry Pi con **Raspberry Pi OS Bookworm (64‑bit)**. Está pensado para que puedas copiarlo directamente a tu repositorio Git y usarlo como checklist reproducible.

---

## 0. Sistema base

* **Sistema:** Raspberry Pi OS Bookworm (64‑bit, versión FULL)
* **Placa objetivo:** Raspberry Pi 3B+
* **Usuario:** `pi` con permisos sudo

Actualizar sistema:

```bash
sudo apt update
sudo apt upgrade -y
```

Reiniciar:

```bash
sudo reboot
```

---

## 1. Configuración de audio del sistema

### 1.1 Forzar salida por jack 3.5 mm

Abrir configuración:

```bash
sudo raspi-config
```

Ruta:

```
System Options → Audio → Headphones
```

Salir y reiniciar.

---

### 1.2 Verificar dispositivos de audio

Salida de audio:

```bash
aplay -l
```

Debe aparecer algo similar a:

```
card X: bcm2835 Headphones
```

Entrada (micrófono USB):

```bash
arecord -l
```

Debe aparecer algo similar a:

```
card Y: USB Audio Device
```

> **Nota:** Los números de card pueden cambiar. No se deben usar números fijos en el código.

---

### 1.3 Forzar ALSA a usar bcm2835 como salida por defecto

Editar:

```bash
sudo nano /etc/asound.conf
```

Contenido recomendado:

```conf
defaults.pcm.card bcm2835
defaults.ctl.card bcm2835
```

Guardar y reiniciar:

```bash
sudo reboot
```

---

### 1.4 Test rápido de audio

```bash
speaker-test -t sine -f 440
```

Si escuchas un tono, la salida está correctamente configurada.

---

## 2. Micrófono USB

### 2.1 Ajustar niveles

```bash
alsamixer
```

* Presionar `F6`
* Seleccionar el micrófono USB
* Subir `Mic` y `Capture`
* Desactivar AGC / Auto Gain si existen

Guardar configuración:

```bash
sudo alsactl store
```

---

### 2.2 Test de grabación independiente

```bash
arecord -f cd test.wav
```

Hablar unos segundos y detener con `Ctrl+C`.

Reproducir:

```bash
aplay test.wav
```

---

## 3. GPIO (botón físico)

### 3.1 Instalación de gpiozero

```bash
sudo apt install -y python3-gpiozero
```

### 3.2 Cableado del botón

* Un pin → **GPIO 4**
* Otro pin → **GND**
* Botón normalmente abierto
* Se usa pull‑up interno (no resistencia externa)

---

## 4. Python y entorno virtual

### 4.1 Verificar versión de Python

```bash
python3 --version
```

Debe ser **Python 3.11.x** (Bookworm).

---

### 4.2 Dependencias del sistema (obligatorias)

```bash
sudo apt install -y \
build-essential \
python3-dev \
python3-venv \
libffi-dev \
libasound2-dev \
portaudio19-dev \
ffmpeg
```

---

### 4.3 Crear entorno virtual

Desde la carpeta del proyecto:

```bash
python3 -m venv venv --system-site-packages
```

Activar:

```bash
source venv/bin/activate
```

---

### 4.4 Instalar dependencias Python

Con el `venv` activo:

```bash
pip install --upgrade pip setuptools wheel
pip install numpy sounddevice pydub simpleaudio
```

---

### 4.5 Verificación crítica

```bash
python - <<EOF
import gpiozero
import sounddevice
import pydub
import simpleaudio
import numpy
import audioop
print("Entorno listo")
EOF
```

Si no hay errores, el entorno está correctamente configurado.

---

## 5. Estructura recomendada del proyecto

```
project/
├── main.py
├── recordings/
├── venv/
└── README.md
```

Crear carpeta de grabaciones:

```bash
mkdir -p recordings
```

---

## 6. Arranque automático (bashrc)

Editar:

```bash
nano ~/.bashrc
```

Agregar al final:

```bash
# --- Autostart voice device ---
if [ -z "$SSH_CONNECTION" ]; then
    cd /home/pi/project
    source venv/bin/activate
    python main.py &
fi
```

> Ajusta la ruta y el nombre del script según tu proyecto.

---

## 7. Checklist antes de correr el programa

* [ ] Audio por jack funciona (`speaker-test`)
* [ ] Micrófono USB graba (`arecord`)
* [ ] gpiozero importa sin error
* [ ] `sounddevice` detecta dispositivos
* [ ] `pydub` importa correctamente
* [ ] `audioop` disponible
* [ ] `venv` activo

---

## 8. Notas importantes

* No usar Python 3.13
* No mezclar repositorios
* No depender de números de card ALSA
* Este setup es estable para uso continuo / instalación

---

**Estado:** Raspberry Pi lista para correr el programa.
