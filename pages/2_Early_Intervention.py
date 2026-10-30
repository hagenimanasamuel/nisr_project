import streamlit as st
import pandas as pd
from pathlib import Path

from src.style import apply_style
from src.auth import get_current_user
from src.layout import render_sidebar
from src.demo_alerts import load_mock_students
from src.prediction_model import predict_student_risk, simulate_intervention
from src.follow_up import load_actions, save_action

BASE_DIR = Path(__file__).parent.parent
FAVICON_PATH = BASE_DIR / "favicon.ico"

page_icon = str(FAVICON_PATH) if FAVICON_PATH.exists() else "🎯"

st.set_page_config(
    page_title="Early Intervention: RORA",
    page_icon=page_icon,
    layout="wide",
)

# Apply custom styling
apply_style()

user = get_current_user()

if not user:
    st.warning("Authentication required. Please sign in to view Early Intervention.")
    st.page_link("app.py", label="Go to sign in", icon="🔒")
    st.stop()

# Render shared sidebar with fast role switcher
render_sidebar(current_page="Early Intervention")

st.title("Early Intervention & Case Management")

# Top paragraph explaining the gap
st.write(
    "District data cannot see individual students. This page simulates how authorized "
    "school-level data from systems such as SDMS or CAMIS could be used to identify "
    "attendance, academic, and socio-economic risks early and organize timely student support."
)

# Required single line note
st.caption("Student records on this page are simulated. No real student data is used.")

raw_df = load_mock_students()
if raw_df is None or raw_df.empty:
    st.error("Simulated student data file is missing or unreadable. Please check data/demo/mock_students.csv.")
    st.stop()

df = predict_student_risk(raw_df)
if df is None or df.empty:
    st.error("Could not process risk prediction on student records.")
    st.stop()

flagged = df[df["needs_attention"]]
not_flagged = df[~df["needs_attention"]]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Flagged students", len(flagged))
with col2:
    st.metric("Students without warnings", len(not_flagged))
with col3:
    critical_count = len(df[df["risk_tier"] == "High Risk"])
    st.metric("Critical High Risk (≥70%)", critical_count)

st.divider()

st.subheader("Students who need follow-up")
st.write("These records meet transparent warning criteria across attendance, marks, economics, and climate shocks.")

st.markdown(
    """
**Multi-factor risk indicators monitored:**
- Attendance: Recent attendance below 80 percent, 3 or more consecutive absences, or sharp drop
- Academic marks: Recent term marks below 55 percent or downward trajectory
- Household economic situation: Ubudehe Category 1 and school feeding fee arrears
- Local shocks: Exposure to flood, landslide, or drought disruptions (MINEMA / Meteo data)
"""
)

if flagged.empty:
    st.info("No students currently meet the warning criteria.")
else:
    table_flagged = flagged[
        [
            "student_id",
            "student_name",
            "school",
            "district",
            "grade_level",
            "predicted_risk_pct",
            "risk_tier",
            "primary_driver",
            "term_average_marks",
            "recent_attendance",
            "feeding_fee_status",
            "household_climate_impact",
        ]
    ].rename(
        columns={
            "student_id": "Student ID",
            "student_name": "Student Name",
            "school": "School",
            "district": "District",
            "grade_level": "Grade",
            "predicted_risk_pct": "Predicted Risk (%)",
            "risk_tier": "Risk Tier",
            "primary_driver": "Primary Risk Factor",
            "term_average_marks": "Marks (%)",
            "recent_attendance": "Attendance (%)",
            "feeding_fee_status": "Feeding Fee",
            "household_climate_impact": "Climate Shock",
        }
    )
    st.dataframe(table_flagged, use_container_width=True, hide_index=True)

st.divider()

# =============================================================================
# ROLE-BASED CASE MANAGEMENT & WHAT-IF INTERVENTION SIMULATOR
# =============================================================================
user_role = user.get("role", "")

