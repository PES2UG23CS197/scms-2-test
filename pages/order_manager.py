import streamlit as st
from db.queries import (
    place_order, get_orders, update_order_status,
    fulfill_order, delete_order, get_customer_locations
)

st.title("Order Manager")

# --- Place Custom Order ---
st.subheader("Place Custom Order")
sku = st.text_input("SKU")
quantity = st.number_input("Quantity", min_value=1)
customer_name = st.text_input("Customer Name")

# Dropdown for customer location
locations = get_customer_locations()
customer_location = st.selectbox("Customer Location", locations)

if st.button("Place Order"):
    try:
        place_order(sku, quantity, customer_name, customer_location)
        st.success(f"Order placed for {quantity} units of {sku} by {customer_name} to {customer_location}")
    except Exception as e:
        st.error(f"Failed to place order: {e}")

# --- Display All Orders ---
st.subheader("All Orders")
orders = get_orders()

if orders:
    st.markdown("### 📦 Current Orders")

    # Table Header
    header = st.columns([1, 2, 1.5, 2, 2, 1.5, 1.5])
    header[0].markdown("**Order ID**")
    header[1].markdown("**SKU**")
    header[2].markdown("**Qty**")
    header[3].markdown("**Customer**")
    header[4].markdown("**Location**")
    header[5].markdown("**Status**")
    header[6].markdown("**Actions**")

    for order in orders:
        order_id, sku, qty, customer, location, status = order
        row = st.columns([1, 2, 1.5, 2, 2, 1.5, 1.5])
        row[0].write(order_id)
        row[1].write(sku)
        row[2].write(qty)
        row[3].write(customer)
        row[4].write(location)
        row[5].write(status)

        # Buttons side-by-side
        process_key = f"process_{order_id}"
        delete_key = f"delete_{order_id}"

        if status == "Pending":
            btns = row[6].columns(2)
            if btns[0].button("🟢", key=process_key):
                try:
                    fulfill_order(order_id, sku, qty)
                    update_order_status(order_id, "Processed")
                    st.success(f"Order #{order_id} processed and inventory moved to {location}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to process order: {e}")
            if btns[1].button("🗑️", key=delete_key):
                try:
                    delete_order(order_id)
                    st.success(f"Order #{order_id} deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete order: {e}")
        else:
            row[6].markdown("✅")
else:
    st.info("No orders found.")
