import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
DB_PATH = os.getenv("DB_PATH", "cafe.db")
SHOP_NAME = os.getenv("SHOP_NAME", "Demo Kitchen")

MIN_ORDER = 500           # минимальная сумма заказа, ₽
DELIVERY_PRICE = 200      # стоимость доставки, ₽
FREE_DELIVERY_FROM = 1500  # бесплатная доставка от суммы, ₽

CATEGORIES = {
    "burgers": "🍔 Бургеры",
    "pizza": "🍕 Пицца",
    "rolls": "🍣 Роллы",
    "drinks": "🥤 Напитки",
}

MENU = {
    "b1": {"cat": "burgers", "name": "Классический бургер", "price": 390,
           "desc": "Говяжья котлета, чеддер, томаты, маринованный огурец, фирменный соус"},
    "b2": {"cat": "burgers", "name": "Бургер с беконом", "price": 450,
           "desc": "Говяжья котлета, хрустящий бекон, чеддер, соус барбекю"},
    "b3": {"cat": "burgers", "name": "Чикен бургер", "price": 360,
           "desc": "Куриное филе в панировке, салат айсберг, соус ранч"},
    "p1": {"cat": "pizza", "name": "Маргарита", "price": 520,
           "desc": "Томатный соус, моцарелла, базилик. 30 см"},
    "p2": {"cat": "pizza", "name": "Пепперони", "price": 620,
           "desc": "Томатный соус, моцарелла, пепперони. 30 см"},
    "p3": {"cat": "pizza", "name": "Четыре сыра", "price": 690,
           "desc": "Сливочный соус, моцарелла, дорблю, пармезан, чеддер. 30 см"},
    "r1": {"cat": "rolls", "name": "Филадельфия", "price": 590,
           "desc": "Лосось, сливочный сыр, огурец. 8 шт."},
    "r2": {"cat": "rolls", "name": "Калифорния", "price": 490,
           "desc": "Снежный краб, авокадо, огурец, икра масаго. 8 шт."},
    "d1": {"cat": "drinks", "name": "Морс клюквенный", "price": 150,
           "desc": "Домашний, 0,5 л"},
    "d2": {"cat": "drinks", "name": "Лимонад", "price": 180,
           "desc": "Цитрус-мята, 0,5 л"},
}

STATUSES = {
    "new": "🆕 Новый",
    "accepted": "✅ Принят",
    "cooking": "👨‍🍳 Готовится",
    "ready": "🚗 В пути / готов к выдаче",
    "done": "🏁 Выполнен",
    "cancelled": "❌ Отменён",
}
FINAL_STATUSES = {"done", "cancelled"}

ABOUT_TEXT = (
    f"<b>{SHOP_NAME}</b>\n\n"
    "📍 ул. Примерная, 1\n"
    "🕙 Ежедневно 10:00–23:00\n"
    "📞 +7 (900) 000-00-00\n\n"
    f"🚗 Доставка {DELIVERY_PRICE} ₽, бесплатно от {FREE_DELIVERY_FROM} ₽\n"
    f"🧾 Минимальный заказ — {MIN_ORDER} ₽"
)
