"""
YGroup API Client
https://api-ru.ygroup.ru/v2/
"""

import os
import re
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api-ru.ygroup.ru/v2"
API_BASE_V1 = "https://api-ru.ygroup.ru/v1"
API_TOKEN = os.getenv("YGROUP_API_TOKEN", "")

# Кэш всех ЖК
_facilities_cache: List[Dict] = []
_cache_loaded = False


def get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }


def _load_all_facilities() -> List[Dict]:
    """Загрузить все ЖК (с пагинацией)"""
    global _facilities_cache, _cache_loaded
    
    if _cache_loaded:
        return _facilities_cache
    
    all_posts = []
    page = 1
    
    while True:
        try:
            resp = requests.get(
                f"{API_BASE}/facilities",
                headers=get_headers(),
                params={"types": 6, "per_page": 100, "page": page},
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            posts = data.get("data", {}).get("facility_posts", [])
            
            if not posts:
                break
            
            all_posts.extend(posts)
            
            meta = data.get("data", {}).get("meta", {})
            total = meta.get("total", 0)
            
            if len(all_posts) >= total:
                break
            
            page += 1
            
        except Exception as e:
            print(f"[YGROUP] _load_all_facilities page {page} error: {e}")
            break
    
    _facilities_cache = all_posts
    _cache_loaded = True
    print(f"[YGROUP] Loaded {len(all_posts)} facilities")
    
    return all_posts


def search_facilities(query: str) -> List[Dict]:
    """Поиск ЖК по названию"""
    all_facilities = _load_all_facilities()
    
    if not query:
        return all_facilities[:20]
    
    query_lower = query.lower()
    results = [
        f for f in all_facilities 
        if query_lower in f.get("name", "").lower()
    ]
    
    return results[:20]


def get_facility(facility_id: str) -> Optional[Dict]:
    """Получить ЖК из кэша по ID"""
    all_facilities = _load_all_facilities()
    for f in all_facilities:
        if f.get("id") == facility_id:
            return f
    return None


def get_clusters(facility_id: str) -> List[Dict]:
    """Получить корпуса ЖК"""
    try:
        resp = requests.get(
            f"{API_BASE_V1}/clusters",
            headers=get_headers(),
            params={"facility_id": facility_id},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("clusters", [])
    except Exception as e:
        print(f"[YGROUP] get_clusters error: {e}")
        return []


def get_lots(cluster_id: str) -> List[Dict]:
    """Получить лоты корпуса"""
    try:
        resp = requests.get(
            f"{API_BASE_V1}/lots",
            headers=get_headers(),
            params={"cluster_id": cluster_id},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("lots", [])
    except Exception as e:
        print(f"[YGROUP] get_lots error: {e}")
        return []


# === Data Transformation ===

def extract_building_number(name: str) -> int:
    if not name:
        return 1
    match = re.search(r'\d+', name)
    if match:
        return int(match.group())
    name_lower = name.lower()
    if "family" in name_lower:
        return 1
    if "business" in name_lower:
        return 2
    return 1


def quarter_to_timestamp(quarter: int, year: int) -> int:
    month = {1: 3, 2: 6, 3: 9, 4: 12}.get(quarter, 12)
    dt = datetime(year, month, 1)
    return int(dt.timestamp())


def generate_lot_code(lot: Dict, building_number: int) -> str:
    building_letters = {1: "А", 2: "В", 3: "С", 4: "D", 5: "E", 6: "F"}
    letter = building_letters.get(building_number, "А")
    lot_name = lot.get("name") or ""
    match = re.search(r'\d+', lot_name)
    if match:
        return f"{letter}{match.group()}"
    return f"{letter}{lot.get('id', 'X')}"


def transform_facility(facility: Dict) -> Dict:
    return {
        "ygroup_facility_id": facility.get("id"),
        "name": facility.get("name", ""),
        "city": facility.get("city_name", ""),
        "district": facility.get("district_name", ""),
        "address": facility.get("address", ""),
        "developer": facility.get("developer_name", ""),
        "description": facility.get("description", ""),
        "main_image_url": facility.get("facility_main_image"),
        "lots_count": facility.get("active_lots_amount", 0),
        "min_price": facility.get("min_total_price"),
        "commission_percent": facility.get("commission_percent"),
        "commissioning_year": facility.get("commissioning_year"),
        "commissioning_quarter": facility.get("commissioning_quarter"),
        "is_commissioned": 1 if facility.get("is_commissioned") else 0,
        "fz214": 1 if facility.get("fz214") else 0,
        "min_area_m2": facility.get("min_area_m2"),
        "max_area_m2": facility.get("max_area_m2"),
        "min_price_per_m2": facility.get("min_price_per_m2"),
    }


def transform_cluster(cluster: Dict, property_id: int) -> Dict:
    number = extract_building_number(cluster.get("name", ""))
    commissioning_date = None
    commissioning_timestamp = None
    year = cluster.get("commissioning_year")
    quarter = cluster.get("commissioning_quarter")
    if year and quarter:
        commissioning_date = f"Q{quarter} {year}"
        commissioning_timestamp = quarter_to_timestamp(quarter, year)
    return {
        "property_id": property_id,
        "ygroup_cluster_id": cluster.get("id"),
        "name": cluster.get("name", ""),
        "number": number,
        "floors_count": cluster.get("total_floors"),
        "commissioning_date": commissioning_date,
        "commissioning_timestamp": commissioning_timestamp,
        "is_completed": 1 if cluster.get("is_completed") else 0,
    }


def transform_lot(lot: Dict, property_id: int, building_id: int, building_number: int) -> Dict:
    code = generate_lot_code(lot, building_number)
    floor = None
    position = lot.get("position", {})
    if isinstance(position, dict):
        floor = position.get("vertical_position")
    layout_url = None
    layout_images = lot.get("layout_images", [])
    if layout_images:
        img = layout_images[0]
        if isinstance(img, str):
            layout_url = img
        elif isinstance(img, dict):
            # Новый формат: {'static_object': {'path': 'url'}}
            static_obj = img.get("static_object", {})
            layout_url = static_obj.get("path") or static_obj.get("path_1000px")
    return {
        "property_id": property_id,
        "building_id": building_id,
        "ygroup_lot_id": lot.get("id"),
        "code": code,
        "building": building_number,
        "floor": floor,
        "rooms": lot.get("layout_type"),
        "area_m2": lot.get("area_m2"),
        "price_rub": lot.get("total_price"),
        "price_per_m2": lot.get("price_per_m2"),
        "layout_url": layout_url,
        "decoration_type": lot.get("decoration_type"),
        "status": _map_lot_status(lot.get("status")),
    }


def _map_lot_status(status) -> str:
    """Маппинг статуса лота из YGroup API"""
    if status == 2:
        return "booked"
    elif status == 3:
        return "sold"
    return "available"


def import_facility(user_id: int, facility_id: str) -> Dict[str, Any]:
    """Импортировать ЖК со всеми корпусами и лотами"""
    from db.database import (
        create_property, create_building, create_unit,
        update_property_stats, set_property_custom, get_property_by_ygroup_id
    )
    
    result = {
        "success": False,
        "property_id": None,
        "buildings_count": 0,
        "units_count": 0,
        "error": None
    }
    
    # 0. Проверка на дубликат
    existing = get_property_by_ygroup_id(user_id, facility_id)
    if existing:
        result["error"] = "Этот ЖК уже добавлен"
        return result
    
    # 1. Получаем данные ЖК
    facility = get_facility(facility_id)
    if not facility:
        result["error"] = "ЖК не найден в YGroup"
        return result
    
    # 2. Создаём property
    property_data = transform_facility(facility)
    property_id = create_property(user_id, property_data)
    result["property_id"] = property_id
    
    # 3. Дефолтные кастомные данные
    set_property_custom(property_id, {
        "appreciation_rate": 10,
        "occupancy_rate": 70,
        "operating_expenses_pct": 10,
        "management_fee_pct": 20,
        "tax_rate": 4,
    })
    
    # 4. Получаем корпуса
    clusters = get_clusters(facility_id)
    
    for cluster in clusters:
        building_data = transform_cluster(cluster, property_id)
        building_id = create_building(property_id, building_data)
        building_number = building_data["number"]
        result["buildings_count"] += 1
        
        # Лоты корпуса
        lots = get_lots(cluster["id"])
        for lot in lots:
            unit_data = transform_lot(lot, property_id, building_id, building_number)
            create_unit(property_id, building_id, unit_data)
            result["units_count"] += 1
    
    update_property_stats(property_id)
    result["success"] = True
    print(f"[YGROUP] Imported: {property_data['name']} — {result['buildings_count']} buildings, {result['units_count']} units")
    
    return result


# === Справочники ===

FACILITY_CLASS = {
    1: "Эконом",
    2: "Комфорт", 
    3: "Бизнес",
    4: "Элит",
    5: "Премиум"
}

FACILITY_SUBTYPE = {
    1: "Квартиры",
    2: "Апартаменты",
    3: "Таунхаусы",
    4: "Дуплексы"
}

TERRITORY_TYPE = {
    1: "Закрытая",
    2: "Открытая"
}

HEATING_TYPE = {
    1: "Центральное",
    2: "Автономное",
    3: "Индивидуальное"
}

SEWERAGE_TYPE = {
    1: "Центральная",
    2: "Автономная",
    3: "Септик"
}

WATER_SUPPLY_TYPE = {
    1: "Центральное",
    2: "Скважина",
    3: "Колодец"
}

PARKING_TYPE = {
    1: "Подземная",
    2: "Наземная",
    3: "Придомовая",
    4: "Гостевая"
}

CONTRACT_TYPE = {
    1: "ДКП",
    2: "ДДУ",
    3: "ЖСК"
}

PAYMENT_METHOD = {
    1: "100%",
    2: "Рассрочка",
    3: "Ипотека"
}


def get_facility_details(facility_id: str) -> Optional[Dict]:
    """Получить детальную информацию о ЖК (v1 API)"""
    try:
        resp = requests.get(
            f"{API_BASE_V1}/facilities/{facility_id}",
            headers=get_headers(),
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("facility")
    except Exception as e:
        print(f"[YGROUP] get_facility_details error: {e}")
        return None


def transform_facility_details(f: Dict) -> Dict:
    """Трансформировать детальные данные ЖК"""
    # Парковка (список)
    parking = []
    for p in f.get("parking_types", []):
        if p in PARKING_TYPE:
            parking.append(PARKING_TYPE[p])
    
    # Способы оплаты
    payments = []
    for p in f.get("payment_methods", []):
        if p in PAYMENT_METHOD:
            payments.append(PAYMENT_METHOD[p])
    
    return {
        "description": f.get("description", ""),
        "address": f.get("address", ""),
        "facility_class": FACILITY_CLASS.get(f.get("class"), ""),
        "facility_subtype": FACILITY_SUBTYPE.get(f.get("subtype"), ""),
        "territory_type": TERRITORY_TYPE.get(f.get("territory_type"), ""),
        "has_gas": 1 if f.get("has_gas") else 0,
        "has_electricity": 1 if f.get("has_electricity") else 0,
        "heating_type": HEATING_TYPE.get(f.get("heating_type"), ""),
        "sewerage_type": SEWERAGE_TYPE.get(f.get("sewerage_type"), ""),
        "water_supply_type": WATER_SUPPLY_TYPE.get(f.get("water_supply_type"), ""),
        "parking_types": ", ".join(parking) if parking else "",
        "contract_type": CONTRACT_TYPE.get(f.get("contract_type"), ""),
        "payment_methods": ", ".join(payments) if payments else "",
    }
