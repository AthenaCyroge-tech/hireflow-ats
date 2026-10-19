"""Database layer for HireFlow ATS (SQLite).

All reads/writes go through this module so the UI stays simple and the
logic can be unit-tested without Streamlit.
"""
from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

DEFAULT_DB = Path(__file__).with_name("ats.db")

STAGES = ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"]
ACTIVE = ["Applied", "Screening", "Interview", "Offer"]
SOURCES = ["Career site", "LinkedIn", "Referral", "Job board", "Campus", "Other"]
FIELDS = ["name", "email", "phone", "role", "skills", "experience",
          "source", "stage", "applied_date", "notes"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# (name, email, phone, role, skills, years, source, stage, days_ago, notes)
SAMPLE = [
    ("Aarav Sharma", "aarav.sharma@example.com", "+91 90000 00001", "Python Developer", "Python, Django, PostgreSQL", 2, "LinkedIn", "Applied", 1, "Strong Python fundamentals"),
    ("Priya Nair", "priya.nair@example.com", "+91 90000 00002", "Frontend Developer", "React, TypeScript, CSS", 3, "Referral", "Interview", 6, "Technical round pending"),
    ("Ishaan Mehta", "ishaan.mehta@example.com", "+91 90000 00003", "Data Analyst", "SQL, Python, Power BI", 1, "Career site", "Screening", 3, "Analytical project experience"),
    ("Ananya Rao", "ananya.rao@example.com", "+91 90000 00004", "Backend Developer", "Java, Spring Boot, AWS", 4, "LinkedIn", "Offer", 12, "Offer discussion in progress"),
    ("Kabir Das", "kabir.das@example.com", "+91 90000 00005", "Backend Developer", "Python, FastAPI, Docker", 2, "Referral", "Hired", 20, "Offer accepted"),
    ("Meera Iyer", "meera.iyer@example.com", "+91 90000 00006", "UI/UX Designer", "Figma, UX Research, Prototyping", 3, "Job board", "Applied", 9, "Review case study"),
    ("Rohan Verma", "rohan.verma@example.com", "+91 90000 00007", "Full Stack Developer", "Node.js, React, MongoDB", 2, "Job board", "Rejected", 15, "Role requirements mismatch"),
    ("Zoya Khan", "zoya.khan@example.com", "+91 90000 00008", "Data Analyst", "Excel, SQL, Tableau", 2, "Campus", "Interview", 8, "Recruiter screen completed"),
    ("Vihaan Reddy", "vihaan.reddy@example.com", "+91 90000 00009", "Full Stack Developer", "React, Node.js, PostgreSQL", 1, "Campus", "Screening", 8, "Portfolio looks promising"),
    ("Diya Menon", "diya.menon@example.com", "+91 90000 00010", "Python Developer", "Python, Flask, SQL", 3, "LinkedIn", "Offer", 14, "Awaiting salary confirmation"),
    ("Arjun Pillai", "arjun.pillai@example.com", "+91 90000 00011", "Frontend Developer", "Vue, JavaScript, Tailwind", 2, "Career site", "Applied", 2, "Resume received"),
    ("Sara Thomas", "sara.thomas@example.com", "+91 90000 00012", "UI/UX Designer", "Figma, Wireframing, User Research", 4, "Referral", "Hired", 25, "Joined design team"),
]


# ---------------------------------------------------------------- connection
def db_path() -> Path:
    return Path(os.environ.get("ATS_DB_PATH", DEFAULT_DB))


@contextmanager
def connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _log(conn, cid, name, action, detail="", ts=None):
    conn.execute(
        "INSERT INTO activity(ts, candidate_id, candidate, action, detail) VALUES(?,?,?,?,?)",
        (ts or datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cid, name, action, detail),
    )


def _seed(conn):
    today = date.today()
    for (name, email, phone, role, skills, exp, source, stage, ago, notes) in SAMPLE:
        applied = (today - timedelta(days=ago)).isoformat()
        cur = conn.execute(
            """INSERT INTO candidates(name,email,phone,role,skills,experience,source,stage,applied_date,notes)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (name, email, phone, role, skills, exp, source, stage, applied, notes),
        )
        _log(conn, cur.lastrowid, name, "Candidate added", f"Source: {source}", ts=f"{applied} 10:00:00")


def init_db(seed: bool = True) -> None:
    """Create tables (and upgrade older databases) on first run."""
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS candidates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL,
            skills TEXT NOT NULL DEFAULT '',
            experience INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'Other',
            stage TEXT NOT NULL DEFAULT 'Applied',
            applied_date TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS activity(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            candidate_id INTEGER,
            candidate TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '')""")
        # upgrade databases created by the first version of the app
        cols = {r["name"] for r in c.execute("PRAGMA table_info(candidates)")}
        if "phone" not in cols:
            c.execute("ALTER TABLE candidates ADD COLUMN phone TEXT NOT NULL DEFAULT ''")
        if "source" not in cols:
            c.execute("ALTER TABLE candidates ADD COLUMN source TEXT NOT NULL DEFAULT 'Other'")
        if seed and c.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 0:
            _seed(c)


# ---------------------------------------------------------------- validation
def clean(data: dict) -> dict:
    """Trim and normalise user input."""
    out = {k: data.get(k, "") for k in FIELDS}
    for k in ("name", "email", "phone", "role", "skills", "notes", "source", "stage"):
        out[k] = str(out[k] if out[k] is not None else "").strip()
        if out[k].lower() == "nan":
            out[k] = ""
    out["email"] = out["email"].lower()
    out["skills"] = ", ".join(s.strip() for s in out["skills"].split(",") if s.strip())
    out["source"] = out["source"] or "Other"
    out["stage"] = out["stage"] or "Applied"
    try:
        out["experience"] = int(float(out["experience"] if str(out["experience"]).strip() != "" else 0))
    except (TypeError, ValueError):
        out["experience"] = None
    ad = out["applied_date"]
    if isinstance(ad, (date, datetime)):
        out["applied_date"] = ad.strftime("%Y-%m-%d")
    else:
        out["applied_date"] = str(ad or "").strip() or date.today().isoformat()
    return out


def validate(d: dict) -> list[str]:
    errors = []
    if not d["name"]:
        errors.append("Full name is required.")
    if not d["role"]:
        errors.append("Position is required.")
    if not EMAIL_RE.match(d["email"]):
        errors.append("Enter a valid email address.")
    if d["phone"] and not 7 <= len(re.sub(r"\D", "", d["phone"])) <= 15:
        errors.append("Phone number should have 7–15 digits.")
    if d["experience"] is None or not 0 <= d["experience"] <= 50:
        errors.append("Experience must be a number between 0 and 50.")
    if d["stage"] not in STAGES:
        errors.append(f"Stage must be one of: {', '.join(STAGES)}.")
    try:
        date.fromisoformat(d["applied_date"])
    except ValueError:
        errors.append("Application date must look like YYYY-MM-DD.")
    return errors


def _prepare(data: dict) -> dict:
    d = clean(data)
    errors = validate(d)
    if errors:
        raise ValueError(" ".join(errors))
    return d


def _email_taken(conn, email: str, exclude_id: int | None = None) -> bool:
    row = conn.execute("SELECT id FROM candidates WHERE email = ?", (email,)).fetchone()
    return bool(row) and row["id"] != exclude_id


# ---------------------------------------------------------------- CRUD
def _insert(conn, d: dict, detail: str = "") -> int:
    if _email_taken(conn, d["email"]):
        raise ValueError("A candidate with this email already exists.")
    cur = conn.execute(
        """INSERT INTO candidates(name,email,phone,role,skills,experience,source,stage,applied_date,notes)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        tuple(d[k] for k in FIELDS),
    )
    _log(conn, cur.lastrowid, d["name"], "Candidate added", detail or f"Source: {d['source']}")
    return cur.lastrowid


def add_candidate(data: dict, detail: str = "") -> int:
    d = _prepare(data)
    with connect() as c:
        return _insert(c, d, detail)


def update_candidate(cid: int, data: dict) -> None:
    d = _prepare(data)
    with connect() as c:
        old = c.execute("SELECT * FROM candidates WHERE id = ?", (cid,)).fetchone()
        if not old:
            raise ValueError("Candidate not found.")
        if _email_taken(c, d["email"], exclude_id=cid):
            raise ValueError("That email is already assigned to another candidate.")
        c.execute(
            """UPDATE candidates SET name=?,email=?,phone=?,role=?,skills=?,experience=?,
               source=?,stage=?,applied_date=?,notes=? WHERE id=?""",
            (*[d[k] for k in FIELDS], cid),
        )
        if old["stage"] != d["stage"]:
            _log(c, cid, d["name"], "Stage changed", f"{old['stage']} → {d['stage']}")
        if any(str(old[k]) != str(d[k]) for k in FIELDS if k != "stage"):
            _log(c, cid, d["name"], "Profile updated")


def move_stage(cid: int, stage: str) -> None:
    if stage not in STAGES:
        raise ValueError("Unknown stage.")
    with connect() as c:
        old = c.execute("SELECT name, stage FROM candidates WHERE id = ?", (cid,)).fetchone()
        if not old:
            raise ValueError("Candidate not found.")
        if old["stage"] == stage:
            return
        c.execute("UPDATE candidates SET stage = ? WHERE id = ?", (stage, cid))
        _log(c, cid, old["name"], "Stage changed", f"{old['stage']} → {stage}")


def delete_candidate(cid: int) -> None:
    with connect() as c:
        old = c.execute("SELECT name FROM candidates WHERE id = ?", (cid,)).fetchone()
        if not old:
            return
        c.execute("DELETE FROM candidates WHERE id = ?", (cid,))
        _log(c, cid, old["name"], "Candidate deleted")


def get_candidates() -> pd.DataFrame:
    with connect() as c:
        rows = c.execute("SELECT * FROM candidates ORDER BY applied_date DESC, id DESC").fetchall()
    if not rows:
        return pd.DataFrame(columns=["id", *FIELDS])
    return pd.DataFrame([dict(r) for r in rows])


def get_activity(limit: int = 10, candidate_id: int | None = None, include_imports: bool = True) -> pd.DataFrame:
    sql, args, where = "SELECT * FROM activity", [], []
    if candidate_id is not None:
        where.append("candidate_id = ?")
        args.append(candidate_id)
    if not include_imports:  # bulk imports would flood the feed with hundreds of rows
        where.append("action != 'Candidate imported'")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY ts DESC, id DESC LIMIT ?"
    args.append(limit)
    with connect() as c:
        rows = c.execute(sql, args).fetchall()
    if not rows:
        return pd.DataFrame(columns=["id", "ts", "candidate_id", "candidate", "action", "detail"])
    return pd.DataFrame([dict(r) for r in rows])


def reset_demo() -> None:
    with connect() as c:
        c.execute("DELETE FROM candidates")
        c.execute("DELETE FROM activity")
        c.execute("DELETE FROM sqlite_sequence WHERE name IN ('candidates','activity')")
        _seed(c)


def clear_all() -> None:
    """Delete every candidate and all history (start with an empty workspace)."""
    with connect() as c:
        c.execute("DELETE FROM candidates")
        c.execute("DELETE FROM activity")
        c.execute("DELETE FROM sqlite_sequence WHERE name IN ('candidates','activity')")


# ---------------------------------------------------------------- bulk import
# Different job sites export different column names; map the common ones to ours.
ALIASES = {
    "name": ["full_name", "candidate_name", "applicant_name", "candidate", "applicant"],
    "email": ["email_address", "email_id", "e_mail", "mail"],
    "phone": ["phone_number", "mobile", "mobile_number", "contact", "contact_number", "contact_no"],
    "role": ["position", "job", "title", "job_title", "applied_for", "applied_position", "applied_role",
             "designation", "position_applied_for"],
    "skills": ["key_skills", "skill_set", "skillset"],
    "experience": ["years", "years_of_experience", "experience_years", "total_experience", "exp", "work_experience"],
    "applied_date": ["date", "applied", "applied_on", "application_date", "date_applied"],
    "source": ["platform", "portal", "job_board", "applied_via", "source_website"],
    "stage": ["status", "current_stage"],
    "notes": ["recruiter_notes", "comments", "remarks", "note"],
}
_ALIAS_LOOKUP = {a: canon for canon, names in ALIASES.items() for a in names}


def to_csv_url(url: str) -> str:
    """Turn a Google Sheets link into its CSV export link (sheet must be shared 'anyone with the link')."""
    url = url.strip()
    m = re.search(r"docs\.google\.com/spreadsheets/d/([\w-]+)", url)
    if not m:
        return url
    gid = re.search(r"[#&?]gid=(\d+)", url)
    return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv" + (f"&gid={gid.group(1)}" if gid else "")


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cols = [re.sub(r"[^a-z0-9]+", "_", str(c).lower()).strip("_") for c in df.columns]
    df.columns = [_ALIAS_LOOKUP.get(c, c) for c in cols]
    return df.loc[:, ~pd.Index(df.columns).duplicated()]


def _coerce_import(d: dict, default_source: str | None) -> dict:
    """Make messy spreadsheet values safe: '3 years' -> 3, '12/10/2026' -> ISO date, unknown status -> Applied."""
    d = dict(d)
    stage = str(d.get("stage") or "").strip().lower()
    d["stage"] = next((s for s in STAGES if s.lower() == stage), "Applied")
    m = re.search(r"\d+(\.\d+)?", str(d.get("experience") or ""))
    d["experience"] = min(int(float(m.group())), 50) if m else 0
    raw = str(d.get("applied_date") or "").strip()
    parsed = pd.to_datetime(raw, errors="coerce", dayfirst=True) if raw else pd.NaT
    d["applied_date"] = parsed.date().isoformat() if pd.notna(parsed) else date.today().isoformat()
    src = str(d.get("source") or "").strip()
    d["source"] = "" if src.lower() == "nan" else src
    if not d["source"]:
        d["source"] = default_source or "Other"
    return d


def import_dataframe(df: pd.DataFrame, default_source: str | None = None) -> tuple[int, list[str]]:
    """Bulk-add candidates in one transaction. Returns (added_count, problems).

    Rows that are invalid or already exist (same email) are skipped and reported, never half-saved.
    """
    df = normalise_columns(df)
    missing = [c for c in ("name", "email", "role") if c not in df.columns]
    if missing:
        raise ValueError(f"The file is missing required column(s): {', '.join(missing)}.")
    added, problems = 0, []
    with connect() as c:
        seen = {r[0] for r in c.execute("SELECT email FROM candidates")}
        for i, row in enumerate(df.to_dict("records")):
            line = i + 2  # header is line 1
            try:
                d = _prepare(_coerce_import(row, default_source))
            except ValueError as e:
                problems.append(f"Row {line}: {e}")
                continue
            if d["email"] in seen:
                problems.append(f"Row {line}: {d['email']} already exists.")
                continue
            cur = c.execute(
                """INSERT INTO candidates(name,email,phone,role,skills,experience,source,stage,applied_date,notes)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""", tuple(d[k] for k in FIELDS))
            _log(c, cur.lastrowid, d["name"], "Candidate imported", f"Source: {d['source']}")
            seen.add(d["email"])
            added += 1
        if added:
            _log(c, None, "Bulk import", "Candidates imported",
                 f"{added} added" + (f", {len(problems)} skipped" if problems else ""))
    return added, problems


# ---------------------------------------------------------------- analytics
def compute_metrics(df: pd.DataFrame) -> dict:
    total = len(df)
    count = lambda s: int((df.stage == s).sum()) if total else 0
    hired = count("Hired")
    return {
        "total": total,
        "active": int(df.stage.isin(ACTIVE).sum()) if total else 0,
        "interview": count("Interview"),
        "offer": count("Offer"),
        "hired": hired,
        "rejected": count("Rejected"),
        "hire_rate": (hired / total * 100) if total else 0.0,
        "avg_experience": float(df.experience.mean()) if total else 0.0,
    }


def needs_attention(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """Candidates still in Applied/Screening for `days` days or more."""
    if df.empty:
        return df
    age = (pd.Timestamp(date.today()) - pd.to_datetime(df.applied_date)).dt.days
    out = df[df.stage.isin(["Applied", "Screening"]) & (age >= days)].copy()
    out["days_waiting"] = age[out.index]
    return out.sort_values("days_waiting", ascending=False)


def top_skills(df: pd.DataFrame, n: int = 8) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Skill", "Candidates"])
    s = (df.skills.fillna("").str.split(",").explode().str.strip())
    s = s[s != ""].value_counts().head(n)
    return pd.DataFrame({"Skill": s.index, "Candidates": s.values})
