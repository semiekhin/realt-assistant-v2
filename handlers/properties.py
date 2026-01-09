"""
Обработчик добавления/удаления ЖК
"""

from config.settings import States, BTN_BACK, format_price
from db.database import set_user_state, get_user_state, get_user_properties
from services.ygroup import search_facilities, import_facility


def build_search_results_keyboard(facilities: list) -> dict:
    """Клавиатура с результатами поиска"""
    keyboard = []
    
    for f in facilities[:10]:
        city = f.get("city_name", "")
        lots = f.get("active_lots_amount", 0)
        label = f"{f['name']}"
        if city:
            label += f" • {city}"
        if lots:
            label += f" • {lots} лотов"
        
        keyboard.append([{
            "text": label[:60],
            "callback_data": f"import_facility:{f['id']}"
        }])
    
    keyboard.append([{"text": BTN_BACK, "callback_data": "back_to_list"}])
    
    return {"inline_keyboard": keyboard}


async def handle_add_property(send_message, edit_message, user_id: int, message_id: int = None):
    """Начало добавления ЖК — запрос поиска"""
    set_user_state(user_id, state=States.ADD_PROPERTY_SEARCH)
    
    text = (
        "🔍 <b>Добавление ЖК</b>\n\n"
        "Введи название ЖК для поиска в YGroup.\n\n"
        "Например: <i>Солнечный</i>, <i>RIZALTA</i>, <i>Парковый</i>"
    )
    
    keyboard = {"inline_keyboard": [[
        {"text": BTN_BACK, "callback_data": "back_to_list"}
    ]]}
    
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


async def handle_search_property(send_message, user_id: int, query: str):
    """Поиск ЖК по названию"""
    # Ищем в YGroup
    facilities = search_facilities(query)
    
    if not facilities:
        text = (
            f"🔍 По запросу «{query}» ничего не найдено.\n\n"
            "Попробуй другое название."
        )
        keyboard = {"inline_keyboard": [[
            {"text": BTN_BACK, "callback_data": "back_to_list"}
        ]]}
    else:
        text = f"🔍 Найдено {len(facilities)} ЖК по запросу «{query}»:\n\nВыбери для добавления:"
        keyboard = build_search_results_keyboard(facilities)
        set_user_state(user_id, state=States.ADD_PROPERTY_SELECT)
    
    await send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_import_facility(send_message, edit_message, user_id: int, facility_id: int, message_id: int):
    """Импорт выбранного ЖК"""
    # Показываем статус загрузки
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text="⏳ Загружаю данные ЖК из YGroup...\n\nЭто может занять несколько секунд.",
        parse_mode="HTML"
    )
    
    # Импортируем
    result = import_facility(user_id, facility_id)
    
    if result["success"]:
        text = (
            f"✅ <b>ЖК добавлен!</b>\n\n"
            f"🏢 Корпусов: {result['buildings_count']}\n"
            f"🏠 Лотов: {result['units_count']}\n\n"
            f"Теперь ты можешь работать с этим ЖК."
        )
    else:
        text = f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}"
    
    keyboard = {"inline_keyboard": [[
        {"text": "🔙 К списку ЖК", "callback_data": "back_to_list"}
    ]]}
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
