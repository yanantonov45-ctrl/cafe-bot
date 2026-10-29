import logging
import re
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from cart import cart_items, cart_text, delivery_fee, order_text, subtotal
from config import (ABOUT_TEXT, ADMIN_IDS, CATEGORIES, MENU, MIN_ORDER,
                    SHOP_NAME, STATUSES)

router = Router()
log = logging.getLogger(__name__)


class Checkout(StatesGroup):
    delivery = State()
    address = State()
    phone = State()
    comment = State()
    confirm = State()


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits[0] == "8":
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    return "+" + digits if 11 <= len(digits) <= 12 else None


async def safe_edit(call: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:  # сообщение не изменилось
        pass


async def cart_count(user_id: int) -> int:
    return sum((await db.get_cart(user_id)).values())


# ---------- Общее ----------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {escape(message.from_user.first_name)}! 👋\n\n"
        f"Это <b>{SHOP_NAME}</b> — соберите заказ прямо в Telegram, "
        "а мы приготовим и привезём 🔥",
        reply_markup=kb.main_menu(),
    )


@router.message(Command("cancel"))
@router.message(F.text == kb.BTN_CANCEL)
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Оформление отменено. Корзина сохранена 🛒",
                         reply_markup=kb.main_menu())


@router.message(F.text == kb.BTN_ABOUT)
async def about(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(ABOUT_TEXT)


@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery):
    await call.answer()


# ---------- Меню ----------

@router.message(Command("menu"))
@router.message(F.text == kb.BTN_MENU)
async def menu_msg(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите категорию:",
                         reply_markup=kb.categories_kb(await cart_count(message.from_user.id)))


@router.callback_query(F.data == "cats")
async def menu_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(call, "Выберите категорию:",
                    kb.categories_kb(await cart_count(call.from_user.id)))
    await call.answer()


@router.callback_query(F.data.startswith("cat:"))
async def category(call: CallbackQuery):
    cat_id = call.data.split(":", 1)[1]
    if cat_id not in CATEGORIES:
        return await call.answer()
    await safe_edit(call, f"<b>{CATEGORIES[cat_id]}</b>", kb.items_kb(cat_id))
    await call.answer()


def item_text(item_id: str) -> str:
    item = MENU[item_id]
    return f"<b>{item['name']}</b>\n\n{item['desc']}\n\n💰 {item['price']} ₽"


@router.callback_query(F.data.startswith("item:"))
async def item_card(call: CallbackQuery):
    item_id = call.data.split(":", 1)[1]
    if item_id not in MENU:
        return await call.answer("Позиция недоступна", show_alert=True)
    qty = (await db.get_cart(call.from_user.id)).get(item_id, 0)
    await safe_edit(call, item_text(item_id), kb.item_kb(item_id, qty))
    await call.answer()


@router.callback_query(F.data.startswith(("add:", "sub:")))
async def item_qty(call: CallbackQuery):
    action, item_id = call.data.split(":", 1)
    if item_id not in MENU:
        return await call.answer()
    qty = await db.change_qty(call.from_user.id, item_id, 1 if action == "add" else -1)
    await call.message.edit_reply_markup(reply_markup=kb.item_kb(item_id, qty))
    await call.answer("Добавлено в корзину" if action == "add" else "Убрано")


# ---------- Корзина ----------

async def render_cart(user_id: int):
    items = cart_items(await db.get_cart(user_id))
    return cart_text(items), kb.cart_kb(items)


@router.message(F.text == kb.BTN_CART)
async def cart_msg(message: Message, state: FSMContext):
    await state.clear()
    text, markup = await render_cart(message.from_user.id)
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data == "cart")
async def cart_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    text, markup = await render_cart(call.from_user.id)
    await safe_edit(call, text, markup)
    await call.answer()


@router.callback_query(F.data.startswith(("cadd:", "csub:")))
async def cart_qty(call: CallbackQuery):
    action, item_id = call.data.split(":", 1)
    await db.change_qty(call.from_user.id, item_id, 1 if action == "cadd" else -1)
    text, markup = await render_cart(call.from_user.id)
    await safe_edit(call, text, markup)
    await call.answer()


@router.callback_query(F.data == "clear")
async def cart_clear(call: CallbackQuery):
    await db.clear_cart(call.from_user.id)
    text, markup = await render_cart(call.from_user.id)
    await safe_edit(call, text, markup)
    await call.answer("Корзина очищена")


# ---------- Оформление ----------

@router.callback_query(F.data == "checkout")
async def checkout(call: CallbackQuery, state: FSMContext):
    items = cart_items(await db.get_cart(call.from_user.id))
    if not items:
        return await call.answer("Корзина пуста", show_alert=True)
    if subtotal(items) < MIN_ORDER:
        return await call.answer(f"Минимальная сумма заказа — {MIN_ORDER} ₽",
                                 show_alert=True)
    await state.set_state(Checkout.delivery)
    await safe_edit(call, "Как хотите получить заказ?", kb.delivery_kb())
    await call.answer()


