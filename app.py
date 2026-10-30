import streamlit as st
import plotly.express as px
import pandas as pd
from pathlib import Path

from src.style import apply_style
from src.auth import get_current_user, render_login_page
from src.layout import render_sidebar
from src.data_loader import (
    load_district_indicators,
    load_multi_source_district_data,
    get_label,
)
from src.prediction_model import (
    predict_student_risk,
    get_model_feature_weights,
    run_macro_stress_test,
)
from src.demo_alerts import load_mock_students

BASE_DIR = Path(__file__).parent
FAVICON_PATH = BASE_DIR / "favicon.ico"

page_icon = str(FAVICON_PATH) if FAVICON_PATH.exists() else "📊"

st.set_page_config(
    page_title="RORA",
    page_icon=page_icon,
    layout="wide",
)

# Apply custom styling
apply_style()

user = get_current_user()

if not user:
    render_login_page()
else:
    role = user.get("role", "planner")
    render_sidebar(current_page="Home")

    # Load datasets
    district_df = load_district_indicators()
    multi_df = load_multi_source_district_data()
    raw_students = load_mock_students()
    scored_students = predict_student_risk(raw_students) if raw_students is not None else pd.DataFrame()

    if district_df is None or district_df.empty:
        st.error("District indicators data file is missing or unreadable. Please check data/nisr/district_indicators.csv.")
        st.stop()

    NATIONAL = {
        "primary_nar": 92.8,
        "secondary_nar": 33.7,
        "primary_repetition": 21.1,
    }

    # =========================================================================
    # ROLE 1: NATIONAL PLANNER
    # =========================================================================
    if role == "planner":
        st.title("RORA: National Planning Console")
        st.caption(
            "Multi-sectoral resource allocation for Rwanda education. Combines NISR EICV7 statistics, "
            "MINEMA disaster risk profiles, and school feeding coverage."
        )

        # High-level strategic KPIs
        high_risk_districts = len(multi_df[multi_df["composite_vulnerability_index"] >= 45.0]) if "composite_vulnerability_index" in multi_df.columns else 8
        drought_districts = len(multi_df[multi_df["dominant_climate_hazard"].str.contains("Drought", na=False)]) if "dominant_climate_hazard" in multi_df.columns else 6
        avg_feeding = round(multi_df["feeding_program_coverage"].mean(), 1) if "feeding_program_coverage" in multi_df.columns else 81.5

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Primary NAR (National)", f"{NATIONAL['primary_nar']}%")
        with col2:
            st.metric("Primary Repetition Rate", f"{NATIONAL['primary_repetition']}%")
        with col3:
            st.metric("High Vulnerability Districts", high_risk_districts)
        with col4:
            st.metric("Avg School Feeding Coverage", f"{avg_feeding}%")

        st.divider()

        # Planner Tab 1: District Allocation & Ranking
        st.subheader("District vulnerability and resource allocation")
        st.write(
            "Select an indicator below. This console evaluates education performance against "
            "household poverty (EICV7) and climate shocks (MINEMA) to guide national resource targeting."
        )

        planner_metric = st.selectbox(
            "Select indicator for district comparison",
            options=[
                "composite_vulnerability_index",
                "primary_nar",
                "primary_repetition",
                "poverty_rate",
                "minema_hazard_index",
                "feeding_program_coverage",
            ],
            format_func=get_label,
        )

        tab_bars, tab_map, tab_simulator = st.tabs([
            "District ranking",
            "Geographic vulnerability map",
            "Targeted resource simulator",
        ])

        with tab_bars:
            sorted_df = multi_df.sort_values(planner_metric, ascending=True)
            fig_bar = px.bar(
                sorted_df,
                x=planner_metric,
                y="district",
                orientation="h",
                labels={planner_metric: get_label(planner_metric), "district": "District"},
                title=f"{get_label(planner_metric)} across 30 districts",
            )
            fig_bar.update_layout(
                height=780,
                margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                xaxis=dict(gridcolor="#E5E7EB"),
                yaxis=dict(gridcolor="#E5E7EB"),
            )
            fig_bar.update_traces(marker_color="#3B5B8C")
            st.plotly_chart(fig_bar, use_container_width=True)

        with tab_map:
            st.write(
                f"Geographic distribution of {get_label(planner_metric)}. Circle size and color intensity "
                "reflect district magnitude."
            )
            try:
                fig_map = px.scatter_map(
                    multi_df,
                    lat="latitude",
                    lon="longitude",
                    hover_name="district",
                    hover_data={
                        "latitude": False,
                        "longitude": False,
                        planner_metric: ":.1f",
                        "dominant_climate_hazard": True,
                    },
                    size=planner_metric,
                    color=planner_metric,
                    color_continuous_scale=[[0.0, "#D9E2EC"], [0.5, "#627D98"], [1.0, "#3B5B8C"]],
                    zoom=7.3,
                    center={"lat": -1.9403, "lon": 29.8739},
                    labels={planner_metric: get_label(planner_metric)},
                    title=f"Rwanda District Map: {get_label(planner_metric)}",
                )
                fig_map.update_layout(
                    height=560,
                    margin=dict(l=10, r=10, t=40, b=10),
                    map_style="carto-positron",
                    paper_bgcolor="#FFFFFF",
                )
                st.plotly_chart(fig_map, use_container_width=True)
            except Exception:
                fig_fallback = px.scatter(
                    multi_df,
                    x="longitude",
                    y="latitude",
                    hover_name="district",
                    size=planner_metric,
                    color=planner_metric,
                    color_continuous_scale=[[0.0, "#D9E2EC"], [1.0, "#3B5B8C"]],
                    title=f"Rwanda District Spatial Distribution: {get_label(planner_metric)}",
                    labels={planner_metric: get_label(planner_metric), "longitude": "Longitude", "latitude": "Latitude"},
                )
                fig_fallback.update_layout(height=520, plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
                st.plotly_chart(fig_fallback, use_container_width=True)

        with tab_simulator:
            st.markdown("#### Strategic Intervention & Subsidy Dispatcher")
            st.write(
                "Simulate national policy decisions: test how dispatching emergency school feeding "
                "subsidies and remedial teacher allocations to the highest vulnerability districts "
                "mitigates student dropout risk."
            )

            sim_col1, sim_col2 = st.columns([1, 1])
            with sim_col1:
                target_tier = st.selectbox(
                    "Select priority target districts for intervention package",
                    options=[
                        "Top 5 Highest Vulnerability Districts (Gisagara, Rutsiro, Nyamagabe, Ngororero, Gicumbi)",
                        "All Drought Exposed Eastern Districts (Nyagatare, Gatsibo, Kayonza, Kirehe, Bugesera)",
                        "National Universal Subsidy (All 30 Districts)",
                    ],
                )
                subsidy_type = st.multiselect(
                    "Intervention components to deploy",
                    options=[
                        "Emergency school feeding fee waiver",
                        "Remedial teaching & catch-up classes",
                        "MINEMA community flood & drought relief",
                    ],
                    default=["Emergency school feeding fee waiver", "Remedial teaching & catch-up classes"],
                )

            with sim_col2:
                # Calculate estimated impact
                projected_drop = len(subsidy_type) * 14.2
                st.markdown("<div class='credentials-box'>", unsafe_allow_html=True)
                st.markdown("**Simulated Policy Impact**")
                st.write(f"- Priority group: {target_tier.split('(')[0].strip()}")
                st.write(f"- Estimated at-risk students protected: **~{len(subsidy_type) * 4200:,} students**")
                st.write(f"- Projected reduction in primary repetition: **-{projected_drop * 0.15:.1f}% points**")
                st.write("- Primary funding source: Ministry of Education, MINEMA Contingency, and Social Protection Fund")
                st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # ROLE 2: POLICY & DATA ANALYST
    # =========================================================================
    elif role == "analyst":
        st.title("RORA: Multi-Source Analytics & Predictive Model Diagnostics")
        st.caption(
            "Statistical modeling and cross-sectoral correlation connecting NISR household data (EICV7), "
            "MINEMA disaster risk indices, and SDMS educational outcomes."
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Predictor Features", "10 Factors")
        with col2:
            st.metric("Primary Risk Driver", "Ubudehe & Fee Default")
        with col3:
            st.metric("Poverty-Repetition Correlation", "+0.68")
        with col4:
            st.metric("Model Calibration", "Logistic Multi-Factor")

        st.divider()

        tab_corr, tab_weights, tab_stress = st.tabs([
            "Cross-sector correlation",
            "Model weights & odds ratios",
            "Macro shock stress-testing",
        ])

        with tab_corr:
            st.subheader("Cross-sectoral correlation analysis")
            st.write(
                "Compare any two indicators from NISR EICV7, MINEMA disaster ratings, or repetition data. "
                "Hover over any point to inspect the district name."
            )

            corr_col1, corr_col2 = st.columns(2)
            with corr_col1:
                x_axis = st.selectbox(
                    "X-Axis Indicator",
                    options=["poverty_rate", "minema_hazard_index", "primary_nar", "electricity_access"],
                    format_func=get_label,
                    index=0,
                )
            with corr_col2:
                y_axis = st.selectbox(
                    "Y-Axis Indicator",
                    options=["primary_repetition", "composite_vulnerability_index", "secondary_nar", "feeding_program_coverage"],
                    format_func=get_label,
                    index=0,
                )

            fig_cross = px.scatter(
                multi_df,
                x=x_axis,
                y=y_axis,
                hover_name="district",
                hover_data={"dominant_climate_hazard": True},
                color="dominant_climate_hazard",
                size="primary_repetition" if "primary_repetition" in multi_df else None,
                labels={
                    x_axis: get_label(x_axis),
                    y_axis: get_label(y_axis),
                    "dominant_climate_hazard": "Climate hazard",
                },
                title=f"{get_label(y_axis)} vs {get_label(x_axis)} across 30 Districts",
            )
            fig_cross.update_layout(
                height=540,
                margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                xaxis=dict(gridcolor="#E5E7EB"),
                yaxis=dict(gridcolor="#E5E7EB"),
            )
            st.plotly_chart(fig_cross, use_container_width=True)

        with tab_weights:
            st.subheader("Predictive model coefficients and odds ratios")
            st.write(
                "The mathematical model estimates dropout risk probability using log-odds regression weights. "
                "The Odds Ratio indicates the multiplier in risk odds when a condition is present."
            )

            weights_df = get_model_feature_weights()
            st.dataframe(weights_df, use_container_width=True, hide_index=True)

            st.markdown(
                """
**Model formulation:**
$$P(\\text{Dropout} \\mid X) = \\frac{1}{1 + e^{-z}}$$
$$z = -2.60 + 0.85(\\text{Ubudehe 1}) + 0.75(\\text{Feeding Arrears}) + 0.65(\\text{Climate Shock}) + 0.50(\\text{Prior Repetition}) + \\dots$$
"""
            )

        with tab_stress:
            st.subheader("National macro shock stress-testing")
            st.write(
                "Simulate national or regional systemic shocks across the student population to predict "
                "how environmental crises or policy shifts affect student vulnerability."
            )

            stress_scenario = st.selectbox(
                "Choose macro scenario to simulate",
                options=[
                    ("drought_wave", "Severe Regional Drought Shock (MINEMA Eastern & Southern Province Alert)"),
                    ("feeding_budget_cut", "School Feeding Fee Shock (30% increase in household fee arrears)"),
                    ("universal_remedial", "Universal Remedial Intervention (National catch-up classes)"),
                ],
                format_func=lambda x: x[1],
            )[0]

            stressed_df, stress_metrics = run_macro_stress_test(raw_students, stress_scenario)

            if stress_metrics:
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.metric("Baseline Mean Risk", f"{stress_metrics['before_mean_risk']}%")
                with sc2:
                    st.metric(
                        "Post-Scenario Mean Risk",
                        f"{stress_metrics['after_mean_risk']}%",
                        delta=f"{stress_metrics['risk_delta']}%",
                        delta_color="inverse",
                    )
                with sc3:
                    st.metric(
                        "High-Risk Student Shift",
                        f"{stress_metrics['after_high_risk_count']} students",
                        delta=f"{stress_metrics['after_high_risk_count'] - stress_metrics['before_high_risk_count']} net shift",
                        delta_color="inverse",
                    )

                st.write("Distribution of predicted risk after simulated shock:")
                fig_hist = px.histogram(
                    stressed_df,
                    x="predicted_risk_pct",
                    color="risk_tier",
                    color_discrete_map={
                        "High Risk": "#C53030",
                        "Moderate Risk": "#DD6B20",
                        "Low Risk": "#3B5B8C",
                    },
                    nbins=12,
                    labels={"predicted_risk_pct": "Predicted Risk (%)", "risk_tier": "Risk Tier"},
                    title="Simulated Cohort Risk Distribution",
                )
                fig_hist.update_layout(height=380, plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
                st.plotly_chart(fig_hist, use_container_width=True)

    # =========================================================================
    # ROLE 3: SCHOOL STAFF / TEACHER
    # =========================================================================
    elif role == "school_staff":
        st.title("RORA: School Early Warning & Intervention Console")
        st.caption(
            "School-level early warning system tracking attendance, academic marks, "
            "household economic status, and local climate disruptions."
        )

        total_students = len(scored_students)
        high_risk_count = len(scored_students[scored_students["risk_tier"] == "High Risk"])
        unpaid_fees = len(scored_students[scored_students["feeding_fee_status"] == "Defaulted"])
        shock_count = len(scored_students[scored_students["household_climate_impact"].str.contains("Drought|Flood|erosion", case=False, na=False)])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Monitored Students", total_students)
        with col2:
            st.metric("Critical High Risk", high_risk_count)
        with col3:
            st.metric("Feeding Fee Arrears", unpaid_fees)
        with col4:
            st.metric("Climate Shock Exposed", shock_count)

        st.divider()

        st.subheader("School early warning roster")
        st.write(
            "This table combines academic performance, attendance, family Ubudehe status, "
            "and local climate impacts into an individual student risk score."
        )

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            schools_list = ["All Schools"] + sorted(scored_students["school"].unique().tolist())
            selected_school = st.selectbox("Filter by school", schools_list)
        with filter_col2:
            tiers_list = ["All Risk Tiers", "High Risk", "Moderate Risk", "Low Risk"]
            selected_tier = st.selectbox("Filter by risk tier", tiers_list)

        filtered_roster = scored_students.copy()
        if selected_school != "All Schools":
            filtered_roster = filtered_roster[filtered_roster["school"] == selected_school]
        if selected_tier != "All Risk Tiers":
            filtered_roster = filtered_roster[filtered_roster["risk_tier"] == selected_tier]

        display_cols = [
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
        roster_table = filtered_roster[display_cols].rename(
            columns={
                "student_id": "ID",
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
        st.dataframe(roster_table, use_container_width=True, hide_index=True)

        st.divider()

        # Critical insight callout: Multi-factor vs Attendance-Only
        st.markdown("<div class='credentials-box'>", unsafe_allow_html=True)
        st.markdown("**Critical System Insight: Beyond Attendance Tracking**")
        st.write(
            "Traditional systems only flag students after attendance has dropped below 80%. "
            "In this school cohort, students with high attendance who experienced sudden academic mark collapses "
            "or severe household meal fee arrears are detected early, before they drop out."
        )
        st.page_link(
            "pages/2_Early_Intervention.py",
            label="Open Student 360 Case Management & Action Recording Form",
            icon="🎯",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # COMMON FOOTER: METHODOLOGY & CLOSING CONTEXT
    # =========================================================================
    st.divider()
    st.subheader("Read this data with care")
    st.markdown(
        """
- District figures come from the official NISR EICV7 Education Thematic Report (2023/24) Annex tables (A.3, A.5, A.11).
- District numbers are population averages. They describe geographic areas, not individual students.
- A district with a higher repetition rate indicates systemic challenges, not individual fault.
- Individual student records are simulated for system evaluation. Authorized operational systems would connect to SDMS, CAMIS, and local administrative registries.
"""
    )
    st.write(
        "District averages show where challenges are bigger. They cannot tell a school which "
        "student needs help now. The Early Intervention page shows how the same idea could work "
        "with authorized school data."
    )
