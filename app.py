"""HireFlow ATS - a mini applicant tracking system (Streamlit + SQLite)."""
from datetime import date, datetime
from html import escape as esc
from urllib.parse import quote, urlsplit

import altair as alt
import pandas as pd
import streamlit as st

import db
import styles

st.set_page_config(page_title="HireFlow ATS", page_icon="🧭", layout="wide")
db.init_db()

ACCENT = "#2563EB"
PAGES = ["Overview", "Candidates", "Pipeline", "Add candidate", "Import / Export"]
FLOW = ["Applied", "Screening", "Interview", "Offer", "Hired"]
PILL = {  # background, text  (muted, standard status colours)
    "Applied": ("#F3F4F6", "#374151"),
    "Screening": ("#E0F2FE", "#075985"),
    "Interview": ("#EEF2FF", "#3730A3"),
    "Offer": ("#FEF3C7", "#92400E"),
    "Hired": ("#DCFCE7", "#166534"),
    "Rejected": ("#FEE2E2", "#991B1B"),
}

# ------------------------------------------------------------------ styling
st.markdown(styles.CSS, unsafe_allow_html=True)

if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"), icon="✅")


# ------------------------------------------------------------------ helpers
def flash(msg: str):
    st.session_state["flash"] = msg


def header(eyebrow: str, title: str, subtitle: str):
    st.markdown(f'<div class="eyebrow">{esc(eyebrow)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="subtitle">{esc(subtitle)}</div>', unsafe_allow_html=True)


def kpi(label, value, note, i=0):
    """Summary card. Numbers count up from 0 (pure CSS); `i` staggers the entrance."""
    if isinstance(value, str) and value.endswith("%"):
        shown = f'<div class="v num pct" style="--n:{int(float(value[:-1]))}" aria-label="{esc(value)}"></div>'
    elif isinstance(value, int):
        shown = f'<div class="v num" style="--n:{value}" aria-label="{value}"></div>'
    else:
        shown = f'<div class="v">{esc(str(value))}</div>'
    st.markdown(f'<div class="kpi" style="animation-delay:{i * 0.07:.2f}s"><div class="l">{esc(label)}</div>{shown}'
                f'<div class="n">{esc(note)}</div></div>', unsafe_allow_html=True)


def pill(stage: str) -> str:
    bg, fg = PILL.get(stage, PILL["Applied"])
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(stage)}</span>'


def ago(date_str: str) -> str:
    try:
        d = (date.today() - date.fromisoformat(str(date_str))).days
    except ValueError:
        return str(date_str)
    return "today" if d <= 0 else "1 day ago" if d == 1 else f"{d} days ago"


def when(ts: str) -> str:
    try:
        t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ts
    d = (date.today() - t.date()).days
    return f"today, {t:%H:%M}" if d <= 0 else "yesterday" if d == 1 else f"{d} days ago"


def bar(data: pd.DataFrame, x: str, y: str, sort=None, horizontal=False, height=260):
    if horizontal:
        enc = dict(y=alt.Y(f"{x}:N", sort=sort or "-x", title=None, axis=alt.Axis(labelLimit=220)),
                   x=alt.X(f"{y}:Q", title=None, axis=alt.Axis(tickMinStep=1, grid=True)))
    else:
        enc = dict(x=alt.X(f"{x}:N", sort=sort, title=None, axis=alt.Axis(labelAngle=0)),
                   y=alt.Y(f"{y}:Q", title=None, axis=alt.Axis(tickMinStep=1, grid=True)))
    chart = (alt.Chart(data).mark_bar(color=ACCENT, cornerRadiusEnd=4, size=26)
             .encode(tooltip=[x, y], **enc).properties(height=height)
             .configure_view(strokeWidth=0).configure_axis(labelFontSize=12, domainColor="#E5E7EB", gridColor="#F3F4F6"))
    st.altair_chart(chart, width="stretch")


def show_table(data: pd.DataFrame, empty_msg="No candidates match your filters."):
    if data.empty:
        st.info(empty_msg)
        return
    view = data[["name", "role", "stage", "experience", "skills", "email", "applied_date"]].copy()
    view.columns = ["Candidate", "Position", "Stage", "Experience", "Skills", "Email", "Applied"]
    st.dataframe(view, hide_index=True, width="stretch",
                 column_config={"Experience": st.column_config.NumberColumn(format="%d yrs")})


def csv_bytes(data: pd.DataFrame) -> bytes:
    return data[db.FIELDS].to_csv(index=False).encode("utf-8")


