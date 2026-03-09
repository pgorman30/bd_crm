import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from db.database import SessionLocal
from db.models import Company, Deal

st.set_page_config(page_title="Deals", layout="wide")
st.title("Deals")

with SessionLocal() as session:
    companies = session.execute(
        select(Company).order_by(Company.name)
    ).scalars().all()

company_map = {c.name: c.id for c in companies}

st.subheader("Add Deal")
with st.form("add_deal", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        company_name = st.selectbox("Company*", list(company_map.keys()) if company_map else [])
        deal_name = st.text_input("Deal name*")
        stage = st.selectbox("Stage", ["prospecting", "intro", "qualified", "proposal", "negotiation"])
    with c2:
        value_estimate = st.number_input("Value estimate (unweighted)", min_value=0.0, value=0.0, step=1000.0)
        probability = st.slider("Probability", 0.0, 1.0, 0.25, 0.01)
        expected_close = st.date_input("Expected close date", value=None)
    with c3:
        notes = st.text_area("Notes", height=120)

    submitted = st.form_submit_button("Add Deal")
    if submitted:
        if not company_name:
            st.error("Company is required.")
        elif not deal_name.strip():
            st.error("Deal name required.")
        else:
            with SessionLocal() as session:
                session.add(
                    Deal(
                        company_id=company_map[company_name],
                        name=deal_name.strip(),
                        stage=stage,
                        value_estimate=value_estimate,
                        probability=probability,
                        expected_close_date=expected_close,
                        notes=notes.strip() or None,
                    )
                )
                session.commit()
            st.success("Deal added.")

st.divider()
st.subheader("Manage Deals")

with SessionLocal() as session:
    deals = session.execute(
        select(Deal)
        .options(selectinload(Deal.company))
        .order_by(desc(Deal.created_at))
    ).scalars().all()

    deal_rows = []
    for d in deals:
        deal_rows.append({
            "Deal ID": d.id,
            "Company": d.company.name if d.company else "",
            "Deal": d.name,
            "Stage": d.stage,
            "Value": d.value_estimate,
            "Prob": d.probability,
            "Weighted": (d.value_estimate or 0) * (d.probability or 0),
            "Expected Close": d.expected_close_date,
            "Closed?": d.is_closed,
            "Closed Status": d.closed_status,
            "Closed Date": d.closed_date,
        })

st.dataframe(pd.DataFrame(deal_rows), use_container_width=True)

st.markdown("### Close / Update a deal")
deal_ids = [d.id for d in deals]
selected_id = st.selectbox("Select Deal ID", deal_ids if deal_ids else [])

if selected_id:
    with SessionLocal() as session:
        d = session.execute(
            select(Deal)
            .options(selectinload(Deal.company))
            .where(Deal.id == selected_id)
        ).scalar_one()

        st.write(f"**{d.company.name if d.company else ''} — {d.name}**")

        stage_options = ["prospecting", "intro", "qualified", "proposal", "negotiation", "won", "lost"]
        closed_status_options = ["", "won", "lost"]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            new_stage = st.selectbox(
                "Stage",
                stage_options,
                index=stage_options.index(d.stage if d.stage in stage_options else "prospecting")
            )
        with c2:
            new_value = st.number_input("Value", min_value=0.0, value=float(d.value_estimate or 0.0), step=1000.0)
        with c3:
            new_prob = st.slider("Prob", 0.0, 1.0, float(d.probability or 0.0), 0.01)
        with c4:
            new_expected = st.date_input("Expected close", value=d.expected_close_date)

        close_toggle = st.checkbox("Mark as closed", value=bool(d.is_closed))
        closed_status = st.selectbox(
            "Closed status",
            closed_status_options,
            index=closed_status_options.index(d.closed_status or "")
        )
        closed_date = st.date_input("Closed date", value=d.closed_date)
        loss_reason = st.text_input("Loss reason (if lost)", value=d.loss_reason or "")

        notes = st.text_area("Notes", value=d.notes or "", height=120)

        if st.button("Save deal changes"):
            d.stage = new_stage
            d.value_estimate = new_value
            d.probability = new_prob
            d.expected_close_date = new_expected

            d.is_closed = close_toggle
            if close_toggle:
                d.closed_status = closed_status or None
                d.closed_date = closed_date or date.today()
                d.loss_reason = (loss_reason.strip() or None) if closed_status == "lost" else None
            else:
                d.closed_status = None
                d.closed_date = None
                d.loss_reason = None

            d.notes = notes.strip() or None
            session.commit()
            st.success("Saved.")