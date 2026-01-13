"""
Realt Assistant V2 — Main App
Telegram Bot для риэлторов
"""

import os
import json
import asyncio
from aiohttp import web, ClientSession
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "realt-v2-secret")

# Handlers
from handlers.start import handle_start, handle_back_to_list
from handlers.properties import handle_add_property, handle_search_property, handle_import_facility
from handlers.property_menu import handle_property_menu, handle_about_property
from handlers.search import (
    handle_search_menu, handle_search_by_building, handle_select_building, handle_select_floor,
    handle_search_area_start, handle_search_area,
    handle_search_budget_start, handle_search_budget,
    handle_search_code_start, handle_search_code
)
from handlers.lot_menu import handle_lot_menu, handle_lot_from_miniapp
from handlers.calc_roi import handle_roi
from handlers.calc_compare import handle_compare, handle_compare_years
from db.database import get_user_state
from config.settings import States


# === Telegram API ===

async def send_message(chat_id: int, text: str, parse_mode: str = None, reply_markup: dict = None):
    """Отправить сообщение"""
    async with ClientSession() as session:
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        async with session.post(f"{TELEGRAM_API}/sendMessage", json=payload) as resp:
            return await resp.json()


async def edit_message(chat_id: int, message_id: int, text: str, parse_mode: str = None, reply_markup: dict = None):
    """Редактировать сообщение"""
    async with ClientSession() as session:
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        async with session.post(f"{TELEGRAM_API}/editMessageText", json=payload) as resp:
            return await resp.json()


async def answer_callback(callback_id: str, text: str = None):
    """Ответить на callback"""
    async with ClientSession() as session:
        payload = {"callback_query_id": callback_id}
        if text:
            payload["text"] = text
        await session.post(f"{TELEGRAM_API}/answerCallbackQuery", json=payload)


# === Message Router ===

async def handle_message(message: dict):
    """Обработка текстовых сообщений"""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "")
    username = message["from"].get("username", "")
    first_name = message["from"].get("first_name", "")
    
    # Команда /start
    if text.startswith("/start"):
        # Проверяем параметры (от Mini App)
        parts = text.split()
        if len(parts) > 1:
            param = parts[1]
            # Формат: lot_PROPERTYID_CODE
            if param.startswith("lot_"):
                try:
                    _, property_id, code = param.split("_", 2)
                    await handle_lot_from_miniapp(send_message, user_id, int(property_id), code)
                    return
                except:
                    pass
        
        await handle_start(send_message, user_id, username, first_name)
        return
    
    # Обработка по состоянию
    state = get_user_state(user_id)
    current_state = state.get("state")
    
    if current_state == States.ADD_PROPERTY_SEARCH:
        await handle_search_property(send_message, user_id, text)
    
    elif current_state == States.SEARCH_BY_AREA:
        await handle_search_area(send_message, user_id, text)
    
    elif current_state == States.SEARCH_BY_BUDGET:
        await handle_search_budget(send_message, user_id, text)
    
    elif current_state == States.SEARCH_BY_CODE:
        await handle_search_code(send_message, user_id, text)
    
    else:
        # Неизвестное сообщение — показываем /start
        await handle_start(send_message, user_id, username, first_name)


# === Callback Router ===

async def handle_callback(callback: dict):
    """Обработка callback кнопок"""
    callback_id = callback["id"]
    user_id = callback["from"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback.get("data", "")
    
    await answer_callback(callback_id)
    
    # Роутинг по callback_data
    
    # Список ЖК
    if data == "back_to_list":
        await handle_back_to_list(send_message, edit_message, user_id, message_id)
    
    # Добавление ЖК
    elif data == "add_property":
        await handle_add_property(send_message, edit_message, user_id, message_id)
    
    elif data.startswith("import_facility:"):
        facility_id = data.split(":")[1]
        await handle_import_facility(send_message, edit_message, user_id, facility_id, message_id)
    
    # Меню ЖК
    elif data.startswith("property:"):
        property_id = int(data.split(":")[1])
        await handle_property_menu(edit_message, user_id, property_id, message_id)
    
    elif data.startswith("about:"):
        property_id = int(data.split(":")[1])
        await handle_about_property(edit_message, user_id, property_id, message_id)
    
    # Поиск
    elif data.startswith("search:"):
        property_id = int(data.split(":")[1])
        await handle_search_menu(edit_message, user_id, property_id, message_id)
    
    elif data.startswith("search_building:"):
        property_id = int(data.split(":")[1])
        await handle_search_by_building(edit_message, user_id, property_id, message_id)
    
    elif data.startswith("building:"):
        parts = data.split(":")
        property_id, building = int(parts[1]), int(parts[2])
        await handle_select_building(edit_message, user_id, property_id, building, message_id)
    
    elif data.startswith("floor:"):
        parts = data.split(":")
        property_id, building, floor = int(parts[1]), int(parts[2]), int(parts[3])
        await handle_select_floor(edit_message, user_id, property_id, building, floor, message_id)
    
    elif data.startswith("search_area:"):
        property_id = int(data.split(":")[1])
        await handle_search_area_start(edit_message, send_message, user_id, property_id, message_id)
    
    elif data.startswith("search_budget:"):
        property_id = int(data.split(":")[1])
        await handle_search_budget_start(edit_message, user_id, property_id, message_id)
    
    elif data.startswith("search_code:"):
        property_id = int(data.split(":")[1])
        await handle_search_code_start(edit_message, user_id, property_id, message_id)
    
    # Лот
    elif data.startswith("lot:"):
        parts = data.split(":")
        property_id, code = int(parts[1]), parts[2]
        await handle_lot_menu(edit_message, user_id, property_id, code, message_id)
    
    # TODO: KP, ROI, Compare, AI
    elif data.startswith("kp:"):
        await edit_message(user_id, message_id, "🚧 КП — в разработке", "HTML")
    
    elif data.startswith("roi:"):
        parts = data.split(":")
        property_id, code = int(parts[1]), parts[2]
        await handle_roi(edit_message, user_id, property_id, code, message_id)
    
    elif data.startswith("compare_years:"):
        parts = data.split(":")
        property_id, code, years = int(parts[1]), parts[2], int(parts[3])
        await handle_compare_years(edit_message, user_id, property_id, code, years, message_id)
    
    elif data.startswith("compare:"):
        parts = data.split(":")
        property_id, code = int(parts[1]), parts[2]
        await handle_compare(edit_message, user_id, property_id, code, message_id)
    
    elif data.startswith("ai:"):
        await edit_message(user_id, message_id, "🚧 AI — в разработке", "HTML")
    
    elif data == "settings":
        await edit_message(user_id, message_id, "🚧 Настройки — в разработке", "HTML")


# === Webhook Handler ===

async def webhook_handler(request: web.Request) -> web.Response:
    """Обработчик webhook от Telegram"""
    # Проверка secret
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret != WEBHOOK_SECRET:
        return web.Response(status=403)
    
    try:
        data = await request.json()
        
        if "message" in data:
            await handle_message(data["message"])
        elif "callback_query" in data:
            await handle_callback(data["callback_query"])
        
        return web.Response(text="ok")
    
    except Exception as e:
        print(f"[ERROR] {e}")
        return web.Response(text="error", status=500)


async def health_handler(request: web.Request) -> web.Response:
    """Health check"""
    return web.Response(text="OK")


# === App ===

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/webhook", webhook_handler)
    app.router.add_get("/health", health_handler)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8080)
