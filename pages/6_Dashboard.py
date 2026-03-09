import streamlit as st
from datetime import date
from db.database import SessionLocal, DB_PATH
from utils.kpi import compute_kpis, week_bounds, month_bounds, quarter_bounds
from utils.backup import backup_sqlite
from pathlib import Path

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("KPI Dashboard")

period = st.radio("Period", ["Week", "Month", "Quarter"], horizontal=True, index=0)
today = date.today()

if period == "Week":
    start_d, end_d = week_bounds(today)
elif period == "Month":
    start_d, end_d = month_bounds(today)
else:
    start_d, end_d = quarter_bounds(today)

st.caption(f"Period: {start_d} → {end_d} (Mon–Sun week logic)")

with SessionLocal() as session:
    k = compute_kpis(session, start_d, end_d)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Emails sent", k.emails_sent)
c2.metric("Meetings booked", k.meetings_booked)
c3.metric("Quotes issued", k.quotes_issued)
c4.metric("Deals closed", k.deals_closed)
c5.metric("Quote close rate", f"{k.quote_close_rate*100:.1f}%")

st.divider()

p1, p2 = st.columns(2)
p1.metric("Open pipeline (unweighted)", f"${k.pipeline_unweighted:,.0f}")
p2.metric("Open pipeline (weighted)", f"${k.pipeline_weighted:,.0f}")

st.divider()
st.subheader("Backup")
backup_dir = Path(DB_PATH).parent / "backups"
if st.button("Create backup now"):
    dst = backup_sqlite(DB_PATH, backup_dir)
    st.success(f"Backup created: {dst}")