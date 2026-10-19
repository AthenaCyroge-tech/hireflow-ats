import pandas as pd
import pytest

import db


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ATS_DB_PATH", str(tmp_path / "test.db"))
    db.init_db()


def person(**kw):
    base = dict(name="Test User", email="test.user@example.com", role="QA Engineer",
                skills="Python, pytest", experience=2, stage="Applied")
    base.update(kw)
    return base


def test_seed_data_created_once():
    assert len(db.get_candidates()) == len(db.SAMPLE)
    db.init_db()  # running again must not duplicate
    assert len(db.get_candidates()) == len(db.SAMPLE)


def test_add_and_read():
    cid = db.add_candidate(person())
    df = db.get_candidates()
    row = df[df.id == cid].iloc[0]
    assert row["name"] == "Test User" and row["stage"] == "Applied"


def test_email_is_normalised_and_unique():
    db.add_candidate(person(email="  Test.User@Example.com "))
    with pytest.raises(ValueError, match="already exists"):
        db.add_candidate(person(email="test.user@example.com"))


@pytest.mark.parametrize("bad", [dict(name=""), dict(role=""), dict(email="nope"),
                                 dict(experience=99), dict(stage="Nope"), dict(phone="12")])
def test_validation_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        db.add_candidate(person(**bad))


def test_update_and_stage_history():
    cid = db.add_candidate(person())
    db.update_candidate(cid, person(role="SDET", stage="Interview"))
    row = db.get_candidates().query("id == @cid").iloc[0]
    assert row["role"] == "SDET" and row["stage"] == "Interview"
    actions = db.get_activity(candidate_id=cid)["action"].tolist()
    assert "Stage changed" in actions and "Profile updated" in actions


def test_update_cannot_steal_another_email():
    a = db.add_candidate(person())
    db.add_candidate(person(email="b@example.com", name="B"))
    with pytest.raises(ValueError, match="another candidate"):
        db.update_candidate(a, person(email="b@example.com"))


def test_move_stage_and_delete():
    cid = db.add_candidate(person())
    db.move_stage(cid, "Offer")
    assert db.get_candidates().query("id == @cid").iloc[0]["stage"] == "Offer"
    db.delete_candidate(cid)
    assert cid not in db.get_candidates().id.tolist()


def test_metrics():
    m = db.compute_metrics(db.get_candidates())
    assert m["total"] == len(db.SAMPLE)
    assert m["hired"] == 2 and 0 < m["hire_rate"] < 100


def test_metrics_on_empty_database():
    db.reset_demo()
    for cid in db.get_candidates().id:
        db.delete_candidate(int(cid))
    df = db.get_candidates()
    assert db.compute_metrics(df)["total"] == 0
    assert db.needs_attention(df).empty and db.top_skills(df).empty


def test_needs_attention_and_top_skills():
    df = db.get_candidates()
    assert "Meera Iyer" in db.needs_attention(df).name.tolist()
    assert db.top_skills(df).iloc[0]["Candidates"] >= 2


def test_csv_import_reports_bad_rows():
    csv = pd.DataFrame([
        dict(Name="Ok One", Email="ok.one@example.com", Position="Designer", Experience="3"),
        dict(Name="Bad Email", Email="bad", Position="Designer", Experience="1"),
        dict(Name="Dup", Email="ok.one@example.com", Position="Designer", Experience="1"),
    ])
    added, errors = db.import_dataframe(csv)
    assert added == 1 and len(errors) == 2


def test_csv_import_needs_required_columns():
    with pytest.raises(ValueError, match="missing"):
        db.import_dataframe(pd.DataFrame([dict(name="x")]))


def test_old_database_is_upgraded(tmp_path, monkeypatch):
    import sqlite3
    old = tmp_path / "old.db"
    con = sqlite3.connect(old)
    con.execute("""CREATE TABLE candidates(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE, skills TEXT NOT NULL DEFAULT '', role TEXT NOT NULL,
        experience INTEGER NOT NULL DEFAULT 0, stage TEXT NOT NULL DEFAULT 'Applied',
        applied_date TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '')""")
    con.execute("INSERT INTO candidates(name,email,role,applied_date) VALUES('Old','old@example.com','Dev','2026-01-01')")
    con.commit(); con.close()
    monkeypatch.setenv("ATS_DB_PATH", str(old))
    db.init_db()
    df = db.get_candidates()
    assert len(df) == 1 and df.iloc[0]["source"] == "Other"


def test_reset_demo():
    db.add_candidate(person())
    db.reset_demo()
    assert len(db.get_candidates()) == len(db.SAMPLE)


# ---------------------------------------------------------------- bulk / multi-site import
def test_import_400_rows_is_fast_and_maps_other_sites_columns():
    import time
    db.clear_all()
    n = 400
    df = pd.DataFrame({"Full Name": [f"P{i}" for i in range(n)], "Email ID": [f"p{i}@example.com" for i in range(n)],
                       "Mobile Number": ["+91 98765 43210"] * n, "Job Title": ["Developer"] * n,
                       "Total Experience": ["3 years"] * n, "Applied On": ["12/10/2026"] * n,
                       "Status": ["New"] * n, "Key Skills": ["Python, SQL"] * n})
    t = time.time()
    added, problems = db.import_dataframe(df, default_source="Naukri")
    assert added == n and not problems and time.time() - t < 5
    row = db.get_candidates().iloc[0]
    assert row["source"] == "Naukri" and row["stage"] == "Applied" and row["experience"] == 3
    assert row["applied_date"] == "2026-10-12"          # day-first dates
    # the activity feed is not flooded by 400 rows
    assert len(db.get_activity(10, include_imports=False)) == 1


def test_reimport_skips_duplicates():
    db.clear_all()
    df = pd.DataFrame({"name": ["A"], "email": ["a@example.com"], "role": ["Dev"]})
    assert db.import_dataframe(df)[0] == 1
    added, problems = db.import_dataframe(df)
    assert added == 0 and "already exists" in problems[0]


def test_google_sheet_link_becomes_csv_export_link():
    url = db.to_csv_url("https://docs.google.com/spreadsheets/d/ABC123/edit#gid=55")
    assert url == "https://docs.google.com/spreadsheets/d/ABC123/export?format=csv&gid=55"
    assert db.to_csv_url("https://example.com/a.csv") == "https://example.com/a.csv"


def test_clear_all():
    db.clear_all()
    assert db.get_candidates().empty and db.get_activity().empty
