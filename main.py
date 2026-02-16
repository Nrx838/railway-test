import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

# Инициализация
app = FastAPI()

# Настройка Gemini
# ВАЖНО: Ключ мы не хардкодим, а берем из переменных окружения
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class PromptRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"status": "Online", "platform": "Railway"}

@app.post("/chat")
def chat_with_gemini(request: PromptRequest):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured")
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(request.text)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Railway ожидает, что мы слушаем 0.0.0.0 и порт из переменной PORT
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
