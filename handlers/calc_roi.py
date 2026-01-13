"""
ROI калькулятор
"""

from config.settings import format_price, format_price_full
from db.database import (
    get_property, get_unit_by_code, get_building,
    get_property_custom
)
from services.calculations import calc_roi, calc_compare_deposit, CB_RATE


def format_roi_result(unit: dict, prop: dict, building: dict, custom: dict, roi: dict) -> str:
    """Форматирование результата ROI"""
    
    text = f"📊 <b>Расчёт доходности</b>\n"
    text += f"Лот {unit['code']} • {prop['name']}\n\n"
    
    text += f"💰 Стоимость: {format_price_full(unit['price_rub'])}\n"
    
    # Срок сдачи
    if building:
        if building.get("is_completed"):
            text += "🔑 Статус: Сдан ✅\n"
        elif building.get("commissioning_date"):
            text += f"🔑 Сдача: {building['commissioning_date']}\n"
    
    text += "\n"
    
    # Параметры расчёта
    text += "<b>⚙️ Параметры:</b>\n"
    text += f"• Рост цены: {custom.get('appreciation_rate', 10)}% в год\n"
    
    if roi["has_rental"]:
        text += f"• Аренда: {format_price(custom.get('rental_daily_rate', 0))}/сутки\n"
        text += f"• Загрузка: {custom.get('occupancy_rate', 70)}%\n"
        text += f"• Расходы: {custom.get('operating_expenses_pct', 10)}% + УК {custom.get('management_fee_pct', 20)}%\n"
        text += f"• Налог: {custom.get('tax_rate', 4)}%\n"
    else:
        text += "• Аренда: не задана\n"
    
    text += "\n<b>📈 Прогноз по годам:</b>\n"
    
    for year_data in roi["by_year"]:
        y = year_data["year"]
        profit = format_price(year_data["total_profit"])
        roi_pct = year_data["roi_pct"]
        annual = year_data["annual_yield"]
        
        text += f"<b>{y} год:</b> +{profit} ({roi_pct}%, ~{annual}%/год)\n"
    
    if roi["has_rental"] and roi["payback_years"] < 100:
        text += f"\n⏱ Окупаемость: {roi['payback_years']} лет\n"
    
    return text


async def handle_roi(edit_message, user_id: int, property_id: int, code: str, message_id: int):
    """Показать ROI расчёт"""
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
    
    # Параметры для расчёта
    is_completed = building.get("is_completed", False) if building else False
    commissioning_timestamp = building.get("commissioning_timestamp") if building else None
    
    # Расчёт ROI
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
    
    text = format_roi_result(unit, prop, building, custom, roi)
    
    keyboard = {"inline_keyboard": [
        [{"text": "💰 Сравнить с депозитом", "callback_data": f"compare:{property_id}:{code}"}],
        [{"text": "⚙️ Настроить параметры", "callback_data": f"roi_settings:{property_id}:{code}"}],
        [{"text": "🔙 Назад к лоту", "callback_data": f"lot:{property_id}:{code}"}]
    ]}
    
    await edit_message(
        chat_id=user_id,
        message_id=message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
