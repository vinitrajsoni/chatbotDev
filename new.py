from google import genai
from config import GOOGLE_API_KEY
LANG_CODE_NAME = {
    "en-IN": "English", "hi-IN": "Hindi", "bn-IN": "Bengali",
    "gu-IN": "Gujarati", "kn-IN": "Kannada", "ml-IN": "Malayalam",
    "mr-IN": "Marathi", "or-IN": "Odia", "pa-IN": "Punjabi",
    "ta-IN": "Tamil", "te-IN": "Telugu", "ur-IN": "Urdu"
}
def translate(text, lang_code):
    lang = LANG_CODE_NAME.get(lang_code)
    print(lang)
    client = genai.Client(api_key=GOOGLE_API_KEY)

    prompt = f"Translate the following text to {lang}:\n\n{text}"

    response = client.models.generate_content(
        model="models/gemini-1.5-flash",
        contents=prompt
    )
    print(response.text)  # ✅ Print first
    return response.text   # ✅ Then return
