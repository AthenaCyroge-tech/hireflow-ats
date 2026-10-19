"""Smoke tests: every page of the Streamlit app renders without errors."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import db

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PAGES = ["Overview", "Candidates", "Pipeline", "Add candidate", "Import / Export"]


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ATS_DB_PATH", str(tmp_path / "ui.db"))
    db.init_db()


def run(page="Overview"):
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["page"] = page
    return at.run()


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = run(page)
    assert not at.exception, at.exception


def test_add_candidate_through_form():
    at = run("Add candidate")
    at.text_input[0].set_value("UI Tester")
    at.text_input[1].set_value("ui.tester@example.com")
    at.text_input[3].set_value("QA Engineer")
    next(b for b in at.button if b.label == "Add candidate").click().run()
    assert not at.exception
    assert "ui.tester@example.com" in db.get_candidates().email.tolist()


def test_add_form_shows_validation_error():
    at = run("Add candidate")
    at.text_input[1].set_value("not-an-email")
    next(b for b in at.button if b.label == "Add candidate").click().run()
    assert at.error and not at.exception


def test_pipeline_button_moves_candidate():
    at = run("Pipeline")
    btn = next(b for b in at.button if b.label.startswith("Move to") and not b.disabled)
    cid = int(btn.key.split("_")[1])
    before = db.get_candidates().query("id == @cid").iloc[0]["stage"]
    btn.click().run()
    assert not at.exception
    assert db.get_candidates().query("id == @cid").iloc[0]["stage"] != before


def test_candidate_detail_and_edit():
    at = run("Candidates")
    cid = int(db.get_candidates().iloc[0]["id"])
    at.selectbox(key="open_id").select(cid).run()
    assert not at.exception
    at.text_input[1].set_value("Edited Name")  # first text input after search is 'Full name'
    at.button(key="FormSubmitter:edit_%d-Save changes" % cid).click().run()
    assert not at.exception


def test_public_apply_page_records_source():
    at = AppTest.from_file(APP, default_timeout=30)
    at.query_params["apply"] = "1"
    at.query_params["source"] = "LinkedIn"
    at.run()
    assert not at.exception
    at.text_input[0].set_value("Web Applicant")
    at.text_input[1].set_value("web.applicant@example.com")
    at.text_input[3].set_value("Data Analyst")
    next(b for b in at.button if b.label == "Submit application").click().run()
    assert not at.exception
    row = db.get_candidates().query("email == 'web.applicant@example.com'").iloc[0]
    assert row["source"] == "LinkedIn" and row["stage"] == "Applied"


def test_apply_page_has_no_dashboard():
    at = AppTest.from_file(APP, default_timeout=30)
    at.query_params["apply"] = "1"
    at.run()
    assert not at.sidebar.radio


def test_app_handles_400_applicants():
    import pandas as pd
    n = 400
    db.import_dataframe(pd.DataFrame({"name": [f"P{i}" for i in range(n)], "email": [f"x{i}@example.com" for i in range(n)],
                                      "role": ["Developer"] * n}))
    for page in ["Overview", "Candidates", "Pipeline"]:
        at = run(page)
        assert not at.exception, (page, at.exception)


def test_no_demo_or_tech_labels_in_ui():
    at = run("Overview")
    html = " ".join(m.value for m in at.markdown)
    for banned in ["Live demo", "Database connected", "Built with", "Streamlit", "SQLite"]:
        assert banned not in html
