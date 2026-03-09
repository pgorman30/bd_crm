# BD CRM (Local-ish, OneDrive-sync)

## What it does
- Track activities (emails, meetings, calls, etc.)
- Manage companies/contacts
- Manage deals (canonical close = Deal won/lost)
- Issue quotes with versioning per deal
- Dashboard KPIs:
  - emails sent
  - meetings booked
  - quotes issued
  - deals closed
  - quote close rate
  - weighted + unweighted pipeline

## Sync
The database is a single SQLite file stored in OneDrive (default path):
- ~/OneDrive/BD_CRM/data/bd_crm.sqlite

### Important rule
Do not run the app on both computers at the same time.

## Install & run
```bash
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows
.venv\Scripts\activate

pip install -r requirements.txt
python db/migrate.py
streamlit run app.py