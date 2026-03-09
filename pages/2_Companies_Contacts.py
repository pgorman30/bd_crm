import streamlit as st
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from db.database import SessionLocal
from db.models import Company, Contact

st.set_page_config(page_title="Companies & Contacts", layout="wide")
st.title("Companies & Contacts")

tab1, tab2 = st.tabs(["Companies", "Contacts"])

with tab1:
    st.subheader("Add / View Companies")

    with st.form("add_company", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Company name*")
            website = st.text_input("Website")
        with c2:
            segment = st.text_input("Segment (Biotech/AI/CRO/etc)")
            country = st.text_input("Country")
        with c3:
            owner = st.text_input("Owner (you/team)")
            status = st.selectbox("Status", ["prospect", "active", "dormant", "closed"])

        submitted = st.form_submit_button("Add Company")
        if submitted:
            if not name.strip():
                st.error("Company name is required.")
            else:
                with SessionLocal() as session:
                    session.add(
                        Company(
                            name=name.strip(),
                            website=website.strip() or None,
                            segment=segment.strip() or None,
                            country=country.strip() or None,
                            owner=owner.strip() or None,
                            status=status,
                        )
                    )
                    session.commit()
                st.success("Company added.")

    with SessionLocal() as session:
        companies = session.execute(
            select(Company).order_by(Company.name)
        ).scalars().all()

        company_rows = [
            {
                "ID": c.id,
                "Name": c.name,
                "Website": c.website,
                "Segment": c.segment,
                "Country": c.country,
                "Owner": c.owner,
                "Status": c.status,
            }
            for c in companies
        ]

    st.dataframe(
        pd.DataFrame(company_rows),
        use_container_width=True
    )

with tab2:
    st.subheader("Add / View Contacts")

    with SessionLocal() as session:
        companies = session.execute(
            select(Company).order_by(Company.name)
        ).scalars().all()

    company_map = {c.name: c.id for c in companies}

    with st.form("add_contact", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            company_name = st.selectbox("Company*", list(company_map.keys()) if company_map else [])
            contact_name = st.text_input("Contact name*")
            title = st.text_input("Title")
        with c2:
            email = st.text_input("Email")
            linkedin = st.text_input("LinkedIn")

        notes = st.text_area("Notes", height=100)

        submitted = st.form_submit_button("Add Contact")
        if submitted:
            if not company_name:
                st.error("Company is required.")
            elif not contact_name.strip():
                st.error("Contact name is required.")
            else:
                with SessionLocal() as session:
                    session.add(
                        Contact(
                            company_id=company_map[company_name],
                            name=contact_name.strip(),
                            title=title.strip() or None,
                            email=email.strip() or None,
                            linkedin=linkedin.strip() or None,
                            notes=notes.strip() or None,
                        )
                    )
                    session.commit()
                st.success("Contact added.")

    with SessionLocal() as session:
        contacts = session.execute(
            select(Contact).options(selectinload(Contact.company)).order_by(Contact.name)
        ).scalars().all()

        contact_rows = [
            {
                "ID": c.id,
                "Company": c.company.name if c.company else "",
                "Name": c.name,
                "Title": c.title,
                "Email": c.email,
                "LinkedIn": c.linkedin,
                "Notes": (c.notes or "")[:120],
            }
            for c in contacts
        ]

    st.dataframe(
        pd.DataFrame(contact_rows),
        use_container_width=True
    )