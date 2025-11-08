import streamlit as st
from db.queries import (
    move_product, get_route_cost, get_orders,
    update_order_status, move_order_to_customer,
    get_inventory_for_sku, get_locations  # ✅ now imported from queries
)

st.title("Logistics Simulator")

# --- Manual Movement ---
st.subheader("Manual Product Movement")

# ✅ Get filtered origins (warehouses only) and all destinations
origins, destinations = get_locations()

sku = st.text_input("SKU")
origin = st.selectbox("Origin Warehouse", origins, key="manual_origin")
destination = st.selectbox("Destination Warehouse", destinations, key="manual_dest")
quantity = st.number_input("Quantity to Move", min_value=1, key="manual_qty")

if sku and origin and destination and quantity:
    cost_per_unit = get_route_cost(origin.strip(), destination.strip())
    if cost_per_unit is not None:
        total_cost = cost_per_unit * quantity
        st.info(f"Transport Cost: ₹{total_cost:.2f}")
        if st.button("Simulate Movement"):
            try:
                move_product(sku.strip().upper(), origin.strip(), destination.strip(), quantity, total_cost)
                st.success(f"Moved {quantity} units of {sku} from {origin} to {destination}")
            except Exception as e:
                st.error(f"Movement failed: {e}")
    else:
        st.warning("⚠️ No route found between selected origin and destination.")

# --- Move Orders to Customer ---
st.subheader("Move Orders to Customer")

orders = get_orders()
pending_orders = [o for o in orders if o[5] == "Pending"]

if pending_orders:
    header = st.columns([1, 2, 1.5, 2, 2, 1])
    header[0].markdown("**Order ID**")
    header[1].markdown("**SKU**")
    header[2].markdown("**Qty**")
    header[3].markdown("**Customer**")
    header[4].markdown("**Location**")
    header[5].markdown("**Action**")

    for order in pending_orders:
        order_id, sku, qty, customer, location, status = order
        row = st.columns([1, 2, 1.5, 2, 2, 1])
        row[0].write(order_id)
        row[1].write(sku)
        row[2].write(qty)
        row[3].write(customer)
        row[4].write(location)

        # Get all warehouses with enough stock for this SKU
        inventory_sources = get_inventory_for_sku(sku.strip().upper())
        valid_origins = [loc for loc, available_qty in inventory_sources if available_qty >= qty and not loc.startswith("Retail Hub")]

        if not valid_origins:
            row[5].warning("⚠️ No warehouse has enough stock")
        else:
            selected_origin = row[5].selectbox("Origin", valid_origins, key=f"origin_{order_id}")
            route_cost = get_route_cost(selected_origin.strip(), location.strip())
            if route_cost is None:
                row[5].warning("⚠️ No route from origin to customer")
            else:
                if row[5].button("🚚 Move", key=f"move_{order_id}"):
                    try:
                        move_order_to_customer(order_id, sku.strip().upper(), qty, selected_origin.strip(), location.strip())
                        update_order_status(order_id, "Processed")
                        st.success(f"Order #{order_id} moved from {selected_origin} to {location}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to move order: {e}")
else:
    st.info("No pending orders to move.")
