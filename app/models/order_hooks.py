from sqlalchemy import event, inspect

from app.extensions import db
from app.models.order_models import ItemFormData, Order, OrderItem


def is_order_read_only(order) -> bool:
    from app.function.common import READ_ONLY_ORDER_VERSIONS

    return order and order.version in READ_ONLY_ORDER_VERSIONS


@event.listens_for(Order, "before_update", propagate=True)
def protect_order_update(mapper, connection, target):
    if not is_order_read_only(target):
        return

    state = inspect(target)
    changed = {attr.key for attr in state.attrs if attr.history.has_changes()}
    if changed != {"phone"}:
        raise ValueError(
            f"Order version '{target.version}' is read-only (except phone)."
        )


@event.listens_for(Order, "before_delete", propagate=True)
def protect_order_delete(mapper, connection, target):
    if is_order_read_only(target):
        raise ValueError(
            f"Order version '{target.version}' is read-only and cannot be deleted."
        )


def get_parent_order_from_item(item):
    if item.order:
        return item.order
    if item.order_id:
        return db.session.get(Order, item.order_id)
    return None


@event.listens_for(OrderItem, "before_insert", propagate=True)
@event.listens_for(OrderItem, "before_update", propagate=True)
@event.listens_for(OrderItem, "before_delete", propagate=True)
def protect_order_item(mapper, connection, target):
    order = get_parent_order_from_item(target)
    if is_order_read_only(order):
        raise ValueError(
            f"Cannot modify OrderItem: parent Order version '{order.version}' is read-only."
        )


def get_parent_order_from_form_data(form_data):
    if form_data.item and form_data.item.order:
        return form_data.item.order
    if form_data.item_id:
        item = db.session.get(OrderItem, form_data.item_id)
        return item.order if item else None
    return None


@event.listens_for(ItemFormData, "before_insert", propagate=True)
@event.listens_for(ItemFormData, "before_update", propagate=True)
@event.listens_for(ItemFormData, "before_delete", propagate=True)
def protect_item_form_data(mapper, connection, target):
    order = get_parent_order_from_form_data(target)
    if is_order_read_only(order):
        raise ValueError(
            "Cannot modify ItemFormData: parent Order version "
            f"'{order.version}' is read-only."
        )
