import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import select, func, desc
from db.database import SessionLocal
from db.models import Deal, Quote

st.set_page_config(page_title="Quotes", layout="wide")
st.title("Quotes (Versioned per Deal)")

with SessionLocal() as session:
    deals = session.execute(select(Deal).order_by(desc(Deal.created_at))).scalars().all()

deal_map = {f"{d.company.name} — {d.name} (Deal #{d.id})": d.id for d in deals}

st.subheader("Issue a new quote (auto-increments version)")
with st.form("add_quote", clear_on_submit=True):
    deal_key = st.selectbox("Deal*", list(deal_map.keys()) if deal_map else [])
    c1, c2, c3 = st.columns(3)
    with c1:
        date_issued = st.date_input("Date issued", value=date.today())
        amount = st.number_input("Amount", min_value=0.0, value=0.0, step=1000.0)
    with c2:
        currency = st.selectbox("Currency", ["USD", "CNY", "EUR", "GBP"])
        service_type = st.selectbox("Service type", ["Discovery", "Expression", "mRNA-LNP", "Licensing", "Protein", "Other"])
    with c3:
        status = st.selectbox("Status", ["open", "superseded", "withdrawn"])
    notes = st.text_area("Notes", height=120)

    submitted = st.form_submit_button("Add Quote")
    if submitted:
        if not deal_key:
            st.error("Deal required.")
        else:
            deal_id = deal_map[deal_key]
            with SessionLocal() as session:
                max_v = session.scalar(select(func.max(Quote.version)).where(Quote.deal_id == deal_id)) or 0
                q = Quote(
                    deal_id=deal_id,
                    version=max_v + 1,
                    date_issued=date_issued,
                    amount=amount,
                    currency=currency,
                    service_type=service_type,
                    status=status,
                    notes=notes.strip() or None,
                )
                session.add(q)
                session.commit()
            st.success(f"Quote added as v{max_v+1}.")

st.divider()
st.subheader("All quotes")

with SessionLocal() as session:
    quotes = session.execute(select(Quote).order_by(desc(Quote.created_at))).scalars().all()

rows = []
for q in quotes:
    rows.append({
        "Quote ID": q.id,
        "Deal ID": q.deal_id,
        "Deal": q.deal.name if q.deal else "",
        "Company": q.deal.company.name if q.deal and q.deal.company else "",
        "Version": q.version,
        "Issued": q.date_issued,
        "Amount": q.amount,
        "Currency": q.currency,
        "Service": q.service_type,
        "Status": q.status,
        "Notes": (q.notes or "")[:120],
    })

st.dataframe(pd.DataFrame(rows), use_container_width=True)