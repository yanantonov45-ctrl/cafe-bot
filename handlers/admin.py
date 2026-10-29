from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from cart import order_text
from config import ADMIN_IDS, STATUSES

router = Router()
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))

CLIENT_MESSAGES = {
    "accepted": "✅ Заказ #{id} принят! Скоро начнём готовить.",
    "cooking": "👨‍🍳 Заказ #{id} готовится.",
    "ready": "🚗 Заказ #{id} в пути (или готов к выдаче, если самовывоз).",
    "done": "🏁 Заказ #{id} выполнен. Приятного аппетита!",
    "cancelled": "❌ Заказ #{id} отменён. Если есть вопросы — позвоните нам.",
}


@router.message(Command("admin"))
async def admin_panel(message: Message):
    orders = await db.get_active_orders()
    if not orders:
        return await message.answer("🔧 Активных заказов нет.")
    await message.answer(f"🔧 Активных заказов: <b>{len(orders)}</b>")
    for o in orders[:15]:
        await message.answer(order_text(o, f"Заказ #{o['id']}"),
                             reply_markup=kb.admin_order_kb(o["id"], o["status"]))


@router.callback_query(F.data.startswith("ost:"))
async def change_status(call: CallbackQuery, bot: Bot):
    _, order_id, status = call.data.split(":")
    order_id = int(order_id)
    order = await db.get_order(order_id)
    if not order or status not in STATUSES:
        return await call.answer("Заказ не найден", show_alert=True)
    if order["status"] == status:
        return await call.answer("Статус уже установлен")

    await db.set_status(order_id, status)
    order["status"] = status
    await call.message.edit_text(order_text(order, f"Заказ #{order_id}"),
                                 reply_markup=kb.admin_order_kb(order_id, status))
    await call.answer(STATUSES[status])
    try:
        await bot.send_message(order["user_id"], CLIENT_MESSAGES[status].format(id=order_id))
    except Exception:
        pass
