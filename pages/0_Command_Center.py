import streamlit as st
import pandas as pd
from datetime import date, datetime
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import selectinload
from db.database import SessionLocal
from db.models import Activity, Deal, Quote
from utils.kpi import compute_kpis, week_bounds

st.set_page_config(page_title="Command Center", layout="wide")
st.title("BD Command Center")

today = date.today()
week_start, week_end = week_bounds(today)

with SessionLocal() as session:
    k = compute_kpis(session, week_start, week_end)

    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    activities_today = session.scalar(
        select(func.count(Activity.id)).where(
            and_(
                Activity.happened_at >= today_start,
                Activity.happened_at <= today_end,
            )
        )
    ) or 0

    followup_deals = session.execute(
        select(Deal)
        .options(selectinload(Deal.company))
        .where(Deal.is_closed.is_(False))
        .order_by(Deal.expected_close_date.asc().nulls_last(), desc(Deal.created_at))
        .limit(10)
    ).scalars().all()

    recent_quotes = session.execute(
        select(Quote)
        .options(
            selectinload(Quote.deal).selectinload(Deal.company)
        )
        .order_by(desc(Quote.date_issued))
        .limit(10)
    ).scalars().all()

    recent_activity = session.execute(
        select(Activity)
        .options(
            selectinload(Activity.company),
            selectinload(Activity.deal),
            selectinload(Activity.campaign),
        )
        .order_by(desc(Activity.happened_at))
        .limit(10)
    ).scalars().all()

    followup_rows = []
    for d in followup_deals:
        followup_rows.append({
            "Deal ID": d.id,
            "Company": d.company.name if d.company else "",
            "Deal": d.name,
            "Stage": d.stage,
            "Expected Close": d.expected_close_date,
            "Value": d.value_estimate,
            "Weighted": (d.value_estimate or 0) * (d.probability or 0),
        })

    quote_rows = []
    for q in recent_quotes:
        quote_rows.append({
            "Quote ID": q.id,
            "Company": q.deal.company.name if q.deal and q.deal.company else "",
            "Deal": q.deal.name if q.deal else "",
            "Version": q.version,
            "Issued": q.date_issued,
            "Amount": q.amount,
            "Status": q.status,
        })

    activity_rows = []
    for a in recent_activity:
        activity_rows.append({
            "When": a.happened_at,
            "Type": a.type,
            "Outcome": a.outcome,
            "Company": a.company.name if a.company else "",
            "Deal": a.deal.name if a.deal else "",
            "Notes": (a.notes or "")[:100],
        })

st.subheader("This Week")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Emails Sent", k.emails_sent)
c2.metric("Meetings Booked", k.meetings_booked)
c3.metric("Quotes Issued", k.quotes_issued)
c4.metric("Deals Closed", k.deals_closed)
c5.metric("Quote Close Rate", f"{k.quote_close_rate * 100:.1f}%")

st.divider()

c6, c7, c8 = st.columns(3)
c6.metric("Open Pipeline", f"${k.pipeline_unweighted:,.0f}")
c7.metric("Weighted Pipeline", f"${k.pipeline_weighted:,.0f}")
c8.metric("Activities Today", activities_today)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Deals Needing Follow-Up")
    st.dataframe(pd.DataFrame(followup_rows), use_container_width=True)

with right:
    st.subheader("Recent Quotes")
    st.dataframe(pd.DataFrame(quote_rows), use_container_width=True)

st.divider()

st.subheader("Recent Activity")
st.dataframe(pd.DataFrame(activity_rows), use_container_width=True)