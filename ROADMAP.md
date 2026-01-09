# REALT ASSISTANT V2 — Дорожная карта проекта

## 📋 О проекте

**Realt Assistant V2** — Telegram-бот для индивидуальных риэлторов. Персональный AI-ассистент для работы с базой ЖК от разных застройщиков.

**Ключевая идея:** Взять отлаженный движок RIZALTA (навигация, Mini App, КП, калькуляторы) и добавить уровень "Мои ЖК" для работы с несколькими застройщиками.

**Акцент проекта:** НЕ просто база данных объектов, а **ИИ-сервисы** которые помогают риэлтору продавать — анализ, аргументация, работа с возражениями, персональные подборки.

**Принцип:** RIZALTA = донор кода. Сам бот RIZALTA не трогаем. Создаём новый проект на его основе.

---

## 🏗 Архитектура

### Концепция
```
┌─────────────────────────────────────────────────────────────┐
│                     REALT ASSISTANT V2                       │
│                                                              │
│  👤 Риэлтор                                                  │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────────┐           │
│  │            🏠 МОИ ЖК (список)                 │           │
│  │  ┌────────┐  ┌────────┐  ┌────────┐          │           │
│  │  │ЖК Alpha│  │ЖК Beta │  │ЖК Gamma│          │           │
│  │  └───┬────┘  └───┬────┘  └───┬────┘          │           │
│  └──────┼───────────┼───────────┼───────────────┘           │
│         │           │           │                            │
│         └───────────┼───────────┘                            │
│                     ▼                                        │
│  ┌─────────────────────────────────────────────┐            │
│  │              МЕНЮ ЖК                         │            │
│  │  [🏠 Выбор лота] [🔍 Поиск] [ℹ️ О проекте]   │            │
│  └──────────────────┬──────────────────────────┘            │
│                     │                                        │
│                     ▼                                        │
│  ┌─────────────────────────────────────────────┐            │
│  │           МЕНЮ КОНКРЕТНОГО ЛОТА              │            │
│  │                                              │            │
│  │  [📄 КП] [📊 ROI] [💰 vs Депозит] [🤖 AI]    │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Поток пользователя
```
/start → Список ЖК → Выбор ЖК → Меню ЖК
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
        [🏠 Выбор лота]    [🔍 Поиск вручную]   [ℹ️ О проекте]
          Mini App         Building→Floor→Lot      Инфо
                │                   │
                └─────────┬─────────┘
                          ▼
                   Конкретный лот
                          │
        ┌─────────┬───────┴───────┬─────────┐
        ▼         ▼               ▼         ▼
     [📄 КП]  [📊 ROI]    [💰 vs Депозит] [🤖 AI]
```

---

## 🗄 База данных

### properties (ЖК риэлтора)
```sql
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ygroup_facility_id INTEGER,
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
);
```

### buildings (корпуса)
```sql
CREATE TABLE buildings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    ygroup_cluster_id INTEGER,
    name TEXT,
    number INTEGER,
    floors_count INTEGER,
    commissioning_date TEXT,
    commissioning_timestamp INTEGER,
    is_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);
```

### units (квартиры/лоты)
```sql
CREATE TABLE units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    building_id INTEGER,
    ygroup_lot_id INTEGER,
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
);
```

### property_custom (кастомные данные риэлтора)
```sql
CREATE TABLE property_custom (
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
);
```

---

## 🔌 YGroup API
```
Base URL: https://api-ru.ygroup.ru/v2/
Auth: Bearer token

GET /facilities?types=6&city_id={id}  — список ЖК
GET /clusters?facility_id={id}        — корпуса
GET /lots?cluster_id={id}             — квартиры
```

---

## 🚀 Этапы разработки

### Этап 1: Фундамент ⏳
- [ ] Структура проекта
- [ ] База данных
- [ ] YGroup API клиент
- [ ] Импорт тестового ЖК

### Этап 2: Навигация
- [ ] /start → список ЖК
- [ ] Меню ЖК
- [ ] Ручной поиск
- [ ] Меню лота

### Этап 3: Mini App
- [ ] Форк rizalta-miniapp
- [ ] API с property_id
- [ ] Деплой

### Этап 4: Калькуляторы
- [ ] ROI с учётом сдачи
- [ ] Сравнение с депозитом
- [ ] Рассрочка

### Этап 5: КП
- [ ] Шаблон PDF
- [ ] Генерация

### Этап 6-7: AI-сервисы
- [ ] Генератор аргументов
- [ ] Работа с возражениями
- [ ] Помощник в диалоге
- [ ] Инвестиционный отчёт

---

## 📁 Структура проекта
```
/opt/realt-assistant-v2/
├── app.py
├── run_polling.py
├── config/settings.py
├── handlers/
│   ├── start.py
│   ├── properties.py
│   ├── property_menu.py
│   ├── search.py
│   ├── lot_menu.py
│   ├── kp.py
│   ├── calc_roi.py
│   ├── calc_compare.py
│   └── ai_services.py
├── services/
│   ├── telegram.py
│   ├── ygroup.py
│   ├── units_db.py
│   ├── properties_db.py
│   ├── calculations.py
│   └── kp_generator.py
├── db/database.py
└── data/realt.db
```

---

## 🔗 Ссылки

- **Донор:** https://github.com/semiekhin/rizalta-bot
- **Mini App донор:** https://github.com/semiekhin/rizalta-miniapp
- **YGroup API:** https://api-ru.ygroup.ru/v2/

---

*Документ: v0.0.2 от 09.01.2026*
