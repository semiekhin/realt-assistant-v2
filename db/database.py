"""
База данных Realt Assistant V2
SQLite с таблицами: properties, buildings, units, property_custom, users, user_state
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "realt.db"


def get_connection() -> sqlite3.Connection:
    """Получить соединение с БД"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Инициализация всех таблиц"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Пользователи
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Состояние диалога
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_state (
            user_id INTEGER PRIMARY KEY,
            current_property_id INTEGER,
            current_lot_code TEXT,
            state TEXT,
            state_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (current_property_id) REFERENCES properties(id) ON DELETE SET NULL
        )
    """)
    
    # ЖК риэлтора
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ygroup_facility_id TEXT,
            name TEXT NOT NULL,
            city TEXT,
            district TEXT,
            address TEXT,
            developer TEXT,
            description TEXT,
            main_image_url TEXT,
            lots_count INTEGER DEFAULT 0,
            min_price INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, ygroup_facility_id)
        )
    """)
    
    # Корпуса
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buildings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            ygroup_cluster_id TEXT,
            name TEXT,
            number INTEGER,
            floors_count INTEGER,
            commissioning_date TEXT,
            commissioning_timestamp INTEGER,
            is_completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
        )
    """)
    
    # Квартиры/лоты
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            building_id INTEGER,
            ygroup_lot_id TEXT,
            code TEXT NOT NULL,
            building INTEGER,
            floor INTEGER,
            rooms INTEGER,
            area_m2 REAL,
            price_rub INTEGER,
            price_per_m2 INTEGER,
            layout_url TEXT,
            decoration_type TEXT,
            status TEXT DEFAULT 'available',
            block_section TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
            FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL
        )
    """)
    
    # Индексы для units
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_units_property ON units(property_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_units_building ON units(property_id, building)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_units_price ON units(property_id, price_rub)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_units_area ON units(property_id, area_m2)")
    
    # Кастомные данные риэлтора
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS property_custom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL UNIQUE,
            commissioning_date TEXT,
            rental_daily_rate INTEGER,
            occupancy_rate REAL DEFAULT 70,
            operating_expenses_pct REAL DEFAULT 10,
            management_fee_pct REAL DEFAULT 20,
            tax_rate REAL DEFAULT 4,
            appreciation_rate REAL DEFAULT 10,
            installment_pv REAL,
            installment_months INTEGER,
            installment_markup REAL DEFAULT 0,
            commission TEXT,
            commission_pct REAL,
            utp TEXT,
            notes TEXT,
            developer_phone TEXT,
            developer_website TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"[DB] Initialized: {DB_PATH}")


# === Users ===

def get_or_create_user(user_id: int, username: str = "", first_name: str = "", last_name: str = "") -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row:
        user = dict(row)
    else:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        conn.commit()
        user = {"user_id": user_id, "username": username, "first_name": first_name, "last_name": last_name}
    
    conn.close()
    return user


# === User State ===

def get_user_state(user_id: int) -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_state WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return {"user_id": user_id, "current_property_id": None, "current_lot_code": None, "state": None, "state_data": None}


