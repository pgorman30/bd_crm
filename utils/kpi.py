from __future__ import annotations

from datetime import datetime, date, timedelta
from dataclasses import dataclass
from sqlalchemy import select, func, and_
from db.models import Activity, Deal, Quote

# Week is Monday-Sunday
def week_bounds(d: date) -> tuple[date, date]:
    start = d - timedelta(days=d.weekday())  # Monday
    end = start + timedelta(days=6)          # Sunday
    return start, end

def month_bounds(d: date) -> tuple[date, date]:
    start = d.replace(day=1)
    # next month:
    if start.month == 12:
        next_m = date(start.year + 1, 1, 1)
    else:
        next_m = date(start.year, start.month + 1, 1)
    end = next_m - timedelta(days=1)
    return start, end

def quarter_bounds(d: date) -> tuple[date, date]:
    q = (d.month - 1) // 3 + 1
    start_month = 3 * (q - 1) + 1
    start = date(d.year, start_month, 1)
    if start_month == 10:
        next_q = date(d.year + 1, 1, 1)
    else:
        next_q = date(d.year, start_month + 3, 1)
    end = next_q - timedelta(days=1)
    return start, end

@dataclass
class KpiResult:
    emails_sent: int
    meetings_booked: int
    quotes_issued: int
    deals_closed: int
    quote_close_rate: float
    pipeline_unweighted: float
    pipeline_weighted: float

def _dt_range(start_d: date, end_d: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start_d, datetime.min.time())
    end_dt = datetime.combine(end_d, datetime.max.time())
    return start_dt, end_dt

def compute_kpis(session, start_d: date, end_d: date) -> KpiResult:
    start_dt, end_dt = _dt_range(start_d, end_d)

    emails_sent = session.scalar(
        select(func.count(Activity.id)).where(
            and_(
                Activity.happened_at >= start_dt,
                Activity.happened_at <= end_dt,
                Activity.type == "email",
                Activity.outcome == "sent",
                Activity.counts_for_kpi.is_(True),
            )
        )
    ) or 0

    meetings_booked = session.scalar(
        select(func.count(Activity.id)).where(
            and_(
                Activity.happened_at >= start_dt,
                Activity.happened_at <= end_dt,
                Activity.type == "meeting",
                Activity.outcome == "booked",
                Activity.counts_for_kpi.is_(True),
            )
        )
    ) or 0

    quotes_issued = session.scalar(
        select(func.count(Quote.id)).where(
            and_(
                Quote.date_issued >= start_d,
                Quote.date_issued <= end_d,
            )
        )
    ) or 0

    deals_closed = session.scalar(
        select(func.count(Deal.id)).where(
            and_(
                Deal.is_closed.is_(True),
                Deal.closed_date.isnot(None),
                Deal.closed_date >= start_d,
                Deal.closed_date <= end_d,
            )
        )
    ) or 0

    # Quote close rate derived from deals closed won/lost (canonical is Deal)
    won = session.scalar(
        select(func.count(Deal.id)).where(
            and_(
                Deal.is_closed.is_(True),
                Deal.closed_date.isnot(None),
                Deal.closed_date >= start_d,
                Deal.closed_date <= end_d,
                Deal.closed_status == "won",
            )
        )
    ) or 0

    lost = session.scalar(
        select(func.count(Deal.id)).where(
            and_(
                Deal.is_closed.is_(True),
                Deal.closed_date.isnot(None),
                Deal.closed_date >= start_d,
                Deal.closed_date <= end_d,
                Deal.closed_status == "lost",
            )
        )
    ) or 0

    denom = won + lost
    quote_close_rate = (won / denom) if denom else 0.0

    # Pipeline: open deals only
    pipeline_unweighted = session.scalar(
        select(func.coalesce(func.sum(Deal.value_estimate), 0.0)).where(Deal.is_closed.is_(False))
    ) or 0.0

    # Weighted: value_estimate * probability (defaults to 0 if missing)
    pipeline_weighted = session.scalar(
        select(
            func.coalesce(
                func.sum(
                    func.coalesce(Deal.value_estimate, 0.0) * func.coalesce(Deal.probability, 0.0)
                ),
                0.0,
            )
        ).where(Deal.is_closed.is_(False))
    ) or 0.0

    return KpiResult(
        emails_sent=emails_sent,
        meetings_booked=meetings_booked,
        quotes_issued=quotes_issued,
        deals_closed=deals_closed,
        quote_close_rate=quote_close_rate,
        pipeline_unweighted=float(pipeline_unweighted),
        pipeline_weighted=float(pipeline_weighted),
    )