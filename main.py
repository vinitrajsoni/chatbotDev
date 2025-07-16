from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
from audio_utils import text_to_speech, get_lang_code
from llm_chain import load_qa_chain
from new import translate
from bulbul_voice import transcribe_with_sarvam
import os

app = FastAPI()
qa_chain = load_qa_chain()

# Serve audio files from /static
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextQuery(BaseModel):
    text: str

@app.post("/ask")
async def ask_text(query: TextQuery):
    lang_code = get_lang_code(query.text)
    response = qa_chain(query.text, lang_code)

    filename = f"static/tts_{datetime.now().timestamp()}.wav"
    voice_output = text_to_speech(response, lang_code, filename=filename)

    with open("chat_log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.now()}] User: {query.text}\nBot: {response}\n")

    return {
        "response": response,
        "voice_output": f"http://localhost:8000/{voice_output}" if voice_output else None
    }

@app.post("/ask-voice")
async def ask_voice(file: UploadFile = File(...)):
    try:
        with open("temp_voice.wav", "wb") as f:
            f.write(await file.read())

        transcript, lang_code = transcribe_with_sarvam("temp_voice.wav")

        if not transcript:
            return {"error": "Transcription failed", "transcript": "", "response": ""}

        response = qa_chain(transcript, lang_code)

        filename = f"static/tts_{datetime.now().timestamp()}.wav"
        voice_output = text_to_speech(response, lang_code, filename=filename)

        return {
            "transcript": transcript,
            "language_code": lang_code,
            "response": response,
            "voice_output": f"http://localhost:8000/{voice_output}" if voice_output else None
        }

    except Exception as e:
        return {"error": str(e), "transcript": "", "response": ""}



@app.post("/clear-static")
async def clear_static():
    folder = "static"
    deleted = []

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted.append(filename)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

    return {"status": "success", "deleted": deleted}