from db.connection import get_connection

# PRODUCT FUNCTIONS
def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def add_product(sku, name, description, threshold):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Products (sku, name, description, threshold) VALUES (%s, %s, %s, %s)",
                   (sku, name, description, threshold))
    conn.commit()
    cursor.close()
    conn.close()

def update_product(sku, name, description, threshold):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Products SET name=%s, description=%s, threshold=%s WHERE sku=%s",
                   (name, description, threshold, sku))
    conn.commit()
    cursor.close()
    conn.close()

def delete_product(sku):
    conn = get_connection()
    cursor = conn.cursor()

    # First delete inventory entries that reference this SKU
    cursor.execute("DELETE FROM Inventory WHERE sku = %s", (sku,))

    # Then delete the product
    cursor.execute("DELETE FROM Products WHERE sku = %s", (sku,))
    
    conn.commit()
    cursor.close()
    conn.close()

# INVENTORY FUNCTIONS
def get_inventory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Inventory.inventory_id, Inventory.sku, Inventory.location, Inventory.quantity,
               Products.threshold, Products.name
        FROM Inventory
        JOIN Products ON Inventory.sku = Products.sku
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def add_inventory(sku, location, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Inventory (sku, location, quantity) VALUES (%s, %s, %s)",
                   (sku, location, quantity))
    conn.commit()
    cursor.close()
    conn.close()

def update_inventory(sku, location, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Inventory
        SET quantity = %s
        WHERE sku = %s AND location = %s
    """, (quantity, sku, location))
    conn.commit()
    cursor.close()
    conn.close()

def delete_inventory_for_sku(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Inventory WHERE sku = %s", (sku,))
    conn.commit()
    cursor.close()
    conn.close()

def get_low_stock():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.sku, p.name, i.location, i.quantity, p.threshold
        FROM Inventory i
        JOIN Products p ON i.sku = p.sku
        WHERE i.quantity < p.threshold AND i.location NOT LIKE 'Retail Hub%'
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_products_by_warehouse(location):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Inventory.sku, Products.name, Inventory.quantity
        FROM Inventory
        JOIN Products ON Inventory.sku = Products.sku
        WHERE Inventory.location = %s
    """, (location,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# LOGISTICS FUNCTIONS
def move_product(sku, origin, destination, quantity, transport_cost):
    conn = get_connection()
    cursor = conn.cursor()

    sku = sku.strip().upper()
    origin = origin.strip()
    destination = destination.strip()

    # Step 1: Check available stock
    cursor.execute("""
        SELECT quantity FROM Inventory
        WHERE sku = %s AND location = %s
    """, (sku, origin))
    result = cursor.fetchone()

    if not result:
        conn.rollback()
        cursor.close()
        conn.close()
        raise Exception("No inventory record found at origin")

    available_qty = result[0]
    if available_qty < quantity:
        conn.rollback()
        cursor.close()
        conn.close()
        raise Exception("Insufficient stock at origin")

    # Step 2: Deduct from origin
    cursor.execute("""
        UPDATE Inventory
        SET quantity = quantity - %s
        WHERE sku = %s AND location = %s
    """, (quantity, sku, origin))

    # Step 3: Add to destination
    cursor.execute("""
        SELECT quantity FROM Inventory WHERE sku = %s AND location = %s
    """, (sku, destination))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE Inventory
            SET quantity = quantity + %s
            WHERE sku = %s AND location = %s
        """, (quantity, sku, destination))
    else:
        cursor.execute("""
            INSERT INTO Inventory (sku, location, quantity)
            VALUES (%s, %s, %s)
        """, (sku, destination, quantity))

    # Step 4: Log movement
    cursor.execute("""
        INSERT INTO Logistics (sku, origin, destination, transport_cost)
        VALUES (%s, %s, %s, %s)
    """, (sku, origin, destination, transport_cost))

    conn.commit()
    cursor.close()
    conn.close()


def get_route_cost(origin, destination):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cost FROM Routes WHERE origin = %s AND destination = %s
    """, (origin, destination))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

# ORDER FUNCTIONS
def place_order(sku, quantity, customer_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Orders (sku, quantity, customer_name)
        VALUES (%s, %s, %s)
    """, (sku, quantity, customer_name))
    conn.commit()
    cursor.close()
    conn.close()

def get_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, sku, quantity, customer_name, customer_location, status
        FROM Orders
        ORDER BY order_id DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def update_order_status(order_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Orders SET status = %s WHERE order_id = %s
    """, (status, order_id))
    conn.commit()
    cursor.close()
    conn.close()

# FORECAST FUNCTIONS
def get_forecast():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sku, forecast_value, forecast_date FROM DemandForecast
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def add_forecast(sku, forecast_value, forecast_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO DemandForecast (sku, forecast_value, forecast_date)
        VALUES (%s, %s, %s)
    """, (sku, forecast_value, forecast_date))
    conn.commit()
    cursor.close()
    conn.close()

def get_inventory_for_sku(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT location, quantity FROM Inventory
        WHERE sku = %s AND quantity > 0
        ORDER BY quantity DESC
    """, (sku,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def get_cheapest_route(origin, destination):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cost FROM Routes
        WHERE origin = %s AND destination = %s
        ORDER BY cost ASC LIMIT 1
    """, (origin, destination))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def fulfill_order(order_id, sku, quantity):
    inventory_sources = get_inventory_for_sku(sku)
    for location, available_qty in inventory_sources:
        move_qty = min(quantity, available_qty)
        cost = get_cheapest_route(location, "Customer")
        if cost is None:
            continue  # Skip if no route

        move_product(sku, location, "Customer", move_qty, cost)
        quantity -= move_qty
        if quantity <= 0:
            break

def delete_order(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Orders WHERE order_id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()

def place_order(sku, quantity, customer_name, customer_location):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Orders (sku, quantity, customer_name, customer_location, status)
        VALUES (%s, %s, %s, %s, 'Pending')
    """, (sku, quantity, customer_name, customer_location))
    conn.commit()
    cursor.close()
    conn.close()

def move_order_to_customer(order_id, sku, quantity, origin, destination):
    cost_per_unit = get_route_cost(origin, destination)
    if cost_per_unit is None:
        raise Exception("No route found")
    total_cost = cost_per_unit * quantity
    move_product(sku, origin, destination, quantity, total_cost)

def get_all_warehouse_locations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT location FROM Inventory")
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_valid_origins_for_destination(destination, sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT r.origin
        FROM Routes r
        JOIN Inventory i ON r.origin = i.location
        WHERE r.destination = %s AND i.sku = %s AND i.quantity > 0
    """, (destination, sku))
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_customer_locations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT destination FROM Routes WHERE destination LIKE 'Retail Hub%'")
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_inventory_locations_for_sku(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT location FROM Inventory WHERE sku = %s", (sku,))
    results = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def get_locations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT origin FROM Routes")
    origins = [row[0] for row in cursor.fetchall() if not row[0].startswith("Retail Hub")]
    cursor.execute("SELECT DISTINCT destination FROM Routes")
    destinations = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return origins, destinations

def get_inventory_for_forecast(sku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(quantity) FROM Inventory WHERE sku = %s", (sku,))
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result or 0