if user_role == "school_staff":
    st.subheader("Student 360 case evaluation and intervention simulator")
    st.write(
        "Choose one flagged student below. Inspect their full profile, simulate how specific "
        "interventions would reduce their predicted risk, and log the action taken."
    )

    if flagged.empty:
        st.info("There are no students with active warnings right now.")
    else:
        student_id_options = flagged["student_id"].tolist()
        student_display_map = {
            sid: f"{sid}: {flagged.loc[flagged['student_id'] == sid, 'student_name'].values[0]} ({flagged.loc[flagged['student_id'] == sid, 'school'].values[0]})"
            for sid in student_id_options
        }
        selected_id = st.selectbox(
            "Select student to evaluate",
            options=student_id_options,
            format_func=lambda x: student_display_map[x],
        )

        student_row = flagged[flagged["student_id"] == selected_id].iloc[0]

        # 360 Profile Cards
        profile_col1, profile_col2, profile_col3, profile_col4 = st.columns(4)
        with profile_col1:
            st.markdown("<div class='credentials-box'>", unsafe_allow_html=True)
            st.markdown("**Student Identity**")
            st.write(f"Name: **{student_row['student_name']}**")
            st.write(f"School: {student_row['school']}")
            st.write(f"District: {student_row['district']}")
            st.write(f"Grade: {student_row['grade_level']}")
            st.markdown("</div>", unsafe_allow_html=True)

        with profile_col2:
            st.markdown("<div class='credentials-box'>", unsafe_allow_html=True)
            st.markdown("**Academic Profile (SDMS)**")
            st.write(f"Term Marks: **{student_row['term_average_marks']}%**")
            st.write(f"Marks Trend: {student_row['marks_trend']}%")
            st.write(f"Prior Repetition: {student_row['prior_grade_repetition']}")
            st.markdown("</div>", unsafe_allow_html=True)

        with profile_col3:
            st.markdown("<div class='credentials-box'>", unsafe_allow_html=True)
            st.markdown("**Attendance Profile**")
            st.write(f"Attendance: **{student_row['recent_attendance']}%**")
            st.write(f"Consecutive Absences: {student_row['consecutive_absences']} days")
            st.write(f"Previous Term: {student_row['previous_attendance']}%")
            st.markdown("</div>", unsafe_allow_html=True)

        with profile_col4:
            st.markdown("<div class='credentials-box'>", unsafe_allow_html=True)
            st.markdown("**Socio-Economic & Climate**")
            st.write(f"Ubudehe Category: Cat {student_row['ubudehe_category']}")
            st.write(f"Feeding Fee: **{student_row['feeding_fee_status']}**")
            st.write(f"Climate Shock: {student_row['household_climate_impact']}")
            st.markdown("</div>", unsafe_allow_html=True)

        # Factor Attribution Progress Bars
        st.markdown("#### Factor Attribution Breakdown")
        st.write("Percentage of the student's risk probability contributed by each factor domain:")
        bar_col1, bar_col2 = st.columns([1, 1])
        with bar_col1:
            st.write(f"Academic Performance: **{student_row['academic_contrib_pct']}%**")
            st.progress(min(1.0, float(student_row['academic_contrib_pct']) / 100.0))
            st.write(f"Household Poverty & Fees: **{student_row['economic_contrib_pct']}%**")
            st.progress(min(1.0, float(student_row['economic_contrib_pct']) / 100.0))
        with bar_col2:
            st.write(f"Attendance Deficit: **{student_row['attendance_contrib_pct']}%**")
            st.progress(min(1.0, float(student_row['attendance_contrib_pct']) / 100.0))
            st.write(f"Climate & Commute Shocks: **{student_row['shock_contrib_pct']}%**")
            st.progress(min(1.0, float(student_row['shock_contrib_pct']) / 100.0))

        st.markdown("---")

        # Interactive What-If Intervention Simulator
        st.markdown("#### What-If Intervention Simulator")
        st.write(
            "Select proposed interventions below to see how this student's predicted risk score "
            "changes before committing real resources."
        )

        sim_opts_col, sim_result_col = st.columns([1.2, 1])

        with sim_opts_col:
            apply_feeding = st.checkbox("Grant School Feeding Bursary (clears feeding fee arrears)", value=True)
            apply_remedial = st.checkbox("Enroll in Remedial Tutoring (recovers marks by +16%)", value=True)
            apply_mentoring = st.checkbox("Assign Attendance Mentor & Home Visit (resolves absences)", value=False)
            apply_relief = st.checkbox("Link to MINEMA Community Climate Relief", value=False)

            active_interventions = []
            if apply_feeding:
                active_interventions.append("feeding_bursary")
            if apply_remedial:
                active_interventions.append("academic_remedial")
            if apply_mentoring:
                active_interventions.append("attendance_mentoring")
            if apply_relief:
                active_interventions.append("climate_shock_relief")

        with sim_result_col:
            sim_output = simulate_intervention(student_row, active_interventions)
            st.markdown("<div class='credentials-box'>", unsafe_allow_html=True)
            st.markdown("**Simulated Intervention Outcome**")
            st.write(f"- Baseline Risk: **{sim_output['original_prob']}%**")
            st.write(f"- Post-Intervention Risk: **{sim_output['simulated_prob']}%**")
            st.write(f"- Risk Reduction: **-{sim_output['delta_reduction']}% points**")
            st.write(f"- New Status: **{sim_output['new_tier']}**")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Action Recording Form
        st.markdown("#### Record a follow-up action")
        st.write("Record the actual step taken by the school team. Stored in the local case registry.")

        with st.form("action_form"):
            action_type = st.selectbox(
                "Action taken",
                options=[
                    "Contacted family",
                    "Checked student situation",
                    "Referred for support",
                    "Enrolled in remedial tutoring",
                    "Approved school feeding subsidy waiver",
                ],
            )
            note = st.text_area(
                "Short note (optional)",
                placeholder="Enter details of contact, agreed actions with parents, or support schedule...",
                height=90,
            )
            submitted = st.form_submit_button("Save action")

            if submitted:
                final_note = note.strip() if note.strip() else "No note added."
                save_action(
                    student_id=selected_id,
                    action_type=action_type,
                    note=final_note,
                    recorded_by=user.get("username", "school_staff"),
                )
                st.success(f"Saved action for {selected_id} ({student_row['student_name']}).")
                st.rerun()

