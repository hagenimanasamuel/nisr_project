"""RORA main entry point: landing page and the three role consoles."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).parent
FAVICON = BASE_DIR / "favicon.ico"
st.set_page_config(page_title="RORA", page_icon=str(FAVICON) if FAVICON.exists() else ":material/insights:", layout="wide")

from src.analytics import (  # noqa: E402
    COMPONENT_LABELS,
    add_vulnerability_components,
    fit_line,
    roster_view,
    simulate_district_package,
)
from src.auth import get_current_user, render_login_page  # noqa: E402
from src.components import (  # noqa: E402
    BRAND,
    PRIORITY_COLORS,
    PRIORITY_ORDER,
    TIER_COLORS,
    TIER_ORDER,
    callout,
    kpi_row,
    page_header,
    render_footer,
    show_chart,
    show_table,
)
from src.data_loader import get_label, load_multi_source_district_data  # noqa: E402
from src.demo_alerts import load_mock_students  # noqa: E402
from src.layout import render_sidebar  # noqa: E402
from src.prediction_model import get_model_feature_weights, predict_student_risk, run_macro_stress_test  # noqa: E402
from src.style import apply_style  # noqa: E402

apply_style()

# National benchmarks from the NISR EICV7 Education Thematic Report (2023/24).
NATIONAL = {"primary_nar": 92.8, "secondary_nar": 33.7, "primary_repetition": 21.1}
EAST_DROUGHT = ["Nyagatare", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Bugesera"]
INTERVENTIONS = {
    "Emergency school feeding waiver": "feeding_bursary",
    "Remedial teaching and catch-up classes": "academic_remedial",
    "Climate relief linkage (MINEMA)": "climate_shock_relief",
}
MAP_METRICS = [
    "composite_vulnerability_index", "primary_nar", "primary_repetition",
    "poverty_rate", "minema_hazard_index", "feeding_program_coverage",
]
COMPONENT_COLORS = ["#243B5E", "#3B5B8C", "#8DA2C0", "#C9D5E5"]


@st.cache_data(show_spinner=False)
def _districts():
    return load_multi_source_district_data()


@st.cache_data(show_spinner=False)
def _students():
    raw = load_mock_students()
    return raw, (predict_student_risk(raw) if raw is not None else pd.DataFrame())


# --------------------------------------------------------------------------- planner
def planner_console(multi_df, raw_students):
    page_header(
        "National Planner",
        "Where should limited resources go first?",
        "Rank districts, see the pressure behind each ranking, and test a funding package before spending.",
        "The vulnerability index blends poverty (30%), repetition (25%), climate hazard (25%) and the "
        "school access gap (20%). Higher means more children are at risk of falling out.",
    )
    comp, q75 = add_vulnerability_components(multi_df)
    p1 = comp[comp["priority_tier"] == "Priority 1"]

    kpi_row([
        ("Primary NAR (national)", f"{NATIONAL['primary_nar']}%", "Primary net attendance rate, EICV7."),
        ("Primary repetition (national)", f"{NATIONAL['primary_repetition']}%", "Share of primary pupils repeating a grade."),
        ("Priority 1 districts", len(p1), f"Top quartile of the index (score of {q75:.1f} or higher)."),
        ("Avg feeding coverage", f"{comp['feeding_program_coverage'].mean():.1f}%", "Mean school feeding coverage across districts."),
    ])

    tab_rank, tab_map, tab_sim = st.tabs(["District ranking", "Vulnerability map", "Resource simulator"])

    with tab_rank:
        melt = comp.melt(
            id_vars=["district"], value_vars=list(COMPONENT_LABELS),
            var_name="component", value_name="points",
        )
        melt["component"] = melt["component"].map(COMPONENT_LABELS)
        order = comp.sort_values("composite_vulnerability_index")["district"].tolist()
        fig = px.bar(
            melt, x="points", y="district", color="component", orientation="h",
            category_orders={"district": order, "component": list(COMPONENT_LABELS.values())},
            color_discrete_sequence=COMPONENT_COLORS,
            labels={"points": "Index points", "district": "", "component": ""},
            title="What drives each district's vulnerability score",
        )
        show_chart(fig, height=800, key="planner_rank")

        top = p1.sort_values("composite_vulnerability_index", ascending=False)[
            ["district", "composite_vulnerability_index", "dominant_climate_hazard", "feeding_program_coverage"]
        ].rename(columns={
            "district": "District", "composite_vulnerability_index": "Index",
            "dominant_climate_hazard": "Main hazard", "feeding_program_coverage": "Feeding coverage (%)",
        })
        st.markdown("**Priority 1 districts**")
        show_table(top)

    with tab_map:
        metric = st.selectbox("Indicator", MAP_METRICS, format_func=get_label)
        scale = [[0.0, "#D9E2EC"], [0.5, "#627D98"], [1.0, BRAND]]
        try:
            fig = px.scatter_map(
                comp, lat="latitude", lon="longitude", hover_name="district",
                hover_data={"latitude": False, "longitude": False, metric: ":.1f", "priority_tier": True},
                size=metric, color=metric, color_continuous_scale=scale, size_max=28,
                zoom=7.3, center={"lat": -1.94, "lon": 29.87}, map_style="carto-positron",
                labels={metric: get_label(metric)}, title=get_label(metric),
            )
        except Exception:
            fig = px.scatter(
                comp, x="longitude", y="latitude", hover_name="district", size=metric,
                color=metric, color_continuous_scale=scale, title=get_label(metric),
            )
        show_chart(fig, height=560, key="planner_map")

        pri = px.scatter(
            comp, x="poverty_rate", y="primary_repetition", color="priority_tier", hover_name="district",
            color_discrete_map=PRIORITY_COLORS, category_orders={"priority_tier": PRIORITY_ORDER},
            labels={"poverty_rate": "Poverty rate (%)", "primary_repetition": "Primary repetition (%)", "priority_tier": ""},
            title="Priority tiers: poverty against repetition",
        )
        show_chart(pri, height=420, key="planner_pri")

    with tab_sim:
        st.write(
            "Pick where to deploy and what to deploy. RORA re-scores every simulated learner "
            "in the selected districts with the same model used by schools."
        )
        scopes = {
            "Priority 1 districts": p1["district"].tolist(),
            "Drought-exposed eastern districts": EAST_DROUGHT,
            "All 30 districts": comp["district"].tolist(),
        }
        c1, c2 = st.columns(2)
        scope_name = c1.selectbox("Target districts", list(scopes))
        chosen = c2.multiselect(
            "Intervention package", list(INTERVENTIONS),
            default=["Emergency school feeding waiver", "Remedial teaching and catch-up classes"],
        )
        result = simulate_district_package(raw_students, scopes[scope_name], [INTERVENTIONS[c] for c in chosen])
        if result is None:
            callout(
                "Nothing to simulate",
                "Choose at least one intervention, and a target group that includes districts with simulated learners.",
                kind="warn",
            )
            return
        kpi_row([
            ("Learners simulated", result["n"], f"Across {len(result['districts'])} district(s): {', '.join(result['districts'])}."),
            ("Mean risk after", f"{result['mean_after']}%", "Average predicted dropout risk after the package.", f"{result['mean_after'] - result['mean_before']:+.1f} pts"),
            ("High-risk learners after", result["high_after"], "Learners at 70% or higher.", result["high_after"] - result["high_before"]),
        ])
        fig = go.Figure()
        fig.add_bar(name="Before", x=["Mean risk (%)", "High-risk learners"], y=[result["mean_before"], result["high_before"]], marker_color="#8DA2C0")
        fig.add_bar(name="After", x=["Mean risk (%)", "High-risk learners"], y=[result["mean_after"], result["high_after"]], marker_color=BRAND)
        fig.update_layout(barmode="group", title="Impact of the selected package")
        show_chart(fig, height=360, key="planner_sim")
        st.caption("Estimates use simulated learner records in the selected districts and illustrate the method, not a forecast.")


# --------------------------------------------------------------------------- analyst
def analyst_console(multi_df, raw_students):
    page_header(
        "Policy & Data Analyst",
        "What is really driving dropout, and what if things get worse?",
        "Inspect the model, test relationships across sectors, and stress the system with national shocks.",
        "Every coefficient is visible and every flag can be explained, so the model can be checked by "
        "a statistician as easily as by a headteacher.",
    )
    weights = get_model_feature_weights()
    fit = fit_line(multi_df["poverty_rate"], multi_df["primary_repetition"])
    kpi_row([
        ("Model features", len(weights), "Predictors in the logistic model."),
        ("Strongest driver", weights.iloc[0]["Feature"], "Largest odds ratio."),
        ("Poverty vs repetition (r)", f"{fit[2]:+.2f}" if fit else "n/a", "Pearson correlation across the 30 districts."),
        ("Model type", "Logistic", "Transparent, fixed coefficients."),
    ])

    tab_corr, tab_w, tab_stress = st.tabs(["Cross-sector correlation", "Model weights", "Shock stress test"])

    with tab_corr:
        c1, c2 = st.columns(2)
        x = c1.selectbox("X axis", ["poverty_rate", "minema_hazard_index", "primary_nar", "electricity_access"], format_func=get_label)
        y = c2.selectbox("Y axis", ["primary_repetition", "composite_vulnerability_index", "secondary_nar", "feeding_program_coverage"], format_func=get_label)
        fig = px.scatter(
            multi_df, x=x, y=y, hover_name="district", color="dominant_climate_hazard",
            labels={x: get_label(x), y: get_label(y), "dominant_climate_hazard": ""},
            title=f"{get_label(y)} against {get_label(x)}",
        )
        line = fit_line(multi_df[x], multi_df[y])
        if line:
            grid, fitted, r = line
            fig.add_scatter(x=grid, y=fitted, mode="lines", name=f"Trend (r = {r:+.2f})", line=dict(color="#1F2933", dash="dash"))
        show_chart(fig, height=520, key="analyst_corr")

        corr_cols = ["poverty_rate", "extreme_poverty", "electricity_access", "minema_hazard_index",
                     "feeding_program_coverage", "primary_nar", "secondary_nar", "primary_repetition"]
        corr = multi_df[corr_cols].corr().round(2)
        corr.index = corr.columns = [get_label(c).split(" (")[0] for c in corr_cols]
        heat = px.imshow(corr, text_auto=True, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto", title="Correlation matrix")
        show_chart(heat, height=520, key="analyst_heat")

    with tab_w:
        st.write("An odds ratio above 1 raises dropout odds when the condition is present.")
        ordered = weights.sort_values("Odds Ratio")
        fig = px.bar(
            ordered, x="Odds Ratio", y="Feature", color="Domain", orientation="h",
            labels={"Feature": ""}, title="Odds ratio by factor",
        )
        fig.add_vline(x=1, line_dash="dash", line_color="#9AA5B1")
        show_chart(fig, height=460, key="analyst_weights")
        show_table(weights)
        st.latex(r"P(\text{dropout}\mid X)=\frac{1}{1+e^{-z}},\qquad z=-2.60+\sum_i \beta_i x_i")
        st.caption("Tiers: High risk is 70% or more, Moderate risk is 40% to 69%, Low risk is below 40%.")

    with tab_stress:
        scenarios = {
            "drought_wave": "Severe drought in the Eastern and Southern provinces",
            "feeding_budget_cut": "Feeding support cut: partial payers default",
            "universal_remedial": "National remedial programme for low marks",
        }
        key = st.selectbox("Scenario", list(scenarios), format_func=scenarios.get)
        before = predict_student_risk(raw_students)
        after, m = run_macro_stress_test(raw_students, key)
        if not m:
            st.info("No student records available for stress testing.")
            return
        kpi_row([
            ("Baseline mean risk", f"{m['before_mean_risk']}%", "Before the scenario."),
            ("Mean risk after", f"{m['after_mean_risk']}%", "After the scenario.", f"{m['risk_delta']:+.1f} pts"),
            ("High-risk learners", m["after_high_risk_count"], "At 70% or higher.", m["after_high_risk_count"] - m["before_high_risk_count"]),
        ])
        counts = pd.concat([
            before["risk_tier"].value_counts().reindex(TIER_ORDER, fill_value=0).rename("Before"),
            after["risk_tier"].value_counts().reindex(TIER_ORDER, fill_value=0).rename("After"),
        ], axis=1).reset_index().rename(columns={"index": "Risk tier", "risk_tier": "Risk tier"})
        long = counts.melt(id_vars="Risk tier", var_name="Stage", value_name="Learners")
        fig = px.bar(
            long, x="Risk tier", y="Learners", color="Stage", barmode="group",
            category_orders={"Risk tier": TIER_ORDER},
            color_discrete_map={"Before": "#8DA2C0", "After": BRAND}, title="Learners per risk tier",
        )
        show_chart(fig, height=380, key="analyst_stress")


# --------------------------------------------------------------------------- school
def school_console(scored):
    page_header(
        "School Staff",
        "Which child do I talk to today?",
        "A ranked list of learners who need attention, with the main reason for each.",
        "Attendance alone misses children who keep showing up while marks collapse or fees go unpaid. "
        "RORA reads all signals together and names the biggest one.",
    )
    if scored.empty:
        st.error("Simulated student data is missing. Check data/demo/mock_students.csv.")
        return

    hidden = scored[(scored["recent_attendance"] >= 85) & (scored["predicted_risk_pct"] >= 40)]
    kpi_row([
        ("Monitored learners", len(scored), "Simulated records."),
        ("High risk", int((scored["risk_tier"] == "High Risk").sum()), "Predicted risk of 70% or more."),
        ("Feeding fee arrears", int((scored["feeding_fee_status"] == "Defaulted").sum()), "Unpaid school feeding contributions."),
        ("Missed by attendance rules", len(hidden), "Attendance of 85% or more, yet predicted risk of 40% or more."),
    ])

    if len(hidden):
        names = ", ".join(hidden["student_name"].tolist())
        callout(
            "Present in class, still at risk",
            f"<b>{len(hidden)} learner(s)</b> pass a standard attendance check but are flagged by RORA: {names}.",
            kind="warn",
        )

    c1, c2 = st.columns([1.6, 1])
    with c1:
        fig = px.scatter(
            scored, x="recent_attendance", y="term_average_marks", color="risk_tier",
            color_discrete_map=TIER_COLORS, category_orders={"risk_tier": TIER_ORDER},
            hover_name="student_name", hover_data={"school": True, "primary_driver": True, "predicted_risk_pct": ":.1f"},
            labels={"recent_attendance": "Attendance (%)", "term_average_marks": "Term marks (%)", "risk_tier": ""},
            title="Attendance against marks",
        )
        fig.add_vline(x=85, line_dash="dash", line_color="#9AA5B1")
        fig.add_hline(y=55, line_dash="dash", line_color="#9AA5B1")
        fig.update_traces(marker=dict(size=11))
        show_chart(fig, height=420, key="school_scatter")
    with c2:
        tiers = scored["risk_tier"].value_counts().reindex(TIER_ORDER, fill_value=0).reset_index()
        tiers.columns = ["Risk tier", "Learners"]
        fig = px.pie(tiers, names="Risk tier", values="Learners", hole=0.55, color="Risk tier", color_discrete_map=TIER_COLORS, title="Risk tiers")
        show_chart(fig, height=420, key="school_pie")

    drivers = scored[scored["needs_attention"]]["primary_driver"].value_counts().reset_index()
    drivers.columns = ["Main risk factor", "Learners"]
    if not drivers.empty:
        fig = px.bar(drivers.sort_values("Learners"), x="Learners", y="Main risk factor", orientation="h", title="Why learners are flagged")
        fig.update_traces(marker_color=BRAND)
        show_chart(fig, height=300, key="school_drivers")

    st.subheader("Early warning roster")
    f1, f2 = st.columns(2)
    school = f1.selectbox("School", ["All schools"] + sorted(scored["school"].unique()))
    tier = f2.selectbox("Risk tier", ["All tiers"] + TIER_ORDER)
    view = scored
    if school != "All schools":
        view = view[view["school"] == school]
    if tier != "All tiers":
        view = view[view["risk_tier"] == tier]
    table = roster_view(view.sort_values("predicted_risk_pct", ascending=False))
    show_table(table, column_config={
        "Predicted risk (%)": st.column_config.ProgressColumn("Predicted risk (%)", min_value=0, max_value=100, format="%.1f"),
    })
    st.page_link("pages/2_Early_Intervention.py", label="Open the Student 360 case view", icon=":material/flag:")


# --------------------------------------------------------------------------- router
user = get_current_user()
if not user:
    render_login_page()
else:
    render_sidebar(current_page="Home")
    multi = _districts()
    if multi is None or multi.empty:
        st.error("District data is missing or unreadable. Check data/nisr/.")
        st.stop()
    raw, scored = _students()

    role = user.get("role")
    if role == "planner":
        planner_console(multi, raw)
    elif role == "analyst":
        analyst_console(multi, raw)
    else:
        school_console(scored)
    render_footer()