from aiogram.types import (InlineKeyboardButton, KeyboardButton,
                           ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CATEGORIES, FINAL_STATUSES, MENU, STATUSES

BTN_MENU = "🍽 Меню"
BTN_CART = "🛒 Корзина"
BTN_ORDERS = "📦 Мои заказы"
BTN_ABOUT = "ℹ️ О нас"
BTN_CANCEL = "✖️ Отмена"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_MENU), KeyboardButton(text=BTN_CART)],
            [KeyboardButton(text=BTN_ORDERS), KeyboardButton(text=BTN_ABOUT)],
        ],
        resize_keyboard=True,
    )


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер", request_contact=True)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def categories_kb(cart_count: int = 0):
    b = InlineKeyboardBuilder()
    for cid, title in CATEGORIES.items():
        b.button(text=title, callback_data=f"cat:{cid}")
    b.adjust(2)
    cart_title = f"🛒 Корзина ({cart_count})" if cart_count else "🛒 Корзина"
    b.row(InlineKeyboardButton(text=cart_title, callback_data="cart"))
    return b.as_markup()


def items_kb(cat_id: str):
    b = InlineKeyboardBuilder()
    for iid, item in MENU.items():
        if item["cat"] == cat_id:
            b.button(text=f"{item['name']} — {item['price']} ₽", callback_data=f"item:{iid}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text="← Категории", callback_data="cats"),
          InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"))
    return b.as_markup()


def item_kb(item_id: str, qty: int):
    item = MENU[item_id]
    b = InlineKeyboardBuilder()
    if qty == 0:
        b.row(InlineKeyboardButton(text=f"➕ В корзину — {item['price']} ₽",
                                   callback_data=f"add:{item_id}"))
    else:
        b.row(
            InlineKeyboardButton(text="➖", callback_data=f"sub:{item_id}"),
            InlineKeyboardButton(text=f"{qty} шт.", callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"add:{item_id}"),
        )
    b.row(InlineKeyboardButton(text="← Назад", callback_data=f"cat:{item['cat']}"),
          InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"))
    return b.as_markup()


def cart_kb(items: list[dict]):
    b = InlineKeyboardBuilder()
    for i in items:
        b.row(
            InlineKeyboardButton(text="➖", callback_data=f"csub:{i['id']}"),
            InlineKeyboardButton(text=f"{i['name']} ×{i['qty']}", callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"cadd:{i['id']}"),
        )
    if items:
        b.row(InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"))
        b.row(InlineKeyboardButton(text="🗑 Очистить", callback_data="clear"),
              InlineKeyboardButton(text="🍽 Меню", callback_data="cats"))
    else:
        b.row(InlineKeyboardButton(text="🍽 Открыть меню", callback_data="cats"))
    return b.as_markup()


def delivery_kb():
    b = InlineKeyboardBuilder()
    b.button(text="🚗 Доставка", callback_data="dlv:delivery")
    b.button(text="🏃 Самовывоз", callback_data="dlv:pickup")
    b.button(text=BTN_CANCEL, callback_data="order_cancel")
    b.adjust(2, 1)
    return b.as_markup()


def skip_comment_kb():
    b = InlineKeyboardBuilder()
    b.button(text="Без комментария →", callback_data="skip_comment")
    return b.as_markup()


def confirm_kb():
    b = InlineKeyboardBuilder()
    b.button(text="✅ Подтвердить заказ", callback_data="order_confirm")
    b.button(text=BTN_CANCEL, callback_data="order_cancel")
    b.adjust(1)
    return b.as_markup()


def admin_order_kb(order_id: int, status: str):
    if status in FINAL_STATUSES:
        return None
    b = InlineKeyboardBuilder()
    for key, title in STATUSES.items():
        if key not in ("new", status):
            b.button(text=title, callback_data=f"ost:{order_id}:{key}")
    b.adjust(2)
    return b.as_markup()