# ------------------------------------------------------------------ PUBLIC APPLY PAGE
def _reset_applied():
    st.session_state.pop("applied_ok", None)


def page_apply():
    """Candidate-facing form, opened with  ?apply=1&source=LinkedIn&role=Python%20Developer"""
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl']{display:none}</style>",
                unsafe_allow_html=True)
    source = str(st.query_params.get("source", "Career site"))[:40] or "Career site"
    role_param = str(st.query_params.get("role", ""))[:80]
    _, mid, _ = st.columns([1, 2.2, 1])
    with mid:
        st.markdown('<div class="sb-brand" style="margin-bottom:10px"><div class="sb-logo">H</div><div>'
                    '<div class="sb-name" style="color:#111827">HireFlow</div>'
                    '<div class="sb-sub">Careers</div></div></div>', unsafe_allow_html=True)
        if st.session_state.get("applied_ok"):
            st.markdown("# Application received")
            st.success(f"Thank you, {st.session_state['applied_ok']}. Our hiring team will review your "
                       "application and contact you by email.")
            st.button("Submit another application", on_click=_reset_applied)
            return
        st.markdown("# Apply for a position")
        st.markdown('<div class="subtitle">Tell us a little about yourself. It takes about a minute.</div>',
                    unsafe_allow_html=True)
        with st.form("public_apply"):
            name = st.text_input("Full name *")
            email = st.text_input("Email address *")
            phone = st.text_input("Phone")
            role = st.text_input("Position applying for *", value=role_param, disabled=bool(role_param))
            a, b = st.columns(2)
            exp = a.number_input("Years of experience", 0, 50, 0)
            skills = b.text_input("Key skills", placeholder="Python, SQL, Figma")
            notes = st.text_area("Cover note or link to your resume / portfolio")
            submitted = st.form_submit_button("Submit application", type="primary")
        if submitted:
            try:
                db.add_candidate(dict(name=name, email=email, phone=phone, role=role_param or role, skills=skills,
                                      experience=exp, source=source, stage="Applied", notes=notes),
                                 detail=f"Applied via {source}")
                st.session_state["applied_ok"] = name.strip()
                st.rerun()
            except ValueError as e:
                st.error(str(e))


# ------------------------------------------------------------------ data + sidebar
if st.query_params.get("apply"):
    page_apply()
    st.stop()

df = db.get_candidates()
m = db.compute_metrics(df)

def go_add():
    st.session_state["page"] = "Add candidate"


