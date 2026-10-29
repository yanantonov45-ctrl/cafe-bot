from html import escape

from config import DELIVERY_PRICE, FREE_DELIVERY_FROM, MENU, STATUSES


def cart_items(cart: dict[str, int]) -> list[dict]:
    """Позиции корзины в виде списка (неизвестные id из старого меню пропускаем)."""
    return [
        {"id": iid, "name": MENU[iid]["name"], "price": MENU[iid]["price"], "qty": qty}
        for iid, qty in cart.items() if iid in MENU
    ]


def subtotal(items: list[dict]) -> int:
    return sum(i["price"] * i["qty"] for i in items)


def delivery_fee(delivery_type: str, amount: int) -> int:
    if delivery_type != "delivery" or amount >= FREE_DELIVERY_FROM:
        return 0
    return DELIVERY_PRICE


def items_text(items: list[dict]) -> str:
    return "\n".join(
        f"• {i['name']} × {i['qty']} = {i['price'] * i['qty']} ₽" for i in items
    )


def cart_text(items: list[dict]) -> str:
    if not items:
        return "🛒 Корзина пуста. Загляните в меню!"
    total = subtotal(items)
    text = f"<b>🛒 Ваша корзина</b>\n\n{items_text(items)}\n\nИтого: <b>{total} ₽</b>"
    if total < FREE_DELIVERY_FROM:
        text += f"\n<i>До бесплатной доставки: {FREE_DELIVERY_FROM - total} ₽</i>"
    return text


def order_text(o: dict, title: str = "", with_status: bool = True) -> str:
    lines = [f"<b>{title}</b>\n"] if title else []
    lines.append(items_text(o["items"]))
    lines.append("")
    if o["delivery_type"] == "delivery":
        fee = o["delivery_fee"]
        lines.append(f"🚗 Доставка: {escape(o['address'] or '')}")
        lines.append(f"   стоимость: {'бесплатно' if fee == 0 else f'{fee} ₽'}")
    else:
        lines.append("🏃 Самовывоз")
    lines.append(f"📞 {o['phone']}")
    if o.get("comment"):
        lines.append(f"💬 {escape(o['comment'])}")
    lines.append(f"\n💰 К оплате: <b>{o['subtotal'] + o['delivery_fee']} ₽</b>")
    if with_status and o.get("status"):
        lines.append(f"Статус: {STATUSES[o['status']]}")
    return "\n".join(lines)
