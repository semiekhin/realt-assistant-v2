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
    text += "<b>📍 Локация:</b>\n"
    if prop.get("address"):
        text += f"{prop['address']}\n"
    else:
        parts = []
        if prop.get("city"):
            parts.append(prop["city"])
        if prop.get("district"):
            parts.append(prop["district"])
        if parts:
            text += f"{', '.join(parts)}\n"
    text += "\n"
    
    # Характеристики
    chars = []
    if prop.get("facility_subtype"):
        chars.append(f"Тип: {prop['facility_subtype']}")
    if prop.get("facility_class"):
        chars.append(f"Класс: {prop['facility_class']}")
    if prop.get("territory_type"):
        chars.append(f"Территория: {prop['territory_type']}")
    if prop.get("parking_types"):
        chars.append(f"Парковка: {prop['parking_types']}")
    
    if chars:
        text += "<b>🏠 Характеристики:</b>\n"
        for c in chars:
            text += f"• {c}\n"
        text += "\n"
    
    # Сдача
    if prop.get("is_commissioned"):
        text += "<b>🔑 Статус:</b> Сдан ✅\n\n"
    elif prop.get("commissioning_year"):
        q = prop.get("commissioning_quarter", "")
        year = prop["commissioning_year"]
        text += f"<b>🔑 Сдача:</b> Q{q} {year}\n\n"
    
    # Коммуникации
    comms = []
    if prop.get("has_gas"):
        comms.append("Газ ✅")
    if prop.get("has_electricity"):
        comms.append("Электричество ✅")
    if prop.get("heating_type"):
        comms.append(f"Отопление: {prop['heating_type']}")
    if prop.get("water_supply_type"):
        comms.append(f"Вода: {prop['water_supply_type']}")
    if prop.get("sewerage_type"):
        comms.append(f"Канализация: {prop['sewerage_type']}")
    
    if comms:
        text += "<b>🔌 Коммуникации:</b>\n"
        for c in comms:
            text += f"• {c}\n"
        text += "\n"
    
    # Оформление и оплата
    payment_info = []
    if prop.get("contract_type"):
        payment_info.append(f"Оформление: {prop['contract_type']}")
    if prop.get("payment_methods"):
        payment_info.append(f"Оплата: {prop['payment_methods']}")
    if prop.get("commission_percent"):
        pct = prop["commission_percent"] * 100
        payment_info.append(f"Комиссия: {pct:.0f}%")
    if prop.get("fz214"):
        payment_info.append("ФЗ-214 ✅")
    
    if payment_info:
        text += "<b>💳 Оформление:</b>\n"
        for p in payment_info:
            text += f"• {p}\n"
        text += "\n"
    
    # Площади и цены
    price_info = []
    area_parts = []
    if prop.get("min_area_m2"):
        area_parts.append(f"{prop['min_area_m2']:.1f}")
    if prop.get("max_area_m2"):
        area_parts.append(f"{prop['max_area_m2']:.1f}")
    if area_parts:
        price_info.append(f"Площади: {' - '.join(area_parts)} м²")
    
    if prop.get("min_price_per_m2"):
        price_info.append(f"Цена за м²: от {format_price(prop['min_price_per_m2'])}")
    if prop.get("min_price"):
        price_info.append(f"Мин. цена: от {format_price(prop['min_price'])}")
    
    if price_info:
        text += "<b>💰 Цены:</b>\n"
        for p in price_info:
            text += f"• {p}\n"
        text += "\n"
    
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
