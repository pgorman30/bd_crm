import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import select, desc
from db.database import SessionLocal
from db.models import Activity, Company, Deal, Campaign

st.set_page_config(page_title="Activity", layout="wide")
st.title("Activity Log")

with SessionLocal() as session:
    companies = session.execute(select(Company).order_by(Company.name)).scalars().all()
    deals = session.execute(select(Deal).order_by(desc(Deal.created_at))).scalars().all()
    campaigns = session.execute(select(Campaign).order_by(desc(Campaign.created_at))).scalars().all()

company_map = {c.name: c.id for c in companies}
deal_map = {f"{d.company.name} — {d.name} (#{d.id})": d.id for d in deals}
campaign_map = {f"{c.name} ({c.platform}) (#{c.id})": c.id for c in campaigns}


def quick_log(activity_type: str, outcome: str):
    with SessionLocal() as session:
        a = Activity(
            happened_at=datetime.now(),
            type=activity_type,
            outcome=outcome,
            source="manual",
            counts_for_kpi=True,
            notes=f"Quick log: {activity_type} / {outcome}",
        )
        session.add(a)
        session.commit()


st.subheader("Quick Log")

q1, q2, q3, q4 = st.columns(4)

with q1:
    if st.button("Log Email Sent", use_container_width=True):
        quick_log("email", "sent")
        st.success("Email logged.")

with q2:
    if st.button("Log Meeting Booked", use_container_width=True):
        quick_log("meeting", "booked")
        st.success("Meeting logged.")

with q3:
    if st.button("Log Call", use_container_width=True):
        quick_log("call", "completed")
        st.success("Call logged.")

with q4:
    if st.button("Log Follow-Up", use_container_width=True):
        quick_log("email", "follow_up")
        st.success("Follow-up logged.")

st.divider()
st.subheader("Detailed Activity Entry")

with st.form("add_activity", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        company_name = st.selectbox("Company (optional)", [""] + list(company_map.keys()))
    with c2:
        activity_type = st.selectbox("Type", ["email", "meeting", "call", "linkedin", "conference", "other"])
    with c3:
        outcome = st.selectbox("Outcome", ["sent", "booked", "completed", "no_response", "follow_up", "other"])
    with c4:
        source = st.selectbox("Source", ["manual", "apollo", "other"])

    c5, c6, c7 = st.columns(3)
    with c5:
        date_val = st.date_input("Date")
        time_val = st.time_input("Time")
        happened_at = datetime.combine(date_val, time_val)

    with c6:
        deal_key = st.selectbox("Link to Deal (optional)", [""] + list(deal_map.keys()))

    with c7:
        campaign_key = st.selectbox("Link to Campaign (optional)", [""] + list(campaign_map.keys()))

    counts_for_kpi = st.checkbox("Counts for KPI", value=True)
    notes = st.text_area("Notes", height=120)

    submitted = st.form_submit_button("Add Activity")

    if submitted:
        with SessionLocal() as session:
            a = Activity(
                company_id=company_map.get(company_name) if company_name else None,
                deal_id=deal_map.get(deal_key) if deal_key else None,
                campaign_id=campaign_map.get(campaign_key) if campaign_key else None,
                happened_at=happened_at,
                type=activity_type,
                outcome=outcome,
                source=source,
                counts_for_kpi=counts_for_kpi,
                notes=notes.strip() if notes else None,
            )
            session.add(a)
            session.commit()
        st.success("Activity added.")

st.divider()
st.subheader("Recent activity (last 200)")

with SessionLocal() as session:
    rows = session.execute(
        select(Activity).order_by(desc(Activity.happened_at)).limit(200)
    ).scalars().all()

data = []
for r in rows:
    data.append(
        {
            "When": r.happened_at,
            "Type": r.type,
            "Outcome": r.outcome,
            "Source": r.source,
            "Company": r.company.name if r.company else "",
            "Deal": f"{r.deal.name}" if r.deal else "",
            "Campaign": f"{r.campaign.name}" if r.campaign else "",
            "Counts KPI": r.counts_for_kpi,
            "Notes": (r.notes or "")[:120],
        }
    )

st.dataframe(pd.DataFrame(data), use_container_width=True)