with st.sidebar:
    st.markdown('<div class="sb-brand"><div class="sb-logo">H</div><div><div class="sb-name">HireFlow</div>'
                '<div class="sb-sub">Applicant Tracking System</div></div></div>'
                '<div class="sb-label">Menu</div>', unsafe_allow_html=True)
    page = st.radio("Navigate", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    st.button("＋  New candidate", key="quick_add", on_click=go_add, width="stretch")
    st.markdown('<div class="sb-user"><div class="av">HR</div><div><div class="nm">Recruiter</div>'
                '<div class="rl">Hiring team</div></div></div>', unsafe_allow_html=True)

st.markdown(f'<div class="topbar"><div class="crumb"><span>HireFlow</span><span class="sep">/</span><b>{esc(page)}</b></div>'
            f'<div class="top-right">'
            f'<span class="datepill">{date.today():%a, %d %b %Y}</span><div class="avatar">HR</div></div></div>',
            unsafe_allow_html=True)


# ------------------------------------------------------------------ OVERVIEW
def page_overview():
    header("Recruiting workspace", "Overview", "A live snapshot of your hiring pipeline.")
    items = [("Candidates", m["total"], "All applications"),
             ("Active", m["active"], "Applied to Offer"),
             ("Interviews", m["interview"], "In interview stage"),
             ("Offers", m["offer"], "Offer stage"),
             ("Hired", m["hired"], "Successful hires"),
             ("Hire rate", f"{m['hire_rate']:.0f}%", "Hired ÷ total")]
    for i, (col, it) in enumerate(zip(st.columns(6), items)):
        with col:
            kpi(*it, i=i)
    st.write("")

    left, right = st.columns([3, 2])
    with left:
        with st.container(border=True):
            st.subheader("Hiring funnel")
            st.caption("Number of candidates in each stage")
            counts = pd.DataFrame({"Stage": db.STAGES,
                                   "Candidates": [int((df.stage == s).sum()) for s in db.STAGES]})
            bar(counts, "Stage", "Candidates", sort=db.STAGES, height=230)
    with right:
        with st.container(border=True):
            st.subheader("Applications by source")
            st.caption("Where your candidates come from")
            if df.empty:
                st.info("No applications yet.")
            else:
                src = df.source.replace("", "Other").value_counts().rename_axis("Source").reset_index(name="Candidates")
                bar(src, "Source", "Candidates", horizontal=True, height=max(160, 40 * len(src)))

    c3, c4 = st.columns([3, 2])
    with c3:
        with st.container(border=True):
            st.subheader("Recently added")
            show_table(df.head(6), "No candidates yet. Add one from the sidebar.")
    with c4:
        with st.container(border=True):
            st.subheader("Recent activity")
            act = db.get_activity(limit=6, include_imports=False)
            if act.empty:
                st.caption("Nothing yet.")
            for _, a in act.iterrows():
                detail = f" · {esc(a.detail)}" if a.detail else ""
                st.markdown(f'<div class="feed"><b>{esc(a.candidate)}</b> — {esc(a.action)}<br>'
                            f'<span class="muted">{when(a.ts)}{detail}</span></div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("Needs attention")
        st.caption("Still in Applied or Screening after 7 days or more")
        stale = db.needs_attention(df)
        if stale.empty:
            st.success("All caught up. No candidates are waiting too long.")
        else:
            view = stale[["name", "role", "stage", "days_waiting"]].head(15)
            view.columns = ["Candidate", "Position", "Stage", "Days waiting"]
            st.dataframe(view, hide_index=True, width="stretch")
            if len(stale) > 15:
                st.caption(f"Showing 15 of {len(stale)}. Filter by stage on the Candidates page to see the rest.")


# ------------------------------------------------------------------ CANDIDATES
def candidate_detail(row):
    cid = int(row["id"])
    t_profile, t_edit, t_delete = st.tabs(["Profile", "Edit details", "Delete"])

    with t_profile:
        a, b = st.columns([3, 2])
        with a:
            skills = "".join(f'<span class="tag">{esc(s.strip())}</span>'
                             for s in str(row["skills"]).split(",") if s.strip()) or '<span class="muted">No skills listed</span>'
            notes = esc(row["notes"]) if str(row["notes"]).strip() else '<span class="muted">No notes</span>'
            st.markdown(
                f'<div class="profile"><h2>{esc(row["name"])}</h2>'
                f'<div class="muted" style="margin:2px 0 10px 0">{esc(row["role"])} &nbsp; {pill(row["stage"])}</div>'
                f'<div class="row"><span class="k">Email</span><span>{esc(row["email"])}</span></div>'
                f'<div class="row"><span class="k">Phone</span><span>{esc(row["phone"]) or "—"}</span></div>'
                f'<div class="row"><span class="k">Source</span><span>{esc(row["source"])}</span></div>'
                f'<div class="row"><span class="k">Experience</span><span>{int(row["experience"])} years</span></div>'
                f'<div class="row"><span class="k">Applied</span><span>{esc(row["applied_date"])} ({ago(row["applied_date"])})</span></div>'
                f'<div class="row" style="display:block"><div class="k" style="margin-bottom:6px">Skills</div>{skills}</div>'
                f'<div class="row" style="display:block;border:none"><div class="k" style="margin-bottom:6px">Recruiter notes</div>{notes}</div>'
                f'</div>', unsafe_allow_html=True)
        with b:
            with st.container(border=True):
                st.markdown("**Move to stage**")
                new_stage = st.selectbox("Stage", db.STAGES, index=db.STAGES.index(row["stage"]),
                                         key=f"mv_{cid}", label_visibility="collapsed")
                if st.button("Update stage", key=f"mvbtn_{cid}", type="primary", width="stretch",
                             disabled=new_stage == row["stage"]):
                    db.move_stage(cid, new_stage)
                    flash(f"{row['name']} moved to {new_stage}.")
                    st.rerun()
            with st.container(border=True):
                st.markdown("**History**")
                hist = db.get_activity(limit=6, candidate_id=cid)
                if hist.empty:
                    st.caption("No history yet.")
                for _, h in hist.iterrows():
                    detail = f" · {esc(h.detail)}" if h.detail else ""
                    st.markdown(f'<div class="feed">{esc(h.action)}<br><span class="muted">{when(h.ts)}{detail}</span></div>',
                                unsafe_allow_html=True)

    with t_edit:
        with st.form(f"edit_{cid}"):
            a, b = st.columns(2)
            with a:
                name = st.text_input("Full name *", row["name"])
                email = st.text_input("Email *", row["email"])
                phone = st.text_input("Phone", row["phone"])
                role = st.text_input("Position *", row["role"])
            with b:
                skills = st.text_input("Skills (comma-separated)", row["skills"])
                exp = st.number_input("Years of experience", 0, 50, int(row["experience"]))
                srcs = db.SOURCES if row["source"] in db.SOURCES else db.SOURCES + [row["source"]]
                source = st.selectbox("Source", srcs, index=srcs.index(row["source"]))
                stage = st.selectbox("Hiring stage", db.STAGES, index=db.STAGES.index(row["stage"]))
            applied = st.date_input("Application date", value=date.fromisoformat(str(row["applied_date"])))
            notes = st.text_area("Recruiter notes", row["notes"])
            if st.form_submit_button("Save changes", type="primary"):
                try:
                    db.update_candidate(cid, dict(name=name, email=email, phone=phone, role=role, skills=skills,
                                                  experience=exp, source=source, stage=stage,
                                                  applied_date=applied, notes=notes))
                    flash("Candidate updated.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with t_delete:
        st.warning("Deleting a candidate permanently removes their record. This cannot be undone.")
        ok = st.checkbox("I understand and want to delete this candidate", key=f"confirm_{cid}")
        if st.button("Delete candidate", key=f"del_{cid}", disabled=not ok):
            db.delete_candidate(cid)
            flash(f"{row['name']} was deleted.")
            st.rerun()


def page_candidates():
    header("People", "Candidates", "Search your talent pool and keep every application moving.")
    f1, f2, f3, f4 = st.columns([2.2, 1, 1.3, 1.2])
    query = f1.text_input("Search", placeholder="Name, email, skills or position")
    stage_f = f2.selectbox("Stage", ["All stages"] + db.STAGES)
    roles = sorted(df.role.dropna().unique().tolist()) if not df.empty else []
    role_f = f3.selectbox("Position", ["All positions"] + roles)
    sort_by = f4.selectbox("Sort by", ["Newest first", "Oldest first", "Name A–Z", "Experience (high–low)"])

    out = df.copy()
    if query.strip() and not out.empty:
        q = query.strip().lower()
        hay = out[["name", "email", "skills", "role"]].fillna("").astype(str).apply(
            lambda col: col.str.lower().str.contains(q, regex=False))
        out = out[hay.any(axis=1)]
    if stage_f != "All stages":
        out = out[out.stage == stage_f]
    if role_f != "All positions":
        out = out[out.role == role_f]
    if not out.empty:
        if sort_by == "Oldest first":
            out = out.sort_values(["applied_date", "id"])
        elif sort_by == "Name A–Z":
            out = out.sort_values("name", key=lambda s: s.str.lower())
        elif sort_by.startswith("Experience"):
            out = out.sort_values("experience", ascending=False)

    top_l, top_r = st.columns([4, 1])
    top_l.caption(f"Showing {len(out)} of {len(df)} candidates")
    top_r.download_button("Download CSV", csv_bytes(out), "candidates.csv", "text/csv",
                          width="stretch", disabled=out.empty)
    show_table(out)

    st.divider()
    st.subheader("Open a candidate")
    if out.empty:
        st.caption("No candidates to open. Adjust your filters or add a new candidate.")
        return
    labels = {int(r["id"]): f"{r['name']} — {r['role']}" for _, r in out.iterrows()}
    chosen = st.selectbox("Select a candidate to view, edit or delete", list(labels), index=None,
                          format_func=lambda i: labels[i], placeholder="Start typing a name…", key="open_id")
    if chosen is not None:
        candidate_detail(out[out.id == chosen].iloc[0])


# ------------------------------------------------------------------ PIPELINE
def move_cb(cid, stage, name):
    try:
        db.move_stage(cid, stage)
        flash(f"{name} moved to {stage}.")
    except ValueError as e:
        flash(str(e))


def page_pipeline():
    header("Workflow", "Hiring pipeline", "Move candidates through each stage of the hiring process.")
    roles = sorted(df.role.dropna().unique().tolist()) if not df.empty else []
    f1, f2, f3 = st.columns([2, 1.3, 1])
    q = f1.text_input("Search", placeholder="Name, email, skills or position", key="pipe_q")
    pos = f2.selectbox("Position", ["All positions"] + roles)
    cap = f3.selectbox("Cards per column", [10, 25, 50, "All"], help="Keeps the board fast when you have hundreds of applicants.")
    data = df
    if pos != "All positions":
        data = data[data.role == pos]
    if q.strip() and not data.empty:
        ql = q.strip().lower()
        hay = data[["name", "email", "skills", "role"]].fillna("").astype(str).apply(
            lambda col: col.str.lower().str.contains(ql, regex=False))
        data = data[hay.any(axis=1)]
    st.write("")
    for stage, col in zip(db.STAGES, st.columns(6)):
        with col:
            subset = data[data.stage == stage]
            shown = subset if cap == "All" else subset.head(int(cap))
            st.markdown(f'<div class="colhead"><span><i style="background:{PILL[stage][1]}"></i>{stage}</span>'
                        f'<span class="count">{len(subset)}</span></div>', unsafe_allow_html=True)
            if subset.empty:
                st.caption("No candidates")
            for _, r in shown.iterrows():
                cid, name = int(r["id"]), r["name"]
                with st.container(border=True):
                    st.markdown(f"**{name}**")
                    st.caption(f"{r['role']} · {int(r['experience'])} yr · {ago(r['applied_date'])}")
                    if stage == "Rejected":
                        st.button("Reopen", key=f"re_{cid}", on_click=move_cb, args=(cid, "Applied", name),
                                  width="stretch", help="Move back to Applied")
                        continue
                    i = FLOW.index(stage)
                    prev_s = FLOW[i - 1] if i > 0 else None
                    next_s = FLOW[i + 1] if i < len(FLOW) - 1 else None
                    st.button(f"Move to {next_s}" if next_s else "Final stage", key=f"n_{cid}",
                              disabled=next_s is None, type="primary", width="stretch",
                              on_click=move_cb, args=(cid, next_s, name))
                    st.button("Back", key=f"p_{cid}", disabled=prev_s is None, width="stretch",
                              on_click=move_cb, args=(cid, prev_s, name), help=f"Return to {prev_s}")
                    st.button("Reject", key=f"x_{cid}", width="stretch",
                              on_click=move_cb, args=(cid, "Rejected", name), help="Mark as rejected")
            if len(subset) > len(shown):
                st.caption(f"+ {len(subset) - len(shown)} more. Raise the limit or use the Candidates page.")


# ------------------------------------------------------------------ ADD
def page_add():
    header("People", "Add a candidate", "Create a profile and place the applicant in your hiring pipeline.")
    with st.form("add_candidate", clear_on_submit=False):
        a, b = st.columns(2)
        with a:
            name = st.text_input("Full name *", placeholder="e.g. Ananya Rao")
            email = st.text_input("Email address *", placeholder="candidate@example.com")
            phone = st.text_input("Phone", placeholder="+91 90000 00000")
            role = st.text_input("Position applied for *", placeholder="e.g. Full Stack Developer")
        with b:
            skills = st.text_input("Skills (comma-separated)", placeholder="Python, React, SQL")
            exp = st.number_input("Years of experience", 0, 50, 0)
            source = st.selectbox("Source", db.SOURCES)
            stage = st.selectbox("Hiring stage", db.STAGES)
        applied = st.date_input("Application date", value=date.today())
        notes = st.text_area("Recruiter notes", placeholder="Feedback, next steps or context")
        submitted = st.form_submit_button("Add candidate", type="primary")
    if submitted:
        try:
            db.add_candidate(dict(name=name, email=email, phone=phone, role=role, skills=skills,
                                  experience=exp, source=source, stage=stage, applied_date=applied, notes=notes))
            flash(f"{name.strip()} was added.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
    st.caption("Fields marked * are required.")


# ------------------------------------------------------------------ IMPORT / EXPORT
def read_upload(up) -> pd.DataFrame:
    if up.name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(up, dtype=str, keep_default_na=False)
    return pd.read_csv(up, dtype=str, keep_default_na=False)


def page_io():
    header("Data", "Import & export", "Collect applications from any website, bulk-import files and export your data.")
    if "import_result" in st.session_state:
        added, problems = st.session_state.pop("import_result")
        dupes = sum("already exists" in p for p in problems)
        (st.success if added else st.warning)(
            f"Imported {added} candidate(s). Skipped {len(problems)} row(s) ({dupes} duplicate email(s)).")
        if problems:
            with st.expander("See skipped rows"):
                for p in problems[:50]:
                    st.write("• " + p)
                if len(problems) > 50:
                    st.caption(f"…and {len(problems) - 50} more.")

    # ---- 1. application links
    with st.container(border=True):
        st.subheader("Application links")
        st.caption("Share one link per website. Candidates fill a short form and land in your pipeline, "
                   "tagged with where they came from.")
        ctx_url = getattr(st.context, "url", None) or "http://localhost:8501"
        parts = urlsplit(str(ctx_url))
        base = st.text_input("Your app address", value=f"{parts.scheme}://{parts.netloc}", key="base_url")
        base = base.strip().rstrip("/")
        site = st.selectbox("Website", ["LinkedIn", "Naukri", "Indeed", "Career site", "Referral", "Campus", "Other"])
        st.code(f"{base}/?apply=1&source={quote(site)}", language=None)
        st.caption("To open a specific job, add &role=Python%20Developer to a link.")

    # ---- 2. import
    with st.container(border=True):
        st.subheader("Import many applications")
        st.caption("Export a file from any job site or form and upload it. Columns such as Full Name, Email ID, "
                   "Job Title or Applied On are recognised automatically. Duplicate emails are skipped.")
        default_src = st.selectbox("Source for rows that have no source column", db.SOURCES, index=db.SOURCES.index("Other"))
        t_file, t_link = st.tabs(["Upload CSV / Excel", "From Google Sheet link"])
        data = None
        with t_file:
            n = st.session_state.setdefault("uploader_n", 0)
            up = st.file_uploader("CSV or Excel file", type=["csv", "xlsx"], key=f"file_{n}")
            if up is not None:
                try:
                    data = read_upload(up)
                except Exception as e:
                    st.error(f"Could not read that file: {e}")
        with t_link:
            link = st.text_input("Google Sheet or CSV link", placeholder="https://docs.google.com/spreadsheets/d/…",
                                 help="Share the sheet as 'Anyone with the link can view'. Connect a Google Form to it to collect applications.")
            if link.strip() and st.button("Load from link"):
                try:
                    st.session_state["link_data"] = pd.read_csv(db.to_csv_url(link), dtype=str, keep_default_na=False)
                except Exception as e:
                    st.error(f"Could not load that link. Check that it is shared with anyone who has the link. ({e})")
            if data is None and "link_data" in st.session_state:
                data = st.session_state["link_data"]
        if data is not None:
            st.caption(f"Preview: {len(data)} row(s)")
            st.dataframe(data.head(8), hide_index=True, width="stretch")
            if st.button(f"Import {len(data)} candidate(s)", type="primary"):
                try:
                    st.session_state["import_result"] = db.import_dataframe(data, default_source=default_src)
                    st.session_state["uploader_n"] = n + 1
                    st.session_state.pop("link_data", None)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    # ---- 3. export
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("Export")
            st.caption("Download every candidate as a CSV file.")
            st.download_button("Download all candidates", csv_bytes(df), "hireflow_candidates.csv", "text/csv",
                               disabled=df.empty)
    with c2:
        with st.container(border=True):
            st.subheader("Import template")
            st.caption("Required columns: name, email, role. Others are optional.")
            tpl = pd.DataFrame([dict(name="Sample Person", email="sample.person@example.com", phone="+91 90000 00099",
                                     role="Data Analyst", skills="SQL, Excel", experience=2, source="LinkedIn",
                                     stage="Applied", applied_date=date.today().isoformat(), notes="Optional note")])
            st.download_button("Download CSV template", tpl.to_csv(index=False).encode(), "hireflow_template.csv", "text/csv")

    # ---- 4. danger zone
    with st.container(border=True):
        st.subheader("Danger zone")
        st.caption("These actions cannot be undone.")
        ok = st.checkbox("I understand this removes everything I added", key="reset_ok")
        d1, d2, _ = st.columns([1, 1, 2])
        if d1.button("Delete all candidates", disabled=not ok):
            db.clear_all()
            flash("All candidates deleted.")
            st.rerun()
        if d2.button("Restore sample data", disabled=not ok):
            db.reset_demo()
            flash("Sample data restored.")
            st.rerun()


PAGE_FUNCS = {"Overview": page_overview, "Candidates": page_candidates, "Pipeline": page_pipeline,
              "Add candidate": page_add, "Import / Export": page_io}
render = PAGE_FUNCS[page]
render()

st.markdown('<div class="footer"><div><b>HireFlow</b> · © 2026 All rights reserved</div></div>', unsafe_allow_html=True)
