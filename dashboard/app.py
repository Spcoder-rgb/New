import streamlit as st

st.set_page_config(page_title="University Food Inventory Dashboard", layout="wide")

st.title("University Food Inventory Dashboard")

section = st.sidebar.selectbox(
    "Section",
    [
        "Overview",
        "Outlets & Universities",
        "Inventory & Batches",
        "Analytics",
        "Forecasting",
    ],
)

if section == "Overview":
    st.markdown("This dashboard visualizes sales, stock, EOQ, reorder points, and expiry alerts.")

elif section == "Outlets & Universities":
    st.markdown("Manage and compare outlets across universities. (To be implemented)")

elif section == "Inventory & Batches":
    st.markdown("View items, batches, stock levels, and wastage. (To be implemented)")

elif section == "Analytics":
    st.markdown("EOQ, reorder points, near-expiry alerts, supplier reliability. (To be implemented)")

elif section == "Forecasting":
    st.markdown("Demand forecasting with ARIMA/Prophet. (To be implemented)")