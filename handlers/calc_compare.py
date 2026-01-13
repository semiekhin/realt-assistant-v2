"""
Сравнение с депозитом
"""

from config.settings import format_price, format_price_full
from db.database import (
    get_property, get_unit_by_code, get_building,
    get_property_custom
)
from services.calculations import calc_roi, calc_compare_deposit, CB_RATE


def format_compare_result(unit: dict, prop: dict, compare: dict, roi: dict) -> str:
    """Форматирование сравнения с депозитом"""
    
    text = f"💰 <b>Недвижимость vs Депозит</b>\n"
    text += f"Лот {unit['code']} • {prop['name']}\n\n"
    
    text += f"📊 Сумма инвестиции: {format_price_full(unit['price_rub'])}\n"
    text += f"📅 Период: {compare['years']} лет\n"
    text += f"🏦 Ставка ЦБ: {compare['cb_rate']}%\n\n"
    
    # Результаты
    text += "<b>🏠 Недвижимость:</b>\n"
    text += f"• Доход: +{format_price(compare['property_profit'])}\n"
    text += f"• ROI: {roi['final_roi']}%\n\n"
    
    text += "<b>🏦 Депозит:</b>\n"
    text += f"• Итого: {format_price(compare['deposit_final'])}\n"
    text += f"• Доход: +{format_price(compare['deposit_profit'])}\n\n"
    
    # Вывод
    diff = compare['difference']
    if compare['winner'] == 'property':
        text += f"✅ <b>Недвижимость выгоднее</b> на {format_price(abs(diff))}\n"
        text += f"Преимущество: +{compare['advantage_pct']}% от суммы инвестиции"
    else:
        text += f"🏦 <b>Депозит выгоднее</b> на {format_price(abs(diff))}\n"
        text += f"Но недвижимость — это актив, который можно использовать"
    
    return text


async def handle_compare(edit_message, user_id: int, property_id: int, code: str, message_id: int):
    """Показать сравнение с депозитом"""
    unit = get_unit_by_code(property_id, code)
    prop = get_property(property_id)
    custom = get_property_custom(property_id) or {}
    
    if not unit or not prop:
        await edit_message(
            chat_id=user_id,
            message_id=message_id,
            text="❌ Лот не найден",
            parse_mode="HTML"
        )
        return
    
    # Получаем данные корпуса
    building = None
    if unit.get("building_id"):
        building = get_building(unit["building_id"])
    
    is_completed = building.get("is_completed", False) if building else False
    commissioning_timestamp = building.get("commissioning_timestamp") if building else None
    
    # Сначала считаем ROI
    roi = calc_roi(
        unit_price=unit["price_rub"],
        commissioning_timestamp=commissioning_timestamp,
        is_completed=is_completed,
        rental_daily_rate=custom.get("rental_daily_rate") or 0,
        occupancy_rate=custom.get("occupancy_rate") or 70,
        operating_expenses_pct=custom.get("operating_expenses_pct") or 10,
        management_fee_pct=custom.get("management_fee_pct") or 20,
        tax_rate=custom.get("tax_rate") or 4,
        appreciation_rate=custom.get("appreciation_rate") or 10,
        years=5
    )
    
    # Сравнение с депозитом
    compare = calc_compare_deposit(
        unit_price=unit["price_rub"],
        roi_data=roi,
        cb_rate=CB_RATE,
        years=5
    )
    
    text = format_compare_result(unit, prop, compare, roi)
    
    keyboard = {"inline_keyboard": [
        [
            {"text": "3 года", "callback_data": f"compare_years:{property_id}:{code}:3"},
            {"text": "5 лет", "callback_data": f"compare_years:{property_id}:{code}:5"},
            {"text": "10 лет", "callback_data": f"compare_years:{property_id}:{code}:10"}
        ],
        [{"text": "📊 Подробный ROI", "callback_data": f"roi:{property_id}:{code}"}],
        [{"text": "🔙 Назад к лоту", "callback_data": f"lot:{property_id}:{code}"}]
    ]}
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_compare_years(edit_message, user_id: int, property_id: int, code: str, years: int, message_id: int):
    """Сравнение на разные сроки"""
    unit = get_unit_by_code(property_id, code)
    prop = get_property(property_id)
    custom = get_property_custom(property_id) or {}
    
    if not unit or not prop:
        return
    
    building = None
    if unit.get("building_id"):
        building = get_building(unit["building_id"])
    
    is_completed = building.get("is_completed", False) if building else False
    commissioning_timestamp = building.get("commissioning_timestamp") if building else None
    
    roi = calc_roi(
        unit_price=unit["price_rub"],
        commissioning_timestamp=commissioning_timestamp,
        is_completed=is_completed,
        rental_daily_rate=custom.get("rental_daily_rate") or 0,
        occupancy_rate=custom.get("occupancy_rate") or 70,
        operating_expenses_pct=custom.get("operating_expenses_pct") or 10,
        management_fee_pct=custom.get("management_fee_pct") or 20,
        tax_rate=custom.get("tax_rate") or 4,
        appreciation_rate=custom.get("appreciation_rate") or 10,
        years=years
    )
    
    compare = calc_compare_deposit(
        unit_price=unit["price_rub"],
        roi_data=roi,
        cb_rate=CB_RATE,
        years=years
    )
    
    text = format_compare_result(unit, prop, compare, roi)
    
    keyboard = {"inline_keyboard": [
        [
            {"text": "✓ 3 года" if years == 3 else "3 года", "callback_data": f"compare_years:{property_id}:{code}:3"},
            {"text": "✓ 5 лет" if years == 5 else "5 лет", "callback_data": f"compare_years:{property_id}:{code}:5"},
            {"text": "✓ 10 лет" if years == 10 else "10 лет", "callback_data": f"compare_years:{property_id}:{code}:10"}
        ],
        [{"text": "📊 Подробный ROI", "callback_data": f"roi:{property_id}:{code}"}],
        [{"text": "🔙 Назад к лоту", "callback_data": f"lot:{property_id}:{code}"}]
    ]}
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
