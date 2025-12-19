# Grabadora Generativa con Micrófono USB

**Raspberry Pi 3B+ · GPIO · Audio Autónomo**

Este proyecto convierte una Raspberry Pi en un **dispositivo autónomo de grabación y reproducción sonora**:

* 🎤 Graba **voz limpia** desde un **micrófono USB**
* 🎧 Reproduce por la **salida de audífonos (jack 3.5 mm)**
* 🔘 La grabación se activa con un **botón físico**
* 🔁 El sistema reproduce grabaciones anteriores de forma aleatoria
* 🎶 El **pitch se modifica solo en reproducción** (-2, -1, +1, +2 semitonos)
* 🚀 El programa **arranca automáticamente al encender** la Raspberry Pi

---

## 1. Preparar una Raspberry Pi desde cero

### Sistema recomendado

* Raspberry Pi OS Lite (32-bit)
* Raspberry Pi 3B+
* Usuario con permisos sudo

Actualizar el sistema:

```bash
sudo apt update
sudo apt upgrade -y
```

Instalar dependencias básicas:

```bash
sudo apt install -y \
python3 \
python3-pip \
python3-numpy \
python3-gpiozero \
ffmpeg \
alsa-utils
```

Instalar librerías de Python:

```bash
pip3 install sounddevice pydub simpleaudio
```

---

## 2. Conexiones físicas

### Micrófono USB

* Conectar el micrófono USB directamente a la Raspberry Pi
* Evitar hubs USB sin alimentación

### Botón

* Un terminal del botón → **GPIO 4**
* El otro terminal → **GND**
* El botón es **normalmente abierto**
* Se usa **pull-up interno** (no se necesita resistencia externa)

### Salida de audio

* Conectar audífonos o bocina amplificada al **jack 3.5 mm**
* No usar HDMI para audio

---

## 3. Configurar la salida de audio por jack (ALSA)

Forzar salida por audífonos:

```bash
sudo raspi-config
```

Ruta:

```
System Options → Audio → Headphones
```

Reiniciar:

```bash
sudo reboot
```

---

## 4. Verificar que el micrófono USB está detectado

Listar dispositivos de grabación:

```bash
arecord -l
```

Ejemplo esperado:

```
card 1: Device [USB Audio Device], device 0: USB Audio
```

Listar dispositivos de reproducción:

```bash
aplay -l
```

Ejemplo esperado:

```
card 0: ALSA [bcm2835 ALSA], device 0: Headphones
```

Si el micrófono no aparece:

* probar otro puerto USB
* cambiar cable
* ejecutar `lsusb`

---

## 5. Ajustes recomendados al micrófono USB

Abrir mezclador:

```bash
alsamixer
```

* Presionar `F6`
* Seleccionar el micrófono USB
* Subir niveles:

  * Mic
  * Capture
* Desactivar (si existen):

  * AGC
  * Auto Gain
  * Noise Suppression

Guardar configuración:

```bash
sudo alsactl store
```

---

## 6. Testear el micrófono (antes del programa)

### Grabación de prueba

```bash
arecord -D plughw:1,0 -f cd test.wav
```

Hablar unos segundos y detener con `Ctrl+C`.

### Reproducción

```bash
aplay test.wav
```

Si se escucha correctamente, el micrófono está listo.

---

## 7. Estructura recomendada del proyecto

```
/home/pi/voice-device/
│
├── main.py
├── recordings/
│   └── (se llena automáticamente)
└── README.md
```

Crear carpetas:

```bash
mkdir -p ~/voice-device/recordings
```

---

## 8. Probar el programa manualmente

```bash
cd ~/voice-device
python3 main.py
```

Salida esperada:

```
Sistema listo. Presiona el botón para grabar.
```

Pruebas clave:

1. Presionar botón → grabación
2. Soltar botón → se guarda MP3
3. El sistema reproduce audios aleatorios
4. Cada reproducción cambia el pitch

---

## 9. Arranque automático usando .bashrc

Editar `.bashrc`:

```bash
nano ~/.bashrc
```

Agregar al final:

```bash
# --- Voice Device Autostart ---
if [ -z "$SSH_CONNECTION" ]; then
    cd /home/pi/voice-device
    python3 main.py &
fi
```

Esto asegura:

* Arranque automático en sesión local
* No interfiere con SSH
* Ejecución en segundo plano

---

## 10. Reinicio y validación

```bash
sudo reboot
```

Tras iniciar:

* Esperar 10–15 segundos
* Presionar el botón
* El sistema debe responder

---

## 11. Notas importantes

* No desconectar el micrófono USB en caliente
* No usar HDMI para audio
* El jack 3.5 mm tiene calidad limitada
* Pensado para uso continuo

---

## 12. Descripción conceptual

Este sistema:

* conserva la memoria sonora original
* reinterpreta cada reproducción
* no destruye la fuente
* evoluciona con el uso

Una **grabadora performativa autónoma**.
