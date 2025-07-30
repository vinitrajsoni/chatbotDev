import base64
import os
import random
import requests
from pydub import AudioSegment
from config import SARVAM_API_KEY
from sarvamai import SarvamAI

BULBUL_SPEAKERS = ["anushka", "manisha", "vidya", "arya", "abhilash", "karun", "hitesh"]
client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

def get_lang_code(text):
    try:
        response = requests.post(
            "https://api.sarvam.ai/text-lid",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json"
            },
            json={"input": text}
        )
        response.raise_for_status()
        lang_code = response.json().get('language_code')
        print(f"Detected Language Code: {lang_code}")
        return lang_code
    except Exception as e:
        print(f"Language detection failed: {e}")
        return None

def text_to_speech(text, lang_code, filename="static/output.wav", speaker=None):
    if not speaker:
        speaker = random.choice(BULBUL_SPEAKERS)

    text = text.replace('\n', ' ').replace("**", "").strip()
    chunk_size = 300
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    combined = AudioSegment.silent(duration=0)
    success_chunks = 0

    for i, chunk in enumerate(chunks):
        try:
            response = client.text_to_speech.convert(
                text=chunk,
                target_language_code=lang_code,
                model="bulbul:v2",
                speaker=speaker,
            )
            audio_base64 = response.audios[0] if response.audios else None

            if audio_base64:
                chunk_path = f"static/chunk_{i}.wav"
                with open(chunk_path, "wb") as f:
                    f.write(base64.b64decode(audio_base64))
                segment = AudioSegment.from_wav(chunk_path)
                combined += segment
                os.remove(chunk_path)
                success_chunks += 1
        except Exception as e:
            print(f"Chunk {i} failed: {e}")
            continue

    if success_chunks == 0:
        print("❌ No audio generated.")
        return None

    combined.export(filename, format="wav")
    print(f"✅ Audio saved to {filename}")
    return filename
