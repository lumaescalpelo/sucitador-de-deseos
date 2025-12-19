from gpiozero import Button
import sounddevice as sd
from pydub import AudioSegment
import numpy as np
import datetime
import random
import threading
import os
import simpleaudio as sa
import time

# ================= CONFIGURACIÓN =================

button_pin = 4
fs = 44100
gain = 0.8
bit_depth = 16
recordings_folder = "/home/pi/Music/recordings"

os.makedirs(recordings_folder, exist_ok=True)

# ================= AUDIO DEVICE ==================

def find_device(name_keywords, is_input=True):
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        name = d["name"].lower()
        if all(k.lower() in name for k in name_keywords):
            if is_input and d["max_input_channels"] > 0:
                return i
            if not is_input and d["max_output_channels"] > 0:
                return i
    raise RuntimeError(f"No se encontró dispositivo: {name_keywords}")

# Entrada: micrófono USB
input_device = find_device(["usb"], is_input=True)

# Salida: jack 3.5 mm (bcm2835)
output_device = find_device(["bcm2835"], is_input=False)

sd.default.device = (input_device, output_device)

print("Entrada de audio:", sd.query_devices(input_device)["name"])
print("Salida de audio:", sd.query_devices(output_device)["name"])

# ================= BOTÓN =========================

button = Button(button_pin)

# ================= AUDIO UTILS ===================

def adjust_bit_depth(audio_data, target_depth):
    peak = np.max(np.abs(audio_data))
    if peak == 0:
        return np.zeros_like(audio_data, dtype=np.int16)

    max_val = 2 ** (target_depth - 1) - 1
    scaled = audio_data / peak * max_val
    return scaled.astype(np.int16)

# ================= GRABACIÓN =====================

def record_audio(
    min_duration=0.1,    # segundos mínimos grabados
    max_duration=10.0    # límite de seguridad
):
    print("Grabando...")
    chunks = []
    start_time = time.time()

    try:
        with sd.InputStream(
            samplerate=fs,
            channels=1,
            device=input_device,
            dtype="float32"
        ) as stream:

            # --- captura inicial garantizada ---
            data, _ = stream.read(int(fs * min_duration))
            chunks.append(data * gain)

            # --- grabación mientras el botón esté presionado ---
            while button.is_pressed:
                if time.time() - start_time > max_duration:
                    print("Tiempo máximo alcanzado")
                    break

                data, _ = stream.read(fs // 4)
                chunks.append(data * gain)

    except Exception as e:
        print("Error durante grabación:", e)
        return None

    if not chunks:
        print("Grabación vacía (descartada)")
        return None

    audio = np.concatenate(chunks, axis=0)

    # descartar audio demasiado silencioso
    if np.max(np.abs(audio)) < 1e-5:
        print("Audio demasiado silencioso (descartado)")
        return None

    audio = adjust_bit_depth(audio, bit_depth)
    print("Grabación finalizada")
    return audio

# ================= GUARDADO ======================

def generate_filename():
    now = datetime.datetime.now()
    return os.path.join(
        recordings_folder,
        now.strftime("%Y-%m-%d-%H-%M-%S.mp3")
    )

def save_audio(audio_data, filename):
    audio = AudioSegment(
        audio_data.tobytes(),
        frame_rate=fs,
        sample_width=2,
        channels=1
    )
    audio.export(filename, format="mp3")
    print("Guardado:", filename)

# ================= PITCH =========================

def change_pitch(audio_segment, semitones):
    return audio_segment._spawn(
        audio_segment.raw_data,
        overrides={
            "frame_rate": int(
                audio_segment.frame_rate * (2 ** (semitones / 12))
            )
        }
    ).set_frame_rate(audio_segment.frame_rate)

# ================= REPRODUCCIÓN ==================

def play_random_recordings():
    pitch_choices = [-2, -1, 1, 2]

    while True:
        try:
            files = os.listdir(recordings_folder)
            if not files:
                time.sleep(1)
                continue

            file = random.choice(files)
            path = os.path.join(recordings_folder, file)

            audio = AudioSegment.from_file(path)
            semitones = random.choice(pitch_choices)
            audio = change_pitch(audio, semitones)

            playback = sa.play_buffer(
                audio.raw_data,
                num_channels=audio.channels,
                bytes_per_sample=audio.sample_width,
                sample_rate=audio.frame_rate
            )
            playback.wait_done()

        except Exception as e:
            print("Error reproducción:", e)
            time.sleep(1)

# ================= THREAD ========================

threading.Thread(
    target=play_random_recordings,
    daemon=True
).start()

# ================= LOOP PRINCIPAL ================

print("Sistema listo. Presiona el botón para grabar.")

while True:
    button.wait_for_press()

    audio = record_audio()
    if audio is None:
        print("Nada que guardar")
        continue

    filename = generate_filename()
    try:
        save_audio(audio, filename)
    except Exception as e:
        print("Error al guardar:", e)
