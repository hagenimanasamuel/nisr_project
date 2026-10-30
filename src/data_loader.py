import pandas as pd
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "nisr" / "district_indicators.csv"
MULTI_SOURCE_FILE = Path(__file__).parent.parent / "data" / "nisr" / "district_multi_source.csv"

COLUMN_LABELS = {
    "district": "District",
    "primary_nar": "Primary NAR (%)",
    "secondary_nar": "Secondary NAR (%)",
    "primary_repetition": "Primary repetition rate (%)",
    "poverty_rate": "Poverty rate (%)",
    "extreme_poverty": "Extreme poverty rate (%)",
    "electricity_access": "Electricity access (%)",
    "minema_hazard_index": "MINEMA climate hazard index (1-5)",
    "dominant_climate_hazard": "Dominant climate hazard",
    "feeding_program_coverage": "School feeding coverage (%)",
    "composite_vulnerability_index": "Composite vulnerability index",
}

# Centroid coordinates for the 30 districts of Rwanda
DISTRICT_COORDINATES = {
    "Bugesera": (-2.2167, 30.1667),
    "Burera": (-1.4500, 29.8667),
    "Gakenke": (-1.7000, 29.7833),
    "Gasabo": (-1.8890, 30.1336),
    "Gatsibo": (-1.6000, 30.4500),
    "Gicumbi": (-1.6000, 30.1167),
    "Gisagara": (-2.6175, 29.8456),
    "Huye": (-2.5967, 29.7394),
    "Kamonyi": (-1.9833, 29.9167),
    "Karongi": (-2.1583, 29.3500),
    "Kayonza": (-1.8833, 30.6500),
    "Kicukiro": (-1.9996, 30.1261),
    "Kirehe": (-2.2667, 30.6500),
    "Muhanga": (-2.0833, 29.7500),
    "Musanze": (-1.5000, 29.6333),
    "Ngoma": (-2.1667, 30.5000),
    "Ngororero": (-1.8667, 29.6167),
    "Nyabihu": (-1.6500, 29.5000),
    "Nyagatare": (-1.3000, 30.3333),
    "Nyamagabe": (-2.4839, 29.4792),
    "Nyamasheke": (-2.3667, 29.1333),
    "Nyanza": (-2.3508, 29.7503),
    "Nyarugenge": (-1.9536, 30.0606),
    "Nyaruguru": (-2.7119, 29.5447),
    "Rubavu": (-1.6833, 29.2667),
    "Ruhango": (-2.2222, 29.7781),
    "Rulindo": (-1.7333, 30.0167),
    "Rusizi": (-2.5833, 28.9167),
    "Rutsiro": (-1.9333, 29.3167),
    "Rwamagana": (-1.9500, 30.4333),
}


def load_district_indicators():
    """
    Loads district indicators from the NISR EICV7 dataset.
    Returns sorted DataFrame with coordinates or None if file cannot be read.
    """
    if not DATA_FILE.exists():
        return None
    try:
        df = pd.read_csv(DATA_FILE)
        df = df.sort_values("district").reset_index(drop=True)
        df["latitude"] = df["district"].map(lambda d: DISTRICT_COORDINATES.get(d, (None, None))[0])
        df["longitude"] = df["district"].map(lambda d: DISTRICT_COORDINATES.get(d, (None, None))[1])
        return df
    except Exception:
        return None


def load_multi_source_district_data():
    """
    Merges official NISR EICV7 indicators with MINEMA disaster and poverty profiles.
    Calculates a calibrated composite vulnerability index for planners and analysts.
    """
    base_df = load_district_indicators()
    if base_df is None:
        return None

    if not MULTI_SOURCE_FILE.exists():
        return base_df

    try:
        multi_df = pd.read_csv(MULTI_SOURCE_FILE)
        merged = pd.merge(base_df, multi_df, on="district", how="left")

        # Composite Vulnerability Index formula (0 to 100)
        # Weights: 30% Poverty, 25% Repetition rate, 25% MINEMA Hazard, 20% Net Attendance Deficit
        hazard_norm = merged["minema_hazard_index"] * 20.0
        nar_deficit = 100.0 - merged["primary_nar"]
        
        merged["composite_vulnerability_index"] = (
            (0.30 * merged["poverty_rate"]) +
            (0.25 * merged["primary_repetition"]) +
            (0.25 * hazard_norm) +
            (0.20 * nar_deficit)
        ).round(1)

        return merged
    except Exception:
        return base_df


def get_label(column_name):
    """Returns human-readable column label."""
    return COLUMN_LABELS.get(column_name, column_name)
