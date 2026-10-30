import numpy as np
import pandas as pd


# Baseline intercept for population log-odds
BASE_INTERCEPT = -2.60

# Model feature coefficients (log-odds weights)
MODEL_WEIGHTS = {
    "attendance_deficit": 0.045,      # Per point below 85% attendance
    "consecutive_absences": 0.35,     # Per consecutive absence beyond threshold
    "attendance_drop": 0.030,         # Per point dropped from previous term
    "marks_deficit": 0.045,           # Per mark below 55% average
    "marks_drop": 0.035,              # Per mark dropped from previous term
    "ubudehe_cat1": 0.85,             # Household in Ubudehe Category 1
    "ubudehe_cat2": 0.40,             # Household in Ubudehe Category 2
    "feeding_defaulted": 0.75,        # Unpaid feeding fee / meal arrears
    "feeding_partial": 0.35,          # Partial feeding fee balance
    "climate_shock": 0.65,            # Household impacted by drought, flood, or food stress
    "long_distance": 0.40,            # Distance to school > 4 km
    "prior_repetition": 0.50,         # Student has previously repeated a grade
}


def calculate_student_log_odds(row):
    """
    Computes individual factor contributions and total log-odds.
    Returns (total_z, components_dict).
    """
    comps = {
        "attendance": 0.0,
        "academic": 0.0,
        "socioeconomic": 0.0,
        "climate_shock": 0.0,
        "geographic": 0.0,
    }

    # 1. Attendance components
    att = float(row.get("recent_attendance", 90.0))
    prev_att = float(row.get("previous_attendance", att))
    consec = float(row.get("consecutive_absences", 0))

    if att < 85.0:
        comps["attendance"] += (85.0 - att) * MODEL_WEIGHTS["attendance_deficit"]
    if consec >= 3:
        comps["attendance"] += consec * MODEL_WEIGHTS["consecutive_absences"]
    if att < prev_att - 8.0:
        comps["attendance"] += (prev_att - att) * MODEL_WEIGHTS["attendance_drop"]

    # 2. Academic marks components
    marks = float(row.get("term_average_marks", 70.0))
    trend = float(row.get("marks_trend", 0.0))

    if marks < 55.0:
        comps["academic"] += (55.0 - marks) * MODEL_WEIGHTS["marks_deficit"]
    if trend < -8.0:
        comps["academic"] += (-trend) * MODEL_WEIGHTS["marks_drop"]
    if str(row.get("prior_grade_repetition", "No")).strip().lower() in ["yes", "true", "1"]:
        comps["academic"] += MODEL_WEIGHTS["prior_repetition"]

    # 3. Socio-economic & school feeding components
    ubudehe = int(row.get("ubudehe_category", 2))
    if ubudehe == 1:
        comps["socioeconomic"] += MODEL_WEIGHTS["ubudehe_cat1"]
    elif ubudehe == 2:
        comps["socioeconomic"] += MODEL_WEIGHTS["ubudehe_cat2"]

    feeding = str(row.get("feeding_fee_status", "Paid")).strip()
    if feeding == "Defaulted":
        comps["socioeconomic"] += MODEL_WEIGHTS["feeding_defaulted"]
    elif feeding == "Partial":
        comps["socioeconomic"] += MODEL_WEIGHTS["feeding_partial"]

    # 4. Climate & environmental shock components
    shock = str(row.get("household_climate_impact", "None")).strip()
    if shock != "None" and shock != "":
        comps["climate_shock"] += MODEL_WEIGHTS["climate_shock"]

    # 5. Geographic & distance components
    distance = float(row.get("distance_to_school_km", 2.0))
    if distance > 4.0:
        comps["geographic"] += MODEL_WEIGHTS["long_distance"]

    total_z = BASE_INTERCEPT + sum(comps.values())
    return total_z, comps


