from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY
import requests

LANG_CODE_NAME = {
    "en-IN": "English", "hi-IN": "Hindi", "bn-IN": "Bengali",
    "gu-IN": "Gujarati", "kn-IN": "Kannada", "ml-IN": "Malayalam",
    "mr-IN": "Marathi", "or-IN": "Odia", "pa-IN": "Punjabi",
    "ta-IN": "Tamil", "te-IN": "Telugu", "ur-IN": "Urdu"
}

GREETINGS = {
    "English": "Hello! How can I help you?",
    "Hindi": "नमस्ते! मैं आपकी किस प्रकार सहायता कर सकता हूँ?",
    "Bengali": "হ্যালো! আমি কীভাবে আপনার সাহায্য করতে পারি?",
    "Gujarati": "હેલો! હું તમને કેવી રીતે મદદ કરી શકું?",
    "Kannada": "ಹಲೋ! ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
    "Malayalam": "ഹലോ! ഞാൻ നിങ്ങൾക്ക് എങ്ങനെ സഹായിക്കാം?",
    "Marathi": "हॅलो! मी तुम्हाला कशी मदत करू शकतो?",
    "Odia": "ନମସ୍କାର! ମୁଁ କିପରି ଆପଣଙ୍କୁ ସାହାଯ୍ୟ କରିପାରିବି?",
    "Punjabi": "ਹੈਲੋ! ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
    "Tamil": "வணக்கம்! நான் உங்களுக்கு எப்படி உதவலாம்?",
    "Telugu": "హలో! నేను మీకు ఎలా సహాయపడగలను?",
    "Urdu": "ہیلو! میں آپ کی کس طرح مدد کر سکتا ہوں؟"
}

FALLBACK_RESPONSES = {
    "English": "Sorry, this isn't relevant. Can I help with something else?",
    "Hindi": "माफ करें, यह प्रासंगिक नहीं है। क्या मैं आपकी किसी और चीज़ में मदद कर सकता हूँ?",
    "Bengali": "দুঃখিত, এটি প্রাসঙ্গিক নয়। আমি কি অন্য কিছুতে সাহায্য করতে পারি?",
    "Gujarati": "માફ કરશો, આ સંબંધિત નથી. શું હું બીજી કોઈ બાબતમાં મદદ કરી શકું?",
    "Kannada": "ಕ್ಷಮಿಸಿ, ಇದು ಸಂಬಂಧಿತವಾಗಿಲ್ಲ. ನಾನು ಮತ್ತೊಂದು ಸಹಾಯ ಮಾಡಬಹುದೇ?",
    "Malayalam": "ക്ഷമിക്കണം, ഇത് പ്രസക്തമായതല്ല. ഞാൻ മറ്റെന്തെങ്കിലുമൊക്കെ സഹായിക്കാമോ?",
    "Marathi": "माफ करा, हे संबंधित नाही. मी इतर काही मदत करू शकतो का?",
    "Odia": "ମାନ୍ୟ କରନ୍ତୁ, ଏହିଟି ସମ୍ବନ୍ଧିତ ନୁହେଁ । ମୁଁ ଅନ୍ୟ କିଛିରେ ସାହାଯ୍ୟ କରିପାରିବି କି?",
    "Punjabi": "ਮਾਫ ਕਰਨਾ, ਇਹ ਸਬੰਧਤ ਨਹੀਂ ਹੈ। ਕੀ ਮੈਂ ਹੋਰ ਕਿਸੇ ਗੱਲ 'ਚ ਤੁਹਾਡੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
    "Tamil": "மன்னிக்கவும், இது தொடர்புடையதல்ல. நான் வேறு எதையாவது உதவ முடியுமா?",
    "Telugu": "క్షమించండి, ఇది సంబంధించినది కాదు. నేను ఇంకేదైనా సహాయపడగలనా?",
    "Urdu": "معاف کیجیے، یہ متعلقہ نہیں ہے۔ کیا میں کسی اور چیز میں آپ کی مدد کر سکتا ہوں؟"
}

def translate_libre(text, source_lang="en", target_lang="hi"):
    url = "https://libretranslate.de/translate"
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }
    response = requests.post(url, json=payload)
    return response.json().get("translatedText")

def load_qa_chain():
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local("embeddings/faiss_index", embedding, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 3})

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=GOOGLE_API_KEY,
    )

    def reply(text: str, lang_code: str):
        lang = LANG_CODE_NAME.get(lang_code, "English")
        
        if text.lower().strip() in ["hi", "hello", "hey"]:
            return GREETINGS.get(lang, GREETINGS["English"])

        docs = retriever.get_relevant_documents(text)
        context = "\n\n".join(doc.page_content for doc in docs)

        fallback = FALLBACK_RESPONSES.get(lang, FALLBACK_RESPONSES["English"])

        prompt = f"""
You are a helpful assistant. Always respond strictly in {lang}.
You must answer using **only** the provided context.
If the answer is not in the context, reply exactly: "{fallback}"

Context:
{context}

Question:
{text}
"""
        result = llm.invoke(prompt)
        return result.content

    return reply
