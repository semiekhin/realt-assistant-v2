"""
Меню конкретного ЖК
"""

from config.settings import (
    BTN_SELECT_LOT, BTN_SEARCH, BTN_ABOUT, BTN_BACK_TO_LIST,
    MINIAPP_URL, States, format_price
)
from db.database import get_property, set_user_state, get_building_stats


def build_property_menu_keyboard(property_id: int) -> dict:
    """Клавиатура меню ЖК"""
    return {
        "inline_keyboard": [
            [{"text": BTN_SELECT_LOT, "web_app": {"url": f"{MINIAPP_URL}?property_id={property_id}"}}],
            [{"text": BTN_SEARCH, "callback_data": f"search:{property_id}"}],
            [{"text": BTN_ABOUT, "callback_data": f"about:{property_id}"}],
            [{"text": BTN_BACK_TO_LIST, "callback_data": "back_to_list"}]
        ]
    }


def format_property_menu(prop: dict) -> str:
    """Форматирование меню ЖК"""
    text = f"🏢 <b>{prop['name']}</b>\n"
    
    # Локация
    location_parts = []
    if prop.get("city"):
        location_parts.append(prop["city"])
    if prop.get("district"):
        location_parts.append(prop["district"])
    if location_parts:
        text += f"📍 {', '.join(location_parts)}\n"
    
    # Застройщик
    if prop.get("developer"):
        text += f"🏗 Застройщик: {prop['developer']}\n"
    
    # Статистика
    stats_parts = []
    if prop.get("lots_count"):
        stats_parts.append(f"{prop['lots_count']} лотов")
    if prop.get("min_price"):
        stats_parts.append(f"от {format_price(prop['min_price'])}")
    if stats_parts:
        text += f"📊 {' • '.join(stats_parts)}\n"
    
    return text


async def handle_property_menu(edit_message, user_id: int, property_id: int, message_id: int):
    """Показать меню ЖК"""
    prop = get_property(property_id)
    
    if not prop:
        await edit_message(
            chat_id=user_id,
            message_id=message_id,
            text="❌ ЖК не найден",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем текущий ЖК
    set_user_state(user_id, property_id=property_id, state=States.PROPERTY_MENU)
    
    text = format_property_menu(prop)
    keyboard = build_property_menu_keyboard(property_id)
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_about_property(edit_message, user_id: int, property_id: int, message_id: int):
    """Информация о ЖК"""
    prop = get_property(property_id)
    
    if not prop:
        return
    
    text = f"ℹ️ <b>О проекте: {prop['name']}</b>\n\n"
    
    # Локация
    if prop.get("city") or prop.get("district") or prop.get("address"):
        text += "<b>📍 Локация:</b>\n"
        if prop.get("city"):
            text += f"Город: {prop['city']}\n"
        if prop.get("district"):
            text += f"Район: {prop['district']}\n"
        if prop.get("address"):
            text += f"Адрес: {prop['address']}\n"
        text += "\n"
    
    # Застройщик
    if prop.get("developer"):
        text += f"<b>🏗 Застройщик:</b> {prop['developer']}\n\n"
    
    # Описание
    if prop.get("description"):
        desc = prop["description"][:500]
        if len(prop["description"]) > 500:
            desc += "..."
        text += f"<b>📝 Описание:</b>\n{desc}\n\n"
    
    # Статистика по корпусам
    stats = get_building_stats(property_id)
    if stats:
        text += "<b>🏢 Корпуса:</b>\n"
        for s in stats:
            text += f"• Корпус {s['building']}: {s['count']} лотов, "
            text += f"этажи {s['min_floor']}-{s['max_floor']}, "
            text += f"{format_price(s['min_price'])} - {format_price(s['max_price'])}\n"
    
    keyboard = {"inline_keyboard": [[
        {"text": "🔙 Назад", "callback_data": f"property:{property_id}"}
    ]]}
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
