"""
Калькуляторы: ROI, сравнение с депозитом, рассрочка
"""

from datetime import datetime
from typing import Dict, List, Optional


def calc_roi(
    unit_price: int,
    commissioning_timestamp: Optional[int],
    is_completed: bool,
    rental_daily_rate: int = 0,
    occupancy_rate: float = 70,
    operating_expenses_pct: float = 10,
    management_fee_pct: float = 20,
    tax_rate: float = 4,
    appreciation_rate: float = 10,
    years: int = 5
) -> Dict:
    """
    Расчёт ROI с учётом срока сдачи.
    
    Если объект НЕ сдан:
    - До сдачи: только рост капитализации
    - После сдачи: + доход от аренды - расходы
    
    Если объект СДАН:
    - Сразу: рост капитализации + аренда - расходы
    """
    now = datetime.now().timestamp()
    
    # Если сдан или нет даты — считаем сдачу в прошлом
    if is_completed or commissioning_timestamp is None:
        commissioning = now - 1
    else:
        commissioning = float(commissioning_timestamp)
    
    results_by_year = []
    cumulative_rental = 0
    
    for year in range(1, years + 1):
        year_start = now + ((year - 1) * 365 * 24 * 3600)
        year_end = now + (year * 365 * 24 * 3600)
        
        # Рост капитализации (всегда)
        property_value = unit_price * ((1 + appreciation_rate / 100) ** year)
        appreciation = property_value - unit_price
        
        # Аренда (только после сдачи)
        year_rental = 0
        if rental_daily_rate > 0 and year_end > commissioning:
            # Сколько дней в этом году после сдачи
            if year_start < commissioning:
                # Частичный год — сдача в середине года
                days_after = (year_end - commissioning) / (24 * 3600)
            else:
                # Полный год после сдачи
                days_after = 365
            
            days_occupied = days_after * (occupancy_rate / 100)
            gross_income = rental_daily_rate * days_occupied
            
            # Расходы
            operating = gross_income * (operating_expenses_pct / 100)
            management = gross_income * (management_fee_pct / 100)
            tax = gross_income * (tax_rate / 100)
            
            year_rental = gross_income - operating - management - tax
            cumulative_rental += year_rental
        
        # Итого за год
        total_profit = appreciation + cumulative_rental
        roi_pct = (total_profit / unit_price) * 100
        annual_yield = roi_pct / year
        
        results_by_year.append({
            "year": year,
            "property_value": int(property_value),
            "appreciation": int(appreciation),
            "year_rental": int(year_rental),
            "cumulative_rental": int(cumulative_rental),
            "total_profit": int(total_profit),
            "roi_pct": round(roi_pct, 1),
            "annual_yield": round(annual_yield, 1),
        })
    
    # Окупаемость
    if cumulative_rental > 0 and years > 0:
        annual_net = cumulative_rental / years
        payback_years = unit_price / annual_net if annual_net > 0 else 999
    else:
        payback_years = 999
    
    return {
        "by_year": results_by_year,
        "payback_years": round(payback_years, 1),
        "final_roi": results_by_year[-1]["roi_pct"] if results_by_year else 0,
        "has_rental": rental_daily_rate > 0,
    }


def calc_compare_deposit(
    unit_price: int,
    roi_data: Dict,
    cb_rate: float,
    years: int = 5
) -> Dict:
    """
    Сравнение инвестиции в недвижимость с банковским депозитом.
    
    Депозит: сложный процент, капитализация ежемесячно.
    """
    # Депозит (сложный процент)
    monthly_rate = cb_rate / 100 / 12
    months = years * 12
    deposit_final = unit_price * ((1 + monthly_rate) ** months)
    deposit_profit = deposit_final - unit_price
    
    # Недвижимость (из ROI расчёта)
    property_profit = 0
    for year_data in roi_data["by_year"]:
        if year_data["year"] == years:
            property_profit = year_data["total_profit"]
            break
    
    # Разница
    difference = property_profit - deposit_profit
    
    return {
        "years": years,
        "cb_rate": cb_rate,
        "deposit_final": int(deposit_final),
        "deposit_profit": int(deposit_profit),
        "property_profit": int(property_profit),
        "difference": int(difference),
        "winner": "property" if difference > 0 else "deposit",
        "advantage_pct": round(abs(difference) / unit_price * 100, 1),
    }


def calc_installment(
    unit_price: int,
    pv_pct: float,
    months: int,
    markup_pct: float = 0
) -> Dict:
    """
    Расчёт рассрочки.
    
    pv_pct: первый взнос в %
    months: срок рассрочки в месяцах
    markup_pct: удорожание в %
    """
    pv = int(unit_price * (pv_pct / 100))
    remainder = unit_price - pv
    
    if markup_pct > 0:
        remainder_total = remainder * (1 + markup_pct / 100)
    else:
        remainder_total = remainder
    
    monthly = remainder_total / months if months > 0 else 0
    total = pv + remainder_total
    overpayment = total - unit_price
    
    return {
        "pv": pv,
        "pv_pct": pv_pct,
        "remainder": int(remainder),
        "monthly": int(monthly),
        "months": months,
        "total": int(total),
        "overpayment": int(overpayment),
        "overpayment_pct": round((overpayment / unit_price) * 100, 1) if unit_price else 0,
    }


# Ставка ЦБ — захардкодим, потом можно парсить
CB_RATE = 21.0  # Ключевая ставка ЦБ на январь 2026
