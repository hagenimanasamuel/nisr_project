"""Early Intervention: flagged learners, Student 360 view, what-if simulator, case log."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).parent.parent
FAVICON = BASE_DIR / "favicon.ico"
st.set_page_config(page_title="Early Intervention · RORA", page_icon=str(FAVICON) if FAVICON.exists() else ":material/flag:", layout="wide")

from src.analytics import roster_view  # noqa: E402
from src.auth import get_current_user  # noqa: E402
from src.components import (  # noqa: E402
    BRAND,
    callout,
    info_card,
    kpi_row,
    page_header,
    render_footer,
    show_chart,
    show_table,
)
from src.demo_alerts import load_mock_students  # noqa: E402
from src.follow_up import flatten_actions, load_actions, save_action  # noqa: E402
from src.layout import render_sidebar  # noqa: E402
from src.prediction_model import predict_student_risk, simulate_intervention  # noqa: E402
from src.style import apply_style  # noqa: E402

apply_style()

user = get_current_user()
if not user:
    st.warning("Please sign in to view this page.")
    st.page_link("app.py", label="Go to sign in", icon=":material/lock:")
    st.stop()

render_sidebar(current_page="Early Intervention")

page_header(
    "Early intervention",
    "From a district average to a named child",
    "Who needs support now, why, and what would change the outcome?",
    "District data cannot see individual learners. This page shows how authorised school records "
    "(for example SDMS) could surface risk early and turn it into a logged follow-up.",
)
st.caption("Student records on this page are simulated. No real student data is used.")

raw = load_mock_students()
if raw is None or raw.empty:
    st.error("Simulated student data is missing. Check data/demo/mock_students.csv.")
    st.stop()
df = predict_student_risk(raw)
flagged = df[df["needs_attention"]].sort_values("predicted_risk_pct", ascending=False)

kpi_row([
    ("Flagged learners", len(flagged), "Predicted risk of 40% or more."),
    ("No warning", len(df) - len(flagged), "Below the warning threshold."),
    ("High risk", int((df["risk_tier"] == "High Risk").sum()), "Predicted risk of 70% or more."),
])

if flash := st.session_state.pop("flash", None):
    st.success(flash)

st.subheader("Learners who need follow-up")
st.write("Warnings combine attendance, marks, household economics and local climate shocks.")
if flagged.empty:
    st.info("No learners currently meet the warning criteria.")
else:
    show_table(
        roster_view(flagged),
        column_config={"Predicted risk (%)": st.column_config.ProgressColumn("Predicted risk (%)", min_value=0, max_value=100, format="%.1f")},
    )

st.divider()

if user.get("role") == "school_staff":
    st.subheader("Student 360 and what-if simulator")
    if flagged.empty:
        st.info("There are no active warnings.")
    else:
        names = flagged.set_index("student_id")
        selected = st.selectbox(
            "Learner",
            names.index.tolist(),
            format_func=lambda s: f"{s} · {names.loc[s, 'student_name']} · {names.loc[s, 'school']}",
        )
        s = flagged[flagged["student_id"] == selected].iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            info_card("Identity", [("Name", s["student_name"]), ("School", s["school"]), ("District", s["district"]), ("Grade", s["grade_level"])])
        with c2:
            info_card("Academic", [("Term marks", f"{s['term_average_marks']}%"), ("Trend", f"{s['marks_trend']:+.1f} pts"), ("Repeated a grade", s["prior_grade_repetition"])])
        with c3:
            info_card("Attendance", [("Recent", f"{s['recent_attendance']}%"), ("Previous term", f"{s['previous_attendance']}%"), ("Consecutive absences", f"{int(s['consecutive_absences'])} days")])
        with c4:
            info_card("Household", [("Ubudehe", f"Category {int(s['ubudehe_category'])}"), ("Feeding fee", s["feeding_fee_status"]), ("Climate shock", s["household_climate_impact"])])

        callout("Recommended first step", f"<b>{s['primary_driver']}</b>. {s['prescribed_action']}.")

        left, right = st.columns([1, 1])
        with left:
            attribution = pd.DataFrame({
                "Domain": ["Academic", "Household and fees", "Attendance", "Climate and commute"],
                "Share (%)": [s["academic_contrib_pct"], s["economic_contrib_pct"], s["attendance_contrib_pct"], s["shock_contrib_pct"]],
            }).sort_values("Share (%)")
            fig = px.bar(attribution, x="Share (%)", y="Domain", orientation="h", title="What is driving this learner's risk", labels={"Domain": ""})
            fig.update_traces(marker_color=BRAND)
            show_chart(fig, height=330, key="attribution")

        with right:
            st.markdown("**What-if simulator**")
            options = {
                "feeding_bursary": st.checkbox("Clear feeding fee arrears", value=True),
                "academic_remedial": st.checkbox("Remedial tutoring (+16 marks)", value=True),
                "attendance_mentoring": st.checkbox("Attendance mentor and home visit"),
                "climate_shock_relief": st.checkbox("Climate relief linkage"),
            }
            sim = simulate_intervention(s, [k for k, on in options.items() if on])
            gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=sim["simulated_prob"],
                number={"suffix": "%"},
                delta={"reference": sim["original_prob"], "increasing": {"color": "#C53030"}, "decreasing": {"color": "#2F855A"}, "suffix": " pts"},
                title={"text": f"Risk after intervention · {sim['new_tier']}"},
                gauge={
                    "axis": {"range": [0, 100]}, "bar": {"color": BRAND},
                    "steps": [
                        {"range": [0, 40], "color": "#E6EDF5"},
                        {"range": [40, 70], "color": "#FBE3CB"},
                        {"range": [70, 100], "color": "#F6D0D0"},
                    ],
                },
            ))
            show_chart(gauge, height=280, key="gauge")
            st.caption(f"Baseline {sim['original_prob']}%. Reduction of {sim['delta_reduction']} points.")

        st.markdown("**Record a follow-up action**")
        with st.form("action_form", clear_on_submit=True):
            action = st.selectbox("Action taken", [
                "Contacted family", "Checked learner situation", "Referred for support",
                "Enrolled in remedial tutoring", "Approved feeding fee waiver",
            ])
            note = st.text_area("Note (optional)", height=90, placeholder="Who was contacted, what was agreed, when to follow up.")
            if st.form_submit_button("Save action"):
                save_action(selected, action, note.strip() or "No note added.", user.get("username"))
                st.session_state["flash"] = f"Saved action for {selected} ({s['student_name']})."
                st.rerun()
else:
    st.subheader("Follow-up actions")
    st.info("Recording actions is reserved for School Staff. Your role has read-only access to the case log below.")

st.divider()
st.subheader("Case log")
log_rows = flatten_actions(load_actions())
if not log_rows:
    st.info("No follow-up actions recorded yet.")
else:
    log = pd.DataFrame(log_rows)
    log = log.join(df.set_index("student_id")[["student_name", "school"]], on="student_id")
    log = log.reindex(columns=["timestamp", "student_id", "student_name", "school", "action_type", "note", "recorded_by"])
    log.columns = ["When", "ID", "Learner", "School", "Action", "Note", "Recorded by"]
    show_table(log)

with st.expander("All simulated records"):
    show_table(roster_view(df.sort_values("predicted_risk_pct", ascending=False), include_ubudehe=True))

st.caption("A warning is a prompt for a teacher to follow up, not proof that a learner will drop out.")
render_footer()