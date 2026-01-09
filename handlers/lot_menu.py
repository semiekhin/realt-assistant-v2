"""
Меню конкретного лота
"""

from config.settings import (
    BTN_KP, BTN_ROI, BTN_COMPARE, BTN_AI, BTN_BACK_TO_SEARCH,
    States, format_price, format_price_full, format_area, format_rooms, format_price_per_m2
)
from db.database import (
    get_property, get_unit_by_code, get_building, set_user_state
)


def build_lot_menu_keyboard(property_id: int, code: str) -> dict:
    return {
        "inline_keyboard": [
            [{"text": BTN_KP, "callback_data": f"kp:{property_id}:{code}"}],
            [{"text": BTN_ROI, "callback_data": f"roi:{property_id}:{code}"}],
            [{"text": BTN_COMPARE, "callback_data": f"compare:{property_id}:{code}"}],
            [{"text": BTN_AI, "callback_data": f"ai:{property_id}:{code}"}],
            [{"text": BTN_BACK_TO_SEARCH, "callback_data": f"search:{property_id}"}]
        ]
    }


def format_lot_menu(unit: dict, property_id: int) -> str:
    """Форматирование меню лота"""
    prop = get_property(property_id)
    
    text = f"🏢 <b>Лот {unit['code']}</b>\n"
    
    # ЖК и корпус
    parts = []
    if prop:
        parts.append(prop["name"])
    parts.append(f"Корпус {unit['building']}")
    parts.append(f"{unit['floor']} этаж")
    text += " • ".join(parts) + "\n\n"
    
    # Характеристики
    text += f"📐 {format_area(unit['area_m2'])} • {format_rooms(unit['rooms'])}\n"
    text += f"💰 {format_price_full(unit['price_rub'])}\n"
    text += f"📊 {format_price_per_m2(unit['price_per_m2'])}\n"
    
    # Отделка
    if unit.get("decoration_type"):
        text += f"🔧 {unit['decoration_type']}\n"
    
    # Срок сдачи (из building)
    if unit.get("building_id"):
        building = get_building(unit["building_id"])
        if building and building.get("commissioning_date"):
            status = "✅ Сдан" if building.get("is_completed") else f"🔑 Сдача: {building['commissioning_date']}"
            text += f"{status}\n"
    
    return text


async def handle_lot_menu(edit_message, user_id: int, property_id: int, code: str, message_id: int):
    """Показать меню лота"""
    unit = get_unit_by_code(property_id, code)
    
    if not unit:
        await edit_message(
            chat_id=user_id,
            message_id=message_id,
            text=f"❌ Лот {code} не найден",
            parse_mode="HTML"
        )
        return
    
    set_user_state(user_id, property_id=property_id, lot_code=code, state=States.LOT_MENU)
    
    text = format_lot_menu(unit, property_id)
    keyboard = build_lot_menu_keyboard(property_id, code)
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_lot_from_miniapp(send_message, user_id: int, property_id: int, code: str):
    """Обработка выбора лота из Mini App"""
    unit = get_unit_by_code(property_id, code)
    
    if not unit:
        await send_message(
            chat_id=user_id,
            text=f"❌ Лот {code} не найден",
            parse_mode="HTML"
        )
        return
    
    set_user_state(user_id, property_id=property_id, lot_code=code, state=States.LOT_MENU)
    
    text = format_lot_menu(unit, property_id)
    keyboard = build_lot_menu_keyboard(property_id, code)
    
    await send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
