import requests
from config import SARVAM_API_KEY

def transcribe_with_sarvam(audio_path):
    url = "https://api.sarvam.ai/speech-to-text-translate"

    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    with open(audio_path, "rb") as f:
        files = {"file": ("audio.wav", f, "audio/wav")}

        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        data = response.json()

        # # Optional: print for debug
        # print("✅ Sarvam Transcription Response:", data)

        # Extract the translated transcript and language
        translated_text = data.get("transcript")
        detected_language = data.get("language_code")

        return translated_text, detected_language

    else:
        print("❌ Sarvam Transcription Failed")
        print("Status code:", response.status_code)
        print("Response:", response.text)
        return "", ""