else:
    # Read-only notice for planner and analyst roles
    st.subheader("Follow-up actions")
    st.info(
        "Action recording is reserved for School Staff. Planners and analysts have read-only access "
        "to monitor recorded interventions across schools and evaluate program efficacy."
    )

st.divider()

st.subheader("Saved follow-up actions")
st.write("These records track interventions taken for flagged students across schools.")

actions = load_actions()
if not actions:
    st.info("No follow-up actions saved yet.")
else:
    action_records = []
    for sid, data in actions.items():
        # Match student name if available
        matched = df[df["student_id"] == sid]
        s_name = matched["student_name"].values[0] if not matched.empty else sid
        s_school = matched["school"].values[0] if not matched.empty else "N/A"

        entry = {
            "Student ID": sid,
            "Student Name": s_name,
            "School": s_school,
            "Action Type": data.get("action_type", ""),
            "Note": data.get("note", ""),
        }
        if "recorded_by" in data:
            entry["Recorded By"] = data["recorded_by"]
        action_records.append(entry)

    actions_df = pd.DataFrame(action_records)
    st.dataframe(actions_df, use_container_width=True, hide_index=True)

st.divider()

st.subheader("All simulated records")
st.write("Complete set of simulated records across all schools without risk filters applied.")
all_table = df[
    [
        "student_id",
        "student_name",
        "school",
        "district",
        "grade_level",
        "predicted_risk_pct",
        "risk_tier",
        "primary_driver",
        "term_average_marks",
        "recent_attendance",
        "ubudehe_category",
        "feeding_fee_status",
        "household_climate_impact",
    ]
].rename(
    columns={
        "student_id": "Student ID",
        "student_name": "Student Name",
        "school": "School",
        "district": "District",
        "grade_level": "Grade",
        "predicted_risk_pct": "Predicted Risk (%)",
        "risk_tier": "Risk Tier",
        "primary_driver": "Primary Risk Factor",
        "term_average_marks": "Marks (%)",
        "recent_attendance": "Attendance (%)",
        "ubudehe_category": "Ubudehe",
        "feeding_fee_status": "Feeding Fee",
        "household_climate_impact": "Climate Shock",
    }
)
st.dataframe(all_table, use_container_width=True, hide_index=True)

st.caption(
    "This page shows how a school could use attendance data to spot students who may need support. "
    "A warning is not proof that a student will drop out. It is a signal for a teacher or staff member to follow up."
)
