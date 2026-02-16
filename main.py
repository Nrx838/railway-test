import os
import json
import redis
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai

# --- Инициализация ---
app = FastAPI()

# 1. Настройка Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# 2. Настройка Redis (Память)
redis_url = os.getenv("REDIS_URL")
r = None
if redis_url:
    # decode_responses=True важно, чтобы получать строки, а не байты
    r = redis.from_url(redis_url, decode_responses=True)

# Модель данных для запроса
class ChatRequest(BaseModel):
    message: str
    session_id: str  # Уникальный ID диалога (чтобы не путать коллег)

# --- Эндпоинт 1: Красивый Интерфейс (HTML) ---
@app.get("/", response_class=HTMLResponse)
def get_chat_ui():
    # Это простая веб-страница, которая лежит прямо в коде
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FlyMyAI Agent Chat</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f0f2f5; }
            .chat-container { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); height: 70vh; overflow-y: scroll; display: flex; flex-direction: column; }
            .message { margin: 10px 0; padding: 10px 15px; border-radius: 15px; max-width: 80%; }
            .user { background: #007bff; color: white; align-self: flex-end; }
            .bot { background: #e4e6eb; color: black; align-self: flex-start; }
            .input-area { margin-top: 20px; display: flex; gap: 10px; }
            input { flex: 1; padding: 15px; border-radius: 25px; border: 1px solid #ccc; outline: none; }
            button { padding: 15px 25px; border-radius: 25px; border: none; background: #007bff; color: white; cursor: pointer; font-weight: bold; }
            button:disabled { background: #ccc; }
        </style>
    </head>
    <body>
        <h2>🤖 FlyMyAI Agent (With Memory)</h2>
        <div id="chat" class="chat-container"></div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Type a message..." onkeypress="handleEnter(event)">
            <button onclick="sendMessage()" id="sendBtn">Send</button>
        </div>

        <script>
            // Генерируем ID сессии, чтобы у каждого коллеги была своя память
            let sessionId = localStorage.getItem('chat_session_id');
            if (!sessionId) {
                sessionId = Math.random().toString(36).substring(7);
                localStorage.setItem('chat_session_id', sessionId);
            }

            const chatBox = document.getElementById('chat');

            function addMessage(text, sender) {
                const div = document.createElement('div');
                div.className = `message ${sender}`;
                div.textContent = text;
                chatBox.appendChild(div);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            async function sendMessage() {
                const input = document.getElementById('userInput');
                const btn = document.getElementById('sendBtn');
                const text = input.value.trim();
                
                if (!text) return;

                addMessage(text, 'user');
                input.value = '';
                input.disabled = true;
                btn.disabled = true;

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ message: text, session_id: sessionId })
                    });
                    const data = await response.json();
                    addMessage(data.response, 'bot');
                } catch (error) {
                    addMessage("Error connecting to server", 'bot');
                }
                
                input.disabled = false;
                btn.disabled = false;
                input.focus();
            }

            function handleEnter(e) {
                if (e.key === 'Enter') sendMessage();
            }
        </script>
    </body>
    </html>
    """

# --- Эндпоинт 2: Логика Чата с Памятью ---
@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="API Key missing")
    if not r:
        raise HTTPException(status_code=500, detail="Redis connection failed")

    session_key = f"chat_history:{request.session_id}"

    # 1. Загружаем историю из Redis
    # История хранится как список JSON-строк
    raw_history = r.lrange(session_key, 0, -1)
    history = []
    
    # Конвертируем формат Redis в формат Gemini
    for item in raw_history:
        msg = json.loads(item) # {"role": "user", "text": "..."}
        history.append({
            "role": msg["role"],
            "parts": [msg["text"]]
        })

    # 2. Инициализируем чат с историей
    model = genai.GenerativeModel('gemini-3-flash-preview')
    chat = model.start_chat(history=history)

    # 3. Получаем ответ от AI
    try:
        response = chat.send_message(request.message)
        ai_text = response.text
    except Exception as e:
        return {"response": f"Error from AI: {str(e)}"}

    # 4. Сохраняем НОВЫЕ сообщения в Redis (Память)
    # Сохраняем вопрос пользователя
    user_msg_json = json.dumps({"role": "user", "text": request.message})
    r.rpush(session_key, user_msg_json)
    
    # Сохраняем ответ модели
    model_msg_json = json.dumps({"role": "model", "text": ai_text})
    r.rpush(session_key, model_msg_json)

    # (Опционально) Ставим таймер удаления памяти через 24 часа (86400 сек)
    r.expire(session_key, 86400)

    return {"response": ai_text}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
