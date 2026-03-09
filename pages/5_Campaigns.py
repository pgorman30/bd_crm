import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from db.database import SessionLocal
from db.models import Campaign, Company

st.set_page_config(page_title="Campaigns", layout="wide")
st.title("Campaigns (Apollo + Manual)")

with SessionLocal() as session:
    companies = session.execute(
        select(Company).order_by(Company.name)
    ).scalars().all()

    company_map = {c.name: c.id for c in companies}

st.subheader("Create campaign")
with st.form("add_campaign", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Campaign name*")
        platform = st.selectbox("Platform", ["apollo", "manual", "other"])
    with c2:
        start_date = st.date_input("Start date", value=date.today())
        end_date = st.date_input("End date", value=None)
    with c3:
        company_name = st.selectbox("Link to company (optional)", [""] + list(company_map.keys()))
        target_segment = st.text_input("Target segment")

    notes = st.text_area("Notes", height=120)
    submitted = st.form_submit_button("Add Campaign")

    if submitted:
        if not name.strip():
            st.error("Campaign name required.")
        else:
            with SessionLocal() as session:
                session.add(
                    Campaign(
                        name=name.strip(),
                        platform=platform,
                        start_date=start_date,
                        end_date=end_date,
                        company_id=company_map.get(company_name) if company_name else None,
                        target_segment=target_segment.strip() or None,
                        notes=notes.strip() or None,
                    )
                )
                session.commit()
            st.success("Campaign added.")

st.divider()
st.subheader("Campaign list")

with SessionLocal() as session:
    campaigns = session.execute(
        select(Campaign)
        .options(selectinload(Campaign.company))
        .order_by(desc(Campaign.created_at))
    ).scalars().all()

    campaign_rows = [
        {
            "ID": c.id,
            "Name": c.name,
            "Platform": c.platform,
            "Company": c.company.name if c.company else "",
            "Start": c.start_date,
            "End": c.end_date,
            "Target": c.target_segment,
            "Notes": (c.notes or "")[:120],
        }
        for c in campaigns
    ]

st.dataframe(pd.DataFrame(campaign_rows), use_container_width=True)