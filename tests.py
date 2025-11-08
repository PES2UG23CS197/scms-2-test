# tests.py
import pytest
from decimal import Decimal
from db.queries import (
    add_product, get_all_products, update_product, delete_product,
    add_inventory, get_inventory, get_low_stock,
    move_product, get_route_cost, get_cheapest_route,
    place_order, get_orders, update_order_status, delete_order,
    add_forecast, get_forecast, get_inventory_for_forecast,
    get_connection
)

# F-001: Add/Edit/Delete Product
def test_add_update_delete_product():
    sku = "TESTSKU"
    delete_product(sku)
    add_product(sku, "Test Product", "Test Desc", 5)
    products = get_all_products()
    assert any(p[0] == sku for p in products)

    update_product(sku, "Updated Name", "Updated Desc", 10)
    updated = [p for p in get_all_products() if p[0] == sku][0]
    assert updated[1] == "Updated Name"
    assert updated[2] == "Updated Desc"
    assert updated[3] == 10

    delete_product(sku)
    products = get_all_products()
    assert not any(p[0] == sku for p in products)

# F-002 & F-003: Inventory Tracking & Low Stock Alert
def test_inventory_tracking_and_alert():
    sku = "SKU001"
    location = "Warehouse A"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Inventory WHERE sku = %s AND location = %s", (sku, location))
    conn.commit()

    add_inventory(sku, location, 3)
    inventory = get_inventory()
    assert any(i[1] == sku and i[2] == location for i in inventory)

    low_stock = get_low_stock()
    assert any(i[0] == sku and i[2] == location for i in low_stock)

# F-004, F-005, F-008: Move Product, Transport Cost, Route Optimization
def test_move_product_and_cost():
    sku = "SKU001"
    origin = "Warehouse A"
    destination = "Retail Hub 1"
    quantity = 1

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Inventory WHERE sku = %s AND location IN (%s, %s)", (sku, origin, destination))
    cursor.execute("INSERT INTO Inventory (sku, location, quantity) VALUES (%s, %s, %s)", (sku, origin, 20))
    conn.commit()

    cost = get_route_cost(origin, destination)
    assert cost is not None

    move_product(sku, origin, destination, quantity, cost)
    inventory = get_inventory()
    dest_qty = [i[3] for i in inventory if i[1] == sku and i[2] == destination]
    assert dest_qty and dest_qty[0] >= quantity

# F-006: Place, Update, Delete Order
def test_order_flow():
    sku = "SKU001"
    customer = "TestUser"
    location = "Retail Hub 1"

    place_order(sku, 2, customer, location)
    orders = get_orders()
    assert any(o[1] == sku and o[3] == customer for o in orders)

    order_id = [o[0] for o in orders if o[3] == customer][0]
    update_order_status(order_id, "Processed")
    updated = [o for o in get_orders() if o[0] == order_id][0]
    assert updated[5] == "Processed"

    delete_order(order_id)
    orders = get_orders()
    assert not any(o[0] == order_id for o in orders)

# F-007: Forecast Demand
def test_forecast_and_gap():
    sku = "SKU001"
    add_forecast(sku, 10, "2025-11-10")
    forecasts = get_forecast()
    assert any(f[0] == sku for f in forecasts)

    inventory = get_inventory_for_forecast(sku)
    assert isinstance(inventory, (int, float, Decimal))
