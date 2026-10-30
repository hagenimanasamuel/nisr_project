import numpy as np
import pandas as pd

from src.prediction_model import simulate_intervention

ROSTER_RENAME = {
    "student_id": "ID",
    "student_name": "Student",
    "school": "School",
    "district": "District",
    "grade_level": "Grade",
    "predicted_risk_pct": "Predicted risk (%)",
    "risk_tier": "Risk tier",
    "primary_driver": "Main risk factor",
    "term_average_marks": "Marks (%)",
    "recent_attendance": "Attendance (%)",
    "ubudehe_category": "Ubudehe",
    "feeding_fee_status": "Feeding fee",
    "household_climate_impact": "Climate shock",
}

COMPONENT_LABELS = {
    "c_poverty": "Poverty rate (30%)",
    "c_repetition": "Primary repetition (25%)",
    "c_hazard": "Climate hazard (25%)",
    "c_access": "School access gap (20%)",
}


def roster_view(df, include_ubudehe=False):
    cols = [
        "student_id", "student_name", "school", "district", "grade_level",
        "predicted_risk_pct", "risk_tier", "primary_driver",
        "term_average_marks", "recent_attendance",
    ]
    if include_ubudehe:
        cols.append("ubudehe_category")
    cols += ["feeding_fee_status", "household_climate_impact"]
    return df[cols].rename(columns=ROSTER_RENAME)


def add_vulnerability_components(df):
    """
    Splits the composite vulnerability index into its weighted parts and assigns
    priority tiers: top quartile = Priority 1, upper half = Priority 2, rest = Priority 3.
    Returns (dataframe, top_quartile_threshold).
    """
    out = df.copy()
    out["c_poverty"] = 0.30 * out["poverty_rate"]
    out["c_repetition"] = 0.25 * out["primary_repetition"]
    out["c_hazard"] = 0.25 * out["minema_hazard_index"] * 20.0
    out["c_access"] = 0.20 * (100.0 - out["primary_nar"])

    idx = out["composite_vulnerability_index"]
    q75 = float(idx.quantile(0.75))
    q50 = float(idx.quantile(0.50))
    out["priority_tier"] = np.where(idx >= q75, "Priority 1", np.where(idx >= q50, "Priority 2", "Priority 3"))
    return out, q75


def simulate_district_package(students, districts, interventions):
    """
    Applies an intervention package to every simulated student in the target districts
    and compares risk before and after. Returns None when nothing can be simulated.
    """
    if students is None or students.empty or not interventions:
        return None
    scope = students[students["district"].isin(districts)]
    if scope.empty:
        return None

    before, after = [], []
    for _, row in scope.iterrows():
        res = simulate_intervention(row, interventions)
        before.append(res["original_prob"])
        after.append(res["simulated_prob"])
    b, a = np.array(before), np.array(after)

    return {
        "n": int(len(scope)),
        "districts": sorted(scope["district"].unique().tolist()),
        "mean_before": round(float(b.mean()), 1),
        "mean_after": round(float(a.mean()), 1),
        "high_before": int((b >= 70.0).sum()),
        "high_after": int((a >= 70.0).sum()),
    }


def fit_line(x, y):
    """Least-squares line and Pearson r. Returns (x_grid, y_fit, r) or None."""
    mask = x.notna() & y.notna()
    xs, ys = x[mask].astype(float), y[mask].astype(float)
    if len(xs) < 3 or xs.nunique() < 2:
        return None
    slope, intercept = np.polyfit(xs, ys, 1)
    r = float(np.corrcoef(xs, ys)[0, 1])
    grid = np.linspace(xs.min(), xs.max(), 20)
    return grid, slope * grid + intercept, r