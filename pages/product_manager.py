import streamlit as st
import pandas as pd
from db.queries import (
    get_all_products, add_product, update_product, delete_product,
    add_inventory, update_inventory, get_all_warehouse_locations,
    delete_inventory_for_sku, get_inventory_locations_for_sku
)

st.title("Product Manager")

# --- Form State Reset ---
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

if st.session_state.form_submitted:
    st.session_state.update({
        "sku": "",
        "name": "",
        "desc": "",
        "threshold": 1,
        "selected_locations": [],
        "form_submitted": False
    })

# --- Step 1: Product Details and Warehouse Selection ---
st.subheader("Add or Update Product")

with st.form("product_info_form"):
    st.text_input("SKU", key="sku")
    st.text_input("Name", key="name")
    st.text_input("Description", key="desc")
    st.number_input("Threshold", min_value=1, key="threshold")

    st.markdown("**Assign to Warehouses**")
    warehouse_locations = [loc for loc in get_all_warehouse_locations() if not loc.startswith("Retail Hub")]
    selected_locations = st.multiselect("Select Warehouses", warehouse_locations, key="selected_locations")

    proceed = st.form_submit_button("Next ➡️")

# --- Step 2: Quantity Assignment ---
if selected_locations:
    st.subheader("Enter Quantity for Each Warehouse")
    with st.form("quantity_form"):
        warehouse_quantities = {}
        for loc in selected_locations:
            warehouse_quantities[loc] = st.number_input(f"Quantity at {loc}", min_value=0, key=f"qty_{loc}")

        col1, col2 = st.columns([1, 1])
        with col1:
            add_clicked = st.form_submit_button("➕ Add Product")
        with col2:
            update_clicked = st.form_submit_button("✏️ Update Product")

        # --- Action Logic ---
        if add_clicked:
            try:
                add_product(
                    st.session_state.sku.strip().upper(),
                    st.session_state.name,
                    st.session_state.desc,
                    st.session_state.threshold
                )
                for loc in selected_locations:
                    qty = warehouse_quantities[loc]
                    if qty > 0:
                        add_inventory(st.session_state.sku.strip().upper(), loc.strip(), qty)
                st.success(f"Product '{st.session_state.sku}' added to selected warehouses.")
                st.session_state.form_submitted = True
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add product: {e}")

        if update_clicked:
            try:
                update_product(
                    st.session_state.sku.strip().upper(),
                    st.session_state.name,
                    st.session_state.desc,
                    st.session_state.threshold
                )
                existing_locations = get_inventory_locations_for_sku(st.session_state.sku.strip().upper())

                for loc in selected_locations:
                    qty = warehouse_quantities[loc]
                    if loc in existing_locations:
                        update_inventory(st.session_state.sku.strip().upper(), loc.strip(), qty)
                    else:
                        add_inventory(st.session_state.sku.strip().upper(), loc.strip(), qty)

            except Exception as e:
                st.error(f"Failed to update product: {e}")

# --- Product List ---
st.subheader("All Products")

products = get_all_products()

if products:
    header = st.columns([1.5, 2.5, 3, 1.5, 1])
    header[0].markdown("**SKU**")
    header[1].markdown("**Name**")
    header[2].markdown("**Description**")
    header[3].markdown("**Threshold**")
    header[4].markdown("**Delete**")

    for p in products:
        row = st.columns([1.5, 2.5, 3, 1.5, 1])
        row[0].write(p[0])  # SKU
        row[1].write(p[1])  # Name
        row[2].write(p[2])  # Description
        row[3].write(p[3])  # Threshold
        if row[4].button("🗑️", key=f"delete_{p[0]}"):
            delete_product(p[0])
            st.warning(f"Deleted {p[0]}")
            st.rerun()
else:
    st.info("No products found.")
