from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Float,
    Boolean,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    website = Column(String(255), nullable=True)
    segment = Column(String(80), nullable=True)  # Biotech / AI / CRO / etc.
    country = Column(String(80), nullable=True)
    owner = Column(String(80), nullable=True)  # BD owner
    status = Column(String(40), nullable=False, default="prospect")  # prospect/active/dormant/closed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="company", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="company", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="company", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    linkedin = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="contacts")
    activities = relationship("Activity", back_populates="contact")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)

    name = Column(String(255), nullable=False)
    platform = Column(String(40), nullable=False, default="apollo")  # apollo/manual/other
    start_date = Column(Date, nullable=False, default=date.today)
    end_date = Column(Date, nullable=True)
    target_segment = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="campaigns")
    activities = relationship("Activity", back_populates="campaign")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    stage = Column(String(40), nullable=False, default="prospecting")
    value_estimate = Column(Float, nullable=True)  # expected value (unweighted)
    probability = Column(Float, nullable=True)  # 0-1 probability
    expected_close_date = Column(Date, nullable=True)

    is_closed = Column(Boolean, default=False, nullable=False)
    closed_status = Column(String(10), nullable=True)  # won/lost
    closed_date = Column(Date, nullable=True)
    loss_reason = Column(String(255), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="deals")
    quotes = relationship("Quote", back_populates="deal", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="deal")

    __table_args__ = (
        Index("ix_deals_company_stage", "company_id", "stage"),
    )


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    # Versioning per deal
    version = Column(Integer, nullable=False, default=1)

    date_issued = Column(Date, nullable=False, default=date.today)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")

    service_type = Column(String(60), nullable=False, default="Other")
    status = Column(String(20), nullable=False, default="open")  # open/superseded/withdrawn

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    deal = relationship("Deal", back_populates="quotes")

    __table_args__ = (
        UniqueConstraint("deal_id", "version", name="uq_quote_deal_version"),
        Index("ix_quotes_deal_date", "deal_id", "date_issued"),
    )


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)

    happened_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    type = Column(String(30), nullable=False)  # email/meeting/call/linkedin/other
    outcome = Column(String(30), nullable=False, default="sent")  # sent/booked/completed/etc
    source = Column(String(30), nullable=False, default="manual")  # manual/apollo

    counts_for_kpi = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="activities")
    contact = relationship("Contact", back_populates="activities")
    deal = relationship("Deal", back_populates="activities")
    campaign = relationship("Campaign", back_populates="activities")

    __table_args__ = (
        Index("ix_activities_happened_at", "happened_at"),
        Index("ix_activities_type_outcome", "type", "outcome"),
    )