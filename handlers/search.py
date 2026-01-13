"""
Ручной поиск лотов: по корпусу, площади, бюджету, номеру
"""

from config.settings import (
    BTN_BY_BUILDING, BTN_BY_AREA, BTN_BY_BUDGET, BTN_BY_CODE, BTN_BACK,
    States, format_price, format_area, format_rooms
)
from db.database import (
    get_property, get_user_state, set_user_state,
    get_building_stats, get_available_floors, get_property_units,
    get_units_by_budget, get_units_by_area, get_unit_by_code
)


def build_search_menu_keyboard(property_id: int) -> dict:
    return {
        "inline_keyboard": [
            [{"text": BTN_BY_BUILDING, "callback_data": f"search_building:{property_id}"}],
            [{"text": BTN_BY_AREA, "callback_data": f"search_area:{property_id}"}],
            [{"text": BTN_BY_BUDGET, "callback_data": f"search_budget:{property_id}"}],
            [{"text": BTN_BY_CODE, "callback_data": f"search_code:{property_id}"}],
            [{"text": BTN_BACK, "callback_data": f"property:{property_id}"}]
        ]
    }


def build_buildings_keyboard(property_id: int, stats: list) -> dict:
    keyboard = []
    for s in stats:
        label = f"Корпус {s['building']} • {s['count']} лотов • от {format_price(s['min_price'])}"
        keyboard.append([{
            "text": label,
            "callback_data": f"building:{property_id}:{s['building']}"
        }])
    keyboard.append([{"text": BTN_BACK, "callback_data": f"search:{property_id}"}])
    return {"inline_keyboard": keyboard}


def build_floors_keyboard(property_id: int, building: int, floors: list) -> dict:
    keyboard = []
    # Группируем по 3 этажа в ряд
    row = []
    for f in floors:
        label = f"{f['floor']} эт ({f['count']})"
        row.append({
            "text": label,
            "callback_data": f"floor:{property_id}:{building}:{f['floor']}"
        })
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([{"text": BTN_BACK, "callback_data": f"search_building:{property_id}"}])
    return {"inline_keyboard": keyboard}


def build_units_keyboard(property_id: int, units: list, back_callback: str) -> dict:
    keyboard = []
    for u in units:
        status_icon = ""
        if u.get("status") == "booked":
            status_icon = "🔒 "
        elif u.get("status") == "sold":
            status_icon = "❌ "
        label = f"{status_icon}{u['code']} • {format_rooms(u['rooms'])} • {format_area(u['area_m2'])} • {format_price(u['price_rub'])}"
        keyboard.append([{
            "text": label,
            "callback_data": f"lot:{property_id}:{u['code']}"
        }])
    keyboard.append([{"text": BTN_BACK, "callback_data": back_callback}])
    return {"inline_keyboard": keyboard}


# === Handlers ===

