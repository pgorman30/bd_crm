import streamlit as st
from sqlalchemy import text
from db.database import DB_PATH, SessionLocal
from db.migrate import main as migrate_main

st.set_page_config(page_title="BD CRM", layout="wide")

# Ensure DB exists
migrate_main()

st.title("BD CRM (Local-ish, OneDrive-sync)")

st.caption(f"Database: {DB_PATH}")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("Rule: don't run this app on both computers at the same time (SQLite + OneDrive).")
with col2:
    st.success("Week definition: Monday–Sunday.")
with col3:
    st.warning("Backups recommended (Dashboard page can trigger backups).")

st.markdown("Use the left sidebar pages to log Activity, manage Deals/Quotes, track Campaigns, and view the Dashboard.")

# simple health check
with SessionLocal() as session:
    session.execute(text("SELECT 1"))