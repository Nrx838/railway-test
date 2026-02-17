import os
import json
import redis
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import google.generativeai as genai

# --- Импорты MCP ---
from mcp.server.fastapi import FastsseServerTransport
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolRequestSchema
)

# --- Настройка Gemini и Redis ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

redis_url = os.getenv("REDIS_URL")
r = None
if redis_url:
    try:
        r = redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        print(f"Redis connection warning: {e}")

# --- Инициализация MCP Сервера ---
mcp_server = Server("flymyai-agent")

# --- Определение Инструментов (Tools) ---
# Мы говорим Cursor'у: "У меня есть инструмент, который умеет думать и помнить"

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="ask_flymyai_brain",
            description="Use this tool to ask questions to the FlyMyAI intelligent agent. It has memory and knows about context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or prompt from the user"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional unique ID for chat history. If not provided, 'default' is used."
                    }
                },
                "required": ["query"]
            }
        )
    ]

# --- Логика выполнения инструмента ---
@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    if name != "ask_flymyai_brain":
        raise ValueError(f"Unknown tool: {name}")

    query = arguments.get("query")
    session_id = arguments.get("session_id", "default_workspace")
    
    if not query:
        return [TextContent(type="text", text="Error: Query is empty")]

    # --- Твоя логика (Gemini + Redis) ---
    session_key = f"mcp_chat:{session_id}"
    
    # 1. Читаем историю
    history = []
    if r:
        raw_history = r.lrange(session_key, 0, -1)
        for item in raw_history:
            try:
                msg = json.loads(item)
                history.append({"role": msg["role"], "parts": [msg["text"]]})
            except: pass

    # 2. Спрашиваем Gemini
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        chat = model.start_chat(history=history)
        response = chat.send_message(query)
        ai_text = response.text
    except Exception as e:
        return [TextContent(type="text", text=f"Error connecting to Gemini: {str(e)}")]

    # 3. Сохраняем в память
    if r:
        r.rpush(session_key, json.dumps({"role": "user", "text": query}))
        r.rpush(session_key, json.dumps({"role": "model", "text": ai_text}))
        r.expire(session_key, 86400) # 24 часа

    return [TextContent(type="text", text=ai_text)]

# --- Настройка FastAPI для SSE (Transport) ---
# Это нужно, чтобы сервер работал по протоколу, который понимает Cursor

app = FastAPI()

# Создаем SSE транспорт
sse = FastsseServerTransport("/sse")

@app.get("/sse")
async def handle_sse(request: Request):
    """Cursor подключается сюда, чтобы слушать события"""
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_server.run(streams[0], streams[1], mcp_server.create_initialization_options())

@app.post("/messages")
async def handle_messages(request: Request):
    """Cursor отправляет сюда запросы (вызовы тулов)"""
    await sse.handle_post_message(request.scope, request.receive, request._send)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
