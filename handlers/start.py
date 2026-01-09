"""
Обработчик /start и списка ЖК
"""

from config.settings import (
    BTN_ADD_PROPERTY, BTN_SETTINGS, BTN_BACK_TO_LIST,
    States, format_price
)
from db.database import (
    get_or_create_user, get_user_properties,
    get_user_state, set_user_state, clear_user_state
)


def build_properties_keyboard(properties: list) -> dict:
    """Клавиатура со списком ЖК"""
    keyboard = []
    
    # Кнопки ЖК
    for prop in properties:
        keyboard.append([{
            "text": f"🏢 {prop['name']}",
            "callback_data": f"property:{prop['id']}"
        }])
    
    # Нижние кнопки
    keyboard.append([
        {"text": BTN_ADD_PROPERTY, "callback_data": "add_property"},
        {"text": BTN_SETTINGS, "callback_data": "settings"}
    ])
    
    return {"inline_keyboard": keyboard}


def format_properties_list(properties: list) -> str:
    """Форматирование списка ЖК"""
    if not properties:
        return (
            "🏠 <b>Realt Assistant</b>\n\n"
            "У тебя пока нет ЖК.\n"
            "Нажми «➕ Добавить ЖК» чтобы начать."
        )
    
    text = "🏠 <b>Realt Assistant</b>\n\nТвои ЖК:\n\n"
    
    for prop in properties:
        text += f"🏢 <b>{prop['name']}</b>\n"
        
        # Город и статистика
        parts = []
        if prop.get("city"):
            parts.append(f"📍 {prop['city']}")
        if prop.get("lots_count"):
            parts.append(f"{prop['lots_count']} лотов")
        if prop.get("min_price"):
            parts.append(f"от {format_price(prop['min_price'])}")
        
        if parts:
            text += "   " + " • ".join(parts) + "\n"
        text += "\n"
    
    return text.strip()


async def handle_start(send_message, user_id: int, username: str = "", first_name: str = ""):
    """Обработка команды /start"""
    # Регистрируем пользователя
    get_or_create_user(user_id, username, first_name)
    
    # Сбрасываем состояние
    clear_user_state(user_id)
    
    # Получаем ЖК пользователя
    properties = get_user_properties(user_id)
    
    # Устанавливаем состояние
    set_user_state(user_id, state=States.PROPERTIES_LIST)
    
    # Отправляем сообщение
    text = format_properties_list(properties)
    keyboard = build_properties_keyboard(properties)
    
    await send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_back_to_list(send_message, edit_message, user_id: int, message_id: int = None):
    """Возврат к списку ЖК"""
    clear_user_state(user_id)
    
    properties = get_user_properties(user_id)
    set_user_state(user_id, state=States.PROPERTIES_LIST)
    
    text = format_properties_list(properties)
    keyboard = build_properties_keyboard(properties)
    
    if message_id:
        await edit_message(
            chat_id=user_id,
            message_id=message_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
