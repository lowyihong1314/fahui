from app.models import OrderItem
from app.services.order_item_service import OrderItemService


def get_paiwei_data_by_item_ids(order_item_ids):
    items = OrderItem.query.filter(OrderItem.id.in_(order_item_ids)).all()
    return [OrderItemService.to_all_print(item) for item in items]