async def handle_search_menu(edit_message, user_id: int, property_id: int, message_id: int):
    """Меню поиска"""
    prop = get_property(property_id)
    if not prop:
        return
    
    set_user_state(user_id, property_id=property_id, state=States.SEARCH_MENU)
    
    text = f"🔍 <b>Поиск — {prop['name']}</b>\n\nВыбери способ поиска:"
    keyboard = build_search_menu_keyboard(property_id)
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_search_by_building(edit_message, user_id: int, property_id: int, message_id: int):
    """Выбор корпуса"""
    prop = get_property(property_id)
    stats = get_building_stats(property_id)
    
    if not stats:
        await edit_message(
            chat_id=user_id,
            message_id=message_id,
            text="❌ В этом ЖК нет лотов",
            parse_mode="HTML"
        )
        return
    
    set_user_state(user_id, property_id=property_id, state=States.SEARCH_BY_BUILDING)
    
    text = f"🏢 <b>{prop['name']}</b>\n\nВыбери корпус:"
    keyboard = build_buildings_keyboard(property_id, stats)
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_select_building(edit_message, user_id: int, property_id: int, building: int, message_id: int):
    """Выбор этажа в корпусе"""
    prop = get_property(property_id)
    floors = get_available_floors(property_id, building)
    
    if not floors:
        await edit_message(
            chat_id=user_id,
            message_id=message_id,
            text="❌ В этом корпусе нет лотов",
            parse_mode="HTML"
        )
        return
    
    set_user_state(user_id, property_id=property_id, state=States.SEARCH_BY_FLOOR)
    
    text = f"🏢 <b>{prop['name']} • Корпус {building}</b>\n\nВыбери этаж:"
    keyboard = build_floors_keyboard(property_id, building, floors)
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_select_floor(edit_message, user_id: int, property_id: int, building: int, floor: int, message_id: int):
    """Список лотов на этаже"""
    prop = get_property(property_id)
    units = get_property_units(property_id, building=building, floor=floor)
    
    if not units:
        await edit_message(
            chat_id=user_id,
            message_id=message_id,
            text="❌ На этом этаже нет лотов",
            parse_mode="HTML"
        )
        return
    
    text = f"🏢 <b>{prop['name']}</b>\nКорпус {building} • {floor} этаж\n\nЛоты ({len(units)}):"
    keyboard = build_units_keyboard(property_id, units, f"building:{property_id}:{building}")
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_search_area_start(edit_message, send_message, user_id: int, property_id: int, message_id: int):
    """Начало поиска по площади"""
    set_user_state(user_id, property_id=property_id, state=States.SEARCH_BY_AREA)
    
    text = (
        "📐 <b>Поиск по площади</b>\n\n"
        "Введи диапазон площади в формате:\n"
        "<code>30-50</code> или <code>40 60</code>\n\n"
        "Или одно число для поиска ±5 м²"
    )
    keyboard = {"inline_keyboard": [[
        {"text": BTN_BACK, "callback_data": f"search:{property_id}"}
    ]]}
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_search_area(send_message, user_id: int, text: str):
    """Поиск по площади"""
    state = get_user_state(user_id)
    property_id = state.get("current_property_id")
    
    if not property_id:
        return
    
    # Парсим диапазон
    import re
    numbers = re.findall(r'\d+', text)
    
    if len(numbers) == 1:
        center = float(numbers[0])
        min_area, max_area = center - 5, center + 5
    elif len(numbers) >= 2:
        min_area, max_area = float(numbers[0]), float(numbers[1])
    else:
        await send_message(
            chat_id=user_id,
            text="❌ Не удалось распознать диапазон. Попробуй: 30-50",
            parse_mode="HTML"
        )
        return
    
    units = get_units_by_area(property_id, min_area, max_area)
    prop = get_property(property_id)
    
    if not units:
        text = f"❌ Не найдено лотов с площадью {min_area}-{max_area} м²"
        keyboard = {"inline_keyboard": [[
            {"text": BTN_BACK, "callback_data": f"search:{property_id}"}
        ]]}
    else:
        text = f"📐 <b>{prop['name']}</b>\nПлощадь {min_area}-{max_area} м²\n\nНайдено {len(units)} лотов:"
        keyboard = build_units_keyboard(property_id, units[:15], f"search:{property_id}")
    
    await send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_search_budget_start(edit_message, user_id: int, property_id: int, message_id: int):
    """Начало поиска по бюджету"""
    set_user_state(user_id, property_id=property_id, state=States.SEARCH_BY_BUDGET)
    
    text = (
        "💰 <b>Поиск по бюджету</b>\n\n"
        "Введи диапазон бюджета в млн ₽:\n"
        "<code>10-15</code> или <code>10 15</code>\n\n"
        "Или одно число для максимального бюджета"
    )
    keyboard = {"inline_keyboard": [[
        {"text": BTN_BACK, "callback_data": f"search:{property_id}"}
    ]]}
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_search_budget(send_message, user_id: int, text: str):
    """Поиск по бюджету"""
    state = get_user_state(user_id)
    property_id = state.get("current_property_id")
    
    if not property_id:
        return
    
    # Парсим диапазон
    import re
    numbers = re.findall(r'[\d.]+', text)
    
    if len(numbers) == 1:
        min_price = 0
        max_price = int(float(numbers[0]) * 1_000_000)
    elif len(numbers) >= 2:
        min_price = int(float(numbers[0]) * 1_000_000)
        max_price = int(float(numbers[1]) * 1_000_000)
    else:
        await send_message(
            chat_id=user_id,
            text="❌ Не удалось распознать бюджет. Попробуй: 10-15",
            parse_mode="HTML"
        )
        return
    
    units = get_units_by_budget(property_id, min_price, max_price)
    prop = get_property(property_id)
    
    if not units:
        text = f"❌ Не найдено лотов в бюджете {format_price(min_price)} - {format_price(max_price)}"
        keyboard = {"inline_keyboard": [[
            {"text": BTN_BACK, "callback_data": f"search:{property_id}"}
        ]]}
    else:
        text = f"💰 <b>{prop['name']}</b>\nБюджет {format_price(min_price)} - {format_price(max_price)}\n\nНайдено {len(units)} лотов:"
        keyboard = build_units_keyboard(property_id, units[:15], f"search:{property_id}")
    
    await send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_search_code_start(edit_message, user_id: int, property_id: int, message_id: int):
    """Начало поиска по номеру лота"""
    set_user_state(user_id, property_id=property_id, state=States.SEARCH_BY_CODE)
    
    text = (
        "🔍 <b>Поиск по номеру</b>\n\n"
        "Введи номер лота:\n"
        "<code>А101</code> или <code>В205</code>"
    )
    keyboard = {"inline_keyboard": [[
        {"text": BTN_BACK, "callback_data": f"search:{property_id}"}
    ]]}
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_search_code(send_message, user_id: int, code: str):
    """Поиск по номеру лота"""
    state = get_user_state(user_id)
    property_id = state.get("current_property_id")
    
    if not property_id:
        return
    
    code = code.strip().upper()
    unit = get_unit_by_code(property_id, code)
    
    if not unit:
        # Пробуем найти похожие
        all_units = get_property_units(property_id)
        similar = [u for u in all_units if code in u["code"].upper()][:5]
        
        if similar:
            text = f"❌ Лот «{code}» не найден. Похожие:"
            keyboard = build_units_keyboard(property_id, similar, f"search:{property_id}")
        else:
            text = f"❌ Лот «{code}» не найден"
            keyboard = {"inline_keyboard": [[
                {"text": BTN_BACK, "callback_data": f"search:{property_id}"}
            ]]}
    else:
        # Найден — показываем меню лота
        from handlers.lot_menu import format_lot_menu, build_lot_menu_keyboard
        text = format_lot_menu(unit, property_id)
        keyboard = build_lot_menu_keyboard(property_id, unit["code"])
        set_user_state(user_id, property_id=property_id, lot_code=unit["code"], state=States.LOT_MENU)
    
    await send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
