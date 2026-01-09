"""
Настройки Realt Assistant V2
"""

import os
from dotenv import load_dotenv

load_dotenv()

# === Telegram ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "realt-v2-secret")

# === OpenAI ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# === YGroup ===
YGROUP_API_TOKEN = os.getenv("YGROUP_API_TOKEN", "")

# === Mini App ===
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://realt-miniapp.vercel.app")

# === Меню: Список ЖК ===
BTN_ADD_PROPERTY = "➕ Добавить ЖК"
BTN_SETTINGS = "⚙️ Настройки"

# === Меню: Внутри ЖК ===
BTN_SELECT_LOT = "🏠 Выбор лота"
BTN_SEARCH = "🔍 Поиск вручную"
BTN_ABOUT = "ℹ️ О проекте"
BTN_BACK_TO_LIST = "🔙 К списку ЖК"

# === Меню: Поиск ===
BTN_BY_BUILDING = "🏢 По корпусу"
BTN_BY_AREA = "📐 По площади"
BTN_BY_BUDGET = "💰 По бюджету"
BTN_BY_CODE = "🔍 По номеру лота"
BTN_BACK = "🔙 Назад"

# === Меню: Лот ===
BTN_KP = "📄 Коммерческое предложение"
BTN_ROI = "📊 Расчёт доходности"
BTN_COMPARE = "💰 Сравнить с депозитом"
BTN_AI = "🤖 AI-помощник"
BTN_BACK_TO_SEARCH = "🔙 К поиску"

# === Меню: AI-сервисы ===
BTN_AI_ARGUMENTS = "🎯 Генератор аргументов"
BTN_AI_OBJECTIONS = "❓ Работа с возражениями"
BTN_AI_DIALOGUE = "💬 Помощник в диалоге"
BTN_AI_REPORT = "📈 Инвестиционный отчёт"
BTN_AI_SCENARIOS = "🎲 Сценарии 'Что если'"
BTN_AI_COMPETITORS = "⚖️ Сравнить с конкурентами"
BTN_BACK_TO_LOT = "🔙 Назад к лоту"

# === Состояния FSM ===
class States:
    # Список ЖК
    PROPERTIES_LIST = "properties_list"
    
    # Добавление ЖК
    ADD_PROPERTY_SEARCH = "add_property_search"
    ADD_PROPERTY_SELECT = "add_property_select"
    
    # Внутри ЖК
    PROPERTY_MENU = "property_menu"
    
    # Поиск
    SEARCH_MENU = "search_menu"
    SEARCH_BY_BUILDING = "search_by_building"
    SEARCH_BY_FLOOR = "search_by_floor"
    SEARCH_BY_AREA = "search_by_area"
    SEARCH_BY_BUDGET = "search_by_budget"
    SEARCH_BY_CODE = "search_by_code"
    
    # Лот
    LOT_MENU = "lot_menu"
    
    # AI
    AI_MENU = "ai_menu"
    AI_DIALOGUE = "ai_dialogue"
    
    # Настройки ЖК
    PROPERTY_SETTINGS = "property_settings"


# === Форматирование ===

def format_price(price: int) -> str:
    """15200000 → '15.2 млн ₽'"""
    if not price:
        return "—"
    if price >= 1_000_000:
        return f"{price / 1_000_000:.1f} млн ₽".replace(".0 ", " ")
    return f"{price:,} ₽".replace(",", " ")


def format_price_full(price: int) -> str:
    """15200000 → '15 200 000 ₽'"""
    if not price:
        return "—"
    return f"{price:,} ₽".replace(",", " ")


def format_area(area: float) -> str:
    """45.5 → '45.5 м²'"""
    if not area:
        return "—"
    return f"{area:.1f} м²".replace(".0 ", " ")


def format_rooms(rooms: int) -> str:
    """0 → 'Студия', 1 → '1-комн', 2 → '2-комн'"""
    if rooms == 0:
        return "Студия"
    return f"{rooms}-комн"


def format_price_per_m2(price_per_m2: int) -> str:
    """350000 → '350 тыс ₽/м²'"""
    if not price_per_m2:
        return "—"
    return f"{price_per_m2 // 1000} тыс ₽/м²"