def set_user_state(user_id: int, property_id: int = None, lot_code: str = None, state: str = None, state_data: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_state (user_id, current_property_id, current_lot_code, state, state_data, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            current_property_id = excluded.current_property_id,
            current_lot_code = excluded.current_lot_code,
            state = excluded.state,
            state_data = excluded.state_data,
            updated_at = excluded.updated_at
    """, (user_id, property_id, lot_code, state, state_data, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def clear_user_state(user_id: int):
    set_user_state(user_id, None, None, None, None)


# === Properties ===

def create_property(user_id: int, data: Dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO properties (user_id, ygroup_facility_id, name, city, district, address, developer, description, main_image_url, lots_count, min_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data.get("ygroup_facility_id"),
        data.get("name"),
        data.get("city"),
        data.get("district"),
        data.get("address"),
        data.get("developer"),
        data.get("description"),
        data.get("main_image_url"),
        data.get("lots_count", 0),
        data.get("min_price")
    ))
    property_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return property_id


def get_user_properties(user_id: int) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties WHERE user_id = ? ORDER BY name", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_property(property_id: int) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_property(property_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM properties WHERE id = ?", (property_id,))
    conn.commit()
    conn.close()


def update_property_stats(property_id: int):
    """Обновить кэш lots_count и min_price"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE properties SET
            lots_count = (SELECT COUNT(*) FROM units WHERE property_id = ?),
            min_price = (SELECT MIN(price_rub) FROM units WHERE property_id = ?),
            updated_at = ?
        WHERE id = ?
    """, (property_id, property_id, datetime.now().isoformat(), property_id))
    conn.commit()
    conn.close()


# === Buildings ===

def create_building(property_id: int, data: Dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO buildings (property_id, ygroup_cluster_id, name, number, floors_count, commissioning_date, commissioning_timestamp, is_completed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        property_id,
        data.get("ygroup_cluster_id"),
        data.get("name"),
        data.get("number"),
        data.get("floors_count"),
        data.get("commissioning_date"),
        data.get("commissioning_timestamp"),
        data.get("is_completed", 0)
    ))
    building_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return building_id


def get_property_buildings(property_id: int) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM buildings WHERE property_id = ? ORDER BY number", (property_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_building(building_id: int) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM buildings WHERE id = ?", (building_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# === Units ===

def create_unit(property_id: int, building_id: int, data: Dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO units (property_id, building_id, ygroup_lot_id, code, building, floor, rooms, area_m2, price_rub, price_per_m2, layout_url, decoration_type, status, block_section)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        property_id,
        building_id,
        data.get("ygroup_lot_id"),
        data.get("code"),
        data.get("building"),
        data.get("floor"),
        data.get("rooms"),
        data.get("area_m2"),
        data.get("price_rub"),
        data.get("price_per_m2"),
        data.get("layout_url"),
        data.get("decoration_type"),
        data.get("status", "available"),
        data.get("block_section")
    ))
    unit_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return unit_id


def get_property_units(property_id: int, building: int = None, floor: int = None) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM units WHERE property_id = ?"
    params = [property_id]
    
    if building:
        query += " AND building = ?"
        params.append(building)
    if floor:
        query += " AND floor = ?"
        params.append(floor)
    
    query += " ORDER BY building, floor, code"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_unit_by_code(property_id: int, code: str, building: int = None) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    if building:
        cursor.execute("SELECT * FROM units WHERE property_id = ? AND code = ? AND building = ?", (property_id, code, building))
    else:
        cursor.execute("SELECT * FROM units WHERE property_id = ? AND code = ?", (property_id, code))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_units_by_budget(property_id: int, min_price: int, max_price: int) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM units WHERE property_id = ? AND price_rub BETWEEN ? AND ? ORDER BY price_rub",
        (property_id, min_price, max_price)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_units_by_area(property_id: int, min_area: float, max_area: float) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM units WHERE property_id = ? AND area_m2 BETWEEN ? AND ? ORDER BY area_m2",
        (property_id, min_area, max_area)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_available_floors(property_id: int, building: int) -> List[Dict]:
    """Список этажей с количеством лотов"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT floor, COUNT(*) as count, MIN(price_rub) as min_price
        FROM units
        WHERE property_id = ? AND building = ?
        GROUP BY floor
        ORDER BY floor
    """, (property_id, building))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_building_stats(property_id: int) -> List[Dict]:
    """Статистика по корпусам"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            building,
            COUNT(*) as count,
            MIN(price_rub) as min_price,
            MAX(price_rub) as max_price,
            MIN(floor) as min_floor,
            MAX(floor) as max_floor
        FROM units
        WHERE property_id = ?
        GROUP BY building
        ORDER BY building
    """, (property_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# === Property Custom ===

def get_property_custom(property_id: int) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM property_custom WHERE property_id = ?", (property_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def set_property_custom(property_id: int, data: Dict):
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = [
        "commissioning_date", "rental_daily_rate", "occupancy_rate",
        "operating_expenses_pct", "management_fee_pct", "tax_rate",
        "appreciation_rate", "installment_pv", "installment_months",
        "installment_markup", "commission", "commission_pct",
        "utp", "notes", "developer_phone", "developer_website"
    ]
    
    values = [data.get(f) for f in fields]
    
    cursor.execute(f"""
        INSERT INTO property_custom (property_id, {', '.join(fields)})
        VALUES (?, {', '.join(['?'] * len(fields))})
        ON CONFLICT(property_id) DO UPDATE SET
            {', '.join([f'{f} = excluded.{f}' for f in fields])},
            updated_at = ?
    """, [property_id] + values + [datetime.now().isoformat()])
    
    conn.commit()
    conn.close()


# Инициализация при импорте
init_db()
