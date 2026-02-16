import os
import redis  # <--- 1. Импортируем библиотеку для базы данных
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

# Инициализация
app = FastAPI()

# --- Настройка Gemini ---
# ВАЖНО: Ключ мы не хардкодим, а берем из переменных окружения
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class PromptRequest(BaseModel):
    text: str

# --- Эндпоинты ---

@app.get("/")
def read_root():
    return {"status": "Online", "platform": "Railway"}

@app.get("/test-redis") # <--- 2. Новый эндпоинт: Проверка памяти
def test_redis_connection():
    # Railway автоматически создает эту переменную, когда ты добавляешь Redis в проект
    redis_url = os.getenv("REDIS_URL")
    
    if not redis_url:
        return {"status": "error", "detail": "REDIS_URL variable not found. Check Railway Variables tab."}

    try:
        # Подключаемся к базе. decode_responses=True нужен, чтобы получать текст, а не байты
        r = redis.from_url(redis_url, decode_responses=True)
        
        # ТЕСТ ЗАПИСИ: Сохраняем данные в Redis
        r.set("flymyai_check", "Redis is connected and working! 🚀")
        
        # ТЕСТ ЧТЕНИЯ: Читаем то, что только что записали
        value = r.get("flymyai_check")
        
        return {
            "status": "success", 
            "message_from_db": value,
            "backend": "Railway Redis"
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/chat")
def chat_with_gemini(request: PromptRequest):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured")
    
    try:
        # Я поставил стабильную версию 'gemini-1.5-flash', чтобы точно работало
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content(request.text)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Railway ожидает, что мы слушаем 0.0.0.0 и порт из переменной PORT
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
