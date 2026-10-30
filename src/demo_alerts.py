import pandas as pd
from pathlib import Path
from src.prediction_model import predict_student_risk

MOCK_FILE = Path(__file__).parent.parent / "data" / "demo" / "mock_students.csv"


def load_mock_students():
    """
    Loads simulated student records from CSV.
    Returns DataFrame or None if file cannot be found or read.
    """
    if not MOCK_FILE.exists():
        return None
    try:
        df = pd.read_csv(MOCK_FILE)
        df.columns = [c.strip() for c in df.columns]
        for col in ["school", "district", "student_name", "feeding_fee_status", "household_climate_impact"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df
    except Exception:
        return None


def apply_rules(df):
    """
    Evaluates student records using both transparent rule thresholds
    and multi-factor statistical risk prediction.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Apply multi-factor predictive scoring engine
    return predict_student_risk(df)