@router.callback_query(Checkout.delivery, F.data.startswith("dlv:"))
async def pick_delivery(call: CallbackQuery, state: FSMContext):
    dtype = call.data.split(":", 1)[1]
    await state.update_data(delivery_type=dtype, address=None)
    if dtype == "delivery":
        await state.set_state(Checkout.address)
        await safe_edit(call, "🚗 Доставка\n\nНапишите адрес: улица, дом, подъезд, квартира.")
    else:
        await state.set_state(Checkout.phone)
        await safe_edit(call, "🏃 Самовывоз")
        await call.message.answer("Оставьте номер телефона — кнопкой или вручную:",
                                  reply_markup=kb.phone_kb())
    await call.answer()


@router.message(Checkout.address, F.text)
async def get_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if not 5 <= len(address) <= 200:
        return await message.answer("Укажите адрес подробнее, пожалуйста.")
    await state.update_data(address=address)
    await state.set_state(Checkout.phone)
    await message.answer("Оставьте номер телефона — кнопкой или вручную:",
                         reply_markup=kb.phone_kb())


async def _save_phone(message: Message, state: FSMContext, raw: str) -> None:
    phone = normalize_phone(raw)
    if not phone:
        await message.answer("Похоже, номер некорректный. Пример: +7 913 123-45-67")
        return
    await state.update_data(phone=phone)
    await state.set_state(Checkout.comment)
    await message.answer("Номер сохранён ✅", reply_markup=kb.main_menu())
    await message.answer("Комментарий к заказу? Например: «без лука», «позвонить за 10 минут».",
                         reply_markup=kb.skip_comment_kb())


@router.message(Checkout.phone, F.contact)
async def phone_contact(message: Message, state: FSMContext):
    await _save_phone(message, state, message.contact.phone_number)


@router.message(Checkout.phone, F.text)
async def phone_text(message: Message, state: FSMContext):
    await _save_phone(message, state, message.text)


async def build_preview(user_id: int, data: dict) -> dict | None:
    items = cart_items(await db.get_cart(user_id))
    if not items:
        return None
    amount = subtotal(items)
    return {
        "items": items,
        "subtotal": amount,
        "delivery_fee": delivery_fee(data["delivery_type"], amount),
        "delivery_type": data["delivery_type"],
        "address": data.get("address"),
        "phone": data["phone"],
        "comment": data.get("comment"),
    }


async def show_confirm(message: Message, user_id: int, state: FSMContext, edit: bool):
    preview = await build_preview(user_id, await state.get_data())
    if not preview:
        await state.clear()
        return await message.answer("Корзина пуста — оформление отменено.")
    await state.set_state(Checkout.confirm)
    text = order_text(preview, "Проверьте заказ:", with_status=False)
    if edit:
        await message.edit_text(text, reply_markup=kb.confirm_kb())
    else:
        await message.answer(text, reply_markup=kb.confirm_kb())


@router.message(Checkout.comment, F.text)
async def get_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text.strip()[:300])
    await show_confirm(message, message.from_user.id, state, edit=False)


@router.callback_query(Checkout.comment, F.data == "skip_comment")
async def skip_comment(call: CallbackQuery, state: FSMContext):
    await state.update_data(comment=None)
    await show_confirm(call.message, call.from_user.id, state, edit=True)
    await call.answer()


@router.callback_query(Checkout.confirm, F.data == "order_confirm")
async def order_confirm(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    preview = await build_preview(call.from_user.id, data)
    if not preview:
        await state.clear()
        return await call.answer("Корзина пуста", show_alert=True)

    stored_items = [{k: i[k] for k in ("name", "price", "qty")} for i in preview["items"]]
    order_id = await db.create_order(
        call.from_user.id, stored_items, preview["subtotal"], preview["delivery_fee"],
        preview["delivery_type"], preview["address"], preview["phone"], preview["comment"],
    )
    await state.clear()
    order = await db.get_order(order_id)
    await safe_edit(call, order_text(order, f"🎉 Заказ #{order_id} оформлен!")
                    + "\n\nМы пришлём уведомление, когда статус изменится.")
    await call.answer()

    user = call.from_user
    link = f'<a href="tg://user?id={user.id}">{escape(user.full_name)}</a>'
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                order_text(order, f"🆕 Новый заказ #{order_id}") + f"\n👤 {link}",
                reply_markup=kb.admin_order_kb(order_id, order["status"]),
            )
        except Exception as e:
            log.warning("Не удалось уведомить админа %s: %s", admin_id, e)


@router.callback_query(F.data == "order_cancel")
async def order_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(call, "Оформление отменено. Корзина сохранена 🛒")
    await call.answer()


# ---------- Мои заказы ----------

@router.message(F.text == kb.BTN_ORDERS)
async def my_orders(message: Message, state: FSMContext):
    await state.clear()
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        return await message.answer("Вы ещё ничего не заказывали. Самое время 😉")
    lines = ["<b>Последние заказы:</b>\n"]
    for o in orders:
        total = o["subtotal"] + o["delivery_fee"]
        lines.append(f"#{o['id']} · {total} ₽ · {STATUSES[o['status']]}")
    await message.answer("\n".join(lines))


@router.message()
async def fallback(message: Message):
    await message.answer("Не совсем понял 🙂 Воспользуйтесь меню ниже.",
                         reply_markup=kb.main_menu())