def predict_student_risk(df):
    """
    Applies the multi-factor predictive model to student records.
    Returns an enriched DataFrame with predicted risk probability, risk tier,
    primary driver, factor contributions, and prescribed actions.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    out_df = df.copy()

    probs = []
    tiers = []
    drivers = []
    prescriptions = []
    att_contribs = []
    acad_contribs = []
    econ_contribs = []
    shock_contribs = []

    driver_labels = {
        "academic": "Academic performance drop",
        "socioeconomic": "Household poverty & fee arrears",
        "attendance": "Severe attendance deficit",
        "climate_shock": "Climate & weather disruption",
        "geographic": "Long commute distance",
    }

    action_map = {
        "academic": "Enroll in remedial tutoring & academic recovery",
        "socioeconomic": "Grant school feeding waiver & emergency bursary",
        "attendance": "Conduct home visit & attendance mentoring",
        "climate_shock": "Refer to MINEMA community relief & nutrition support",
        "geographic": "Arrange community bicycle or safe walking cluster",
    }

    for _, row in out_df.iterrows():
        z, comps = calculate_student_log_odds(row)
        prob = 1.0 / (1.0 + np.exp(-z))
        prob_pct = round(prob * 100.0, 1)

        # Risk tier
        if prob_pct >= 70.0:
            tier = "High Risk"
        elif prob_pct >= 40.0:
            tier = "Moderate Risk"
        else:
            tier = "Low Risk"

        # Factor contributions breakdown
        total_risk_factors = sum(comps.values())
        if total_risk_factors > 0.05:
            att_share = round((comps["attendance"] / total_risk_factors) * 100.0, 1)
            acad_share = round((comps["academic"] / total_risk_factors) * 100.0, 1)
            econ_share = round((comps["socioeconomic"] / total_risk_factors) * 100.0, 1)
            shock_share = round(((comps["climate_shock"] + comps["geographic"]) / total_risk_factors) * 100.0, 1)

            # Determine dominant driver
            top_comp = max(comps, key=comps.get)
            driver = driver_labels.get(top_comp, "Multiple compound factors")
            action = action_map.get(top_comp, "Comprehensive family case review")
        else:
            att_share = 0.0
            acad_share = 0.0
            econ_share = 0.0
            shock_share = 0.0
            driver = "No significant risk factors"
            action = "Routine monitoring"

        probs.append(prob_pct)
        tiers.append(tier)
        drivers.append(driver)
        prescriptions.append(action)
        att_contribs.append(att_share)
        acad_contribs.append(acad_share)
        econ_contribs.append(econ_share)
        shock_contribs.append(shock_share)

    out_df["predicted_risk_pct"] = probs
    out_df["risk_tier"] = tiers
    out_df["primary_driver"] = drivers
    out_df["prescribed_action"] = prescriptions
    out_df["attendance_contrib_pct"] = att_contribs
    out_df["academic_contrib_pct"] = acad_contribs
    out_df["economic_contrib_pct"] = econ_contribs
    out_df["shock_contrib_pct"] = shock_contribs

    # Keep backward compatibility with rule-based flag
    out_df["needs_attention"] = out_df["predicted_risk_pct"] >= 40.0
    out_df["alert_reason"] = out_df["primary_driver"] + " (" + out_df["predicted_risk_pct"].astype(str) + "% risk)"

    return out_df


def simulate_intervention(student_row, applied_interventions):
    """
    Simulates hypothetical interventions on a single student record.
    Returns:
    - original_prob: baseline risk probability (%)
    - simulated_prob: post-intervention risk probability (%)
    - delta: reduction in percentage points
    - updated_tier: new risk tier
    """
    row_copy = student_row.to_dict() if hasattr(student_row, "to_dict") else dict(student_row)

    # 1. Baseline
    z_base, _ = calculate_student_log_odds(row_copy)
    prob_base = float(round((1.0 / (1.0 + np.exp(-z_base))) * 100.0, 1))

    # 2. Apply interventions
    if "feeding_bursary" in applied_interventions:
        row_copy["feeding_fee_status"] = "Paid"

    if "academic_remedial" in applied_interventions:
        current_marks = float(row_copy.get("term_average_marks", 50.0))
        row_copy["term_average_marks"] = min(100.0, current_marks + 16.0)
        row_copy["marks_trend"] = max(0.0, float(row_copy.get("marks_trend", 0.0)) + 12.0)

    if "attendance_mentoring" in applied_interventions:
        current_att = float(row_copy.get("recent_attendance", 75.0))
        row_copy["recent_attendance"] = min(100.0, current_att + 14.0)
        row_copy["consecutive_absences"] = 0

    if "climate_shock_relief" in applied_interventions:
        row_copy["household_climate_impact"] = "None"

    # 3. Simulated calculation
    z_sim, _ = calculate_student_log_odds(row_copy)
    prob_sim = float(round((1.0 / (1.0 + np.exp(-z_sim))) * 100.0, 1))
    delta = float(round(prob_base - prob_sim, 1))

    if prob_sim >= 70.0:
        new_tier = "High Risk"
    elif prob_sim >= 40.0:
        new_tier = "Moderate Risk"
    else:
        new_tier = "Low Risk"

    return {
        "original_prob": prob_base,
        "simulated_prob": prob_sim,
        "delta_reduction": delta,
        "new_tier": new_tier,
    }


def get_model_feature_weights():
    """
    Returns DataFrame of model weights and Odds Ratios for analyst inspection.
    """
    features = [
        {"Feature": "Ubudehe Category 1", "Domain": "Economic", "Weight (β)": 0.85, "Odds Ratio": round(np.exp(0.85), 2), "Interpretation": "2.34x higher odds of dropout vs baseline"},
        {"Feature": "Feeding Fee Defaulted", "Domain": "Economic", "Weight (β)": 0.75, "Odds Ratio": round(np.exp(0.75), 2), "Interpretation": "2.12x higher odds due to meal exclusion"},
        {"Feature": "Climate & Weather Shock", "Domain": "Environmental", "Weight (β)": 0.65, "Odds Ratio": round(np.exp(0.65), 2), "Interpretation": "1.92x higher odds from flood or drought"},
        {"Feature": "Prior Grade Repetition", "Domain": "Academic", "Weight (β)": 0.50, "Odds Ratio": round(np.exp(0.50), 2), "Interpretation": "1.65x higher odds from accumulated learning gaps"},
        {"Feature": "Long Commute Distance (>4km)", "Domain": "Geographic", "Weight (β)": 0.40, "Odds Ratio": round(np.exp(0.40), 2), "Interpretation": "1.49x higher odds due to fatigue and transit hazards"},
        {"Feature": "Consecutive Absences (≥3 days)", "Domain": "Attendance", "Weight (β)": 0.35, "Odds Ratio": round(np.exp(0.35), 2), "Interpretation": "Compounding risk per consecutive day absent"},
        {"Feature": "Marks Below 55% Deficit", "Domain": "Academic", "Weight (β)": 0.045, "Odds Ratio": round(np.exp(0.045), 3), "Interpretation": "+4.6% odds increase per point below pass mark"},
        {"Feature": "Attendance Below 85% Deficit", "Domain": "Attendance", "Weight (β)": 0.045, "Odds Ratio": round(np.exp(0.045), 3), "Interpretation": "+4.6% odds increase per point below benchmark"},
        {"Feature": "Severe Term Mark Drop (>-8%)", "Domain": "Academic", "Weight (β)": 0.035, "Odds Ratio": round(np.exp(0.035), 3), "Interpretation": "Early velocity indicator of disengagement"},
        {"Feature": "Severe Attendance Drop (>-8%)", "Domain": "Attendance", "Weight (β)": 0.030, "Odds Ratio": round(np.exp(0.030), 3), "Interpretation": "Sudden attendance drop indicator"},
    ]
    return pd.DataFrame(features)


def run_macro_stress_test(df, shock_scenario: str):
    """
    Simulates macro-level systemic shocks on the entire cohort.
    Scenarios:
    - 'drought_wave': Simulates severe regional drought in eastern/southern districts
    - 'feeding_budget_cut': Simulates 30% increase in feeding fee arrears
    - 'universal_remedial': Simulates national catch-up program for low marks
    """
    if df is None or df.empty:
        return None, None

    stressed_df = df.copy()

    if shock_scenario == "drought_wave":
        # Impact eastern and southern province districts
        affected_districts = ["Nyagatare", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Bugesera", "Gisagara"]
        mask = stressed_df["district"].isin(affected_districts)
        stressed_df.loc[mask, "household_climate_impact"] = "Drought / Food stress"
        stressed_df.loc[mask, "recent_attendance"] = np.maximum(30.0, stressed_df.loc[mask, "recent_attendance"] - 12.0)

    elif shock_scenario == "feeding_budget_cut":
        # 40% of partial payers default
        mask = stressed_df["feeding_fee_status"] == "Partial"
        stressed_df.loc[mask, "feeding_fee_status"] = "Defaulted"

    elif shock_scenario == "universal_remedial":
        # All students below 55% get +15% marks boost
        low_mask = stressed_df["term_average_marks"] < 55.0
        stressed_df.loc[low_mask, "term_average_marks"] = np.minimum(85.0, stressed_df.loc[low_mask, "term_average_marks"] + 15.0)
        stressed_df.loc[low_mask, "marks_trend"] = 5.0

    scored_before = predict_student_risk(df)
    scored_after = predict_student_risk(stressed_df)

    before_high = (scored_before["risk_tier"] == "High Risk").sum()
    after_high = (scored_after["risk_tier"] == "High Risk").sum()
    before_mean_risk = scored_before["predicted_risk_pct"].mean()
    after_mean_risk = scored_after["predicted_risk_pct"].mean()

    metrics = {
        "before_high_risk_count": int(before_high),
        "after_high_risk_count": int(after_high),
        "before_mean_risk": round(before_mean_risk, 1),
        "after_mean_risk": round(after_mean_risk, 1),
        "risk_delta": round(after_mean_risk - before_mean_risk, 1),
    }

    return scored_after, metrics
