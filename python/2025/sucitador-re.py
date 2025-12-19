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
recordings_folder = "recordings"

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

input_device = find_device(["usb"], is_input=True)
output_device = find_device(["bcm2835"], is_input=False)

sd.default.device = (input_device, output_device)

print("Entrada:", sd.query_devices(input_device)["name"])
print("Salida:", sd.query_devices(output_device)["name"])

# ================= BOTÓN =========================

button = Button(button_pin)

# ================= AUDIO UTILS ===================

def adjust_bit_depth(audio_data, target_depth):
    peak = np.max(np.abs(audio_data))
    if peak == 0:
        return np.zeros_like(audio_data, dtype=np.int16)
    max_val = 2 ** (target_depth - 1) - 1
    return (audio_data / peak * max_val).astype(np.int16)

# ================= GRABACIÓN =====================

def record_audio(min_duration=0.1, max_duration=10.0):
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

            data, _ = stream.read(int(fs * min_duration))
            chunks.append(data * gain)

            while button.is_pressed:
                if time.time() - start_time > max_duration:
                    break
                data, _ = stream.read(fs // 4)
                chunks.append(data * gain)

    except Exception as e:
        print("Error grabación:", e)
        return None

    audio = np.concatenate(chunks, axis=0)
    if np.max(np.abs(audio)) < 1e-5:
        return None

    print("Grabación finalizada")
    return adjust_bit_depth(audio, bit_depth)

# ================= GUARDADO ======================

def generate_filename():
    return os.path.join(
        recordings_folder,
        datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S.mp3")
    )

def save_audio(audio_data, filename):
    AudioSegment(
        audio_data.tobytes(),
        frame_rate=fs,
        sample_width=2,
        channels=1
    ).export(filename, format="mp3")
    print("Guardado:", filename)

# ================= EFECTOS =======================

def change_pitch(audio, semitones):
    if semitones is None:
        return audio
    return audio._spawn(
        audio.raw_data,
        overrides={
            "frame_rate": int(audio.frame_rate * (2 ** (semitones / 12)))
        }
    ).set_frame_rate(audio.frame_rate)

def distortion(audio, gain_db=10):
    boosted = audio + gain_db
    return boosted.apply_gain(-gain_db / 2)

def fuzz(audio):
    samples = np.array(audio.get_array_of_samples())
    clipped = np.clip(samples, -10000, 10000)
    return audio._spawn(clipped.tobytes())

def echo(audio, delay_ms=250, decay=0.5):
    echo_audio = audio - 10
    return audio.overlay(echo_audio, position=delay_ms)

def flanger(audio):
    delay = random.randint(5, 20)
    return audio.overlay(audio, position=delay)

def apply_random_effects(audio):
    # Pitch
    pitch = random.choice([None, -2, -1, 1, 2])
    audio = change_pitch(audio, pitch)

    # Efectos combinables
    if random.random() < 0.4:
        audio = distortion(audio, random.randint(6, 14))

    if random.random() < 0.3:
        audio = fuzz(audio)

    if random.random() < 0.4:
        audio = echo(audio, random.randint(150, 400))

    if random.random() < 0.3:
        audio = flanger(audio)

    return audio

# ================= REPRODUCCIÓN ==================

def play_random_recordings():
    while True:
        try:
            files = os.listdir(recordings_folder)
            if not files:
                time.sleep(1)
                continue

            file = random.choice(files)
            audio = AudioSegment.from_file(os.path.join(recordings_folder, file))

            audio = apply_random_effects(audio)

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

    try:
        save_audio(audio, generate_filename())
    except Exception as e:
        print("Error guardado:", e)
