# HireFlow ATS: Mini Applicant Tracking System

A clean, lightweight ATS to manage candidates, hiring stages, search and dashboard metrics.
Built with **Python, Streamlit, SQLite and Pandas**.

## Features
- **Overview dashboard:** KPI cards, hiring funnel, applications by source, recent candidates and activity, and a "needs attention" list
- **Candidates:** search (name, email, skills, position), filter by stage and position, sort, download CSV
- **Candidate profile:** view details, edit, move stage, delete (with confirmation) and per-candidate history
- **Pipeline board:** one column per stage; advance, go back, reject or reopen candidates with one click
- **Add candidate:** validated form (email format, duplicate email, phone, experience)
- **Public application form:** share `/?apply=1&source=LinkedIn` links, one per website; applications arrive tagged with their source
- **Bulk import:** CSV, Excel or a Google Sheet link. Column names from other sites (Full Name, Email ID, Job Title, Applied On…) are mapped
  automatically, messy values are cleaned, duplicate emails are skipped. 400 applications import in under a second
- **Export:** download all candidates as CSV
- **Activity log:** every add, edit, stage change and delete is recorded
- 12 fictional sample candidates are seeded on first run (delete them under Import / Export → Danger zone)
- 36 automated tests (database logic + every page of the UI)

## Project structure
```
app.py            Streamlit UI (5 pages)
db.py             SQLite database layer + validation + metrics
tests/            pytest tests (database and UI smoke tests)
.streamlit/       Theme configuration
.github/workflows GitHub Actions: runs the tests on every push
```

## Run locally (Windows / macOS / Linux)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```
Open http://localhost:8501. The database file `ats.db` is created automatically on first run.

## Run the tests
```bash
pip install pytest
python -m pytest -q
```

## Database
SQLite, stored in a local `ats.db` file. Tables:
- `candidates`: id, name, email (unique), phone, role, skills, experience, source, stage, applied_date, notes
- `activity`: id, timestamp, candidate_id, candidate, action, detail

Databases created by the earlier version of the app are upgraded automatically (new columns are added).
To start fresh, stop the app and delete `ats.db`, or use **Import / Export → Reset demo data**.

**Persistence note:** on Streamlit Community Cloud the file system is not permanent. Data you add can reset when the app
restarts or is redeployed, and the sample data is restored. This is fine for a demo. For production, use a managed
PostgreSQL database (for example Supabase) instead of SQLite.

## Deploy to Streamlit Community Cloud
1. Push this folder to a **public** GitHub repository.
2. Go to https://share.streamlit.io, sign in with GitHub and choose **Create app**.
3. Select the repository and branch, set the main file path to `app.py` and click **Deploy**.
4. Open the public URL in a private/incognito window and test it.

## Getting applications from many websites
Job sites such as LinkedIn or Naukri do not give free live feeds, so HireFlow supports the three practical routes:
1. **Application link per site:** post a link like `https://YOUR-APP.streamlit.app/?apply=1&source=Naukri` in each job listing.
2. **Spreadsheet import:** export applicants from a site (or collect them with a Google Form) and upload the file or paste the sheet link.
3. **Manual entry:** for referrals and walk-ins.

## Notes
The recruiter dashboard has no login. Add authentication before using it with real candidate data.
