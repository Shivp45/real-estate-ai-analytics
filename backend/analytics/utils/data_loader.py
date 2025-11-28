from pathlib import Path
import pandas as pd

"""
This updated loader supports your dataset automatically.

It maps your column names to the required internal names:

Required → Your Dataset
------------------------------------------
Area     → final location
Year     → year
Price    → flat - weighted average rate
Demand   → total sold - igr
Size     → total carpet area supplied (sqft)
"""

# Mapping dictionary (case-insensitive matching)
COLUMN_MAPPING = {
    "year": "Year",
    "final location": "Area",
    "flat - weighted average rate": "Price",
    "total sold - igr": "Demand",
    "total carpet area supplied (sqft)": "Size",
}

REQUIRED_COLUMNS = ["Year", "Area", "Price", "Demand", "Size"]


def normalize_column_name(col: str) -> str:
    """Normalize: remove spaces, lowercase, and collapse multiple spaces."""
    return col.strip().lower().replace("\n", " ").replace("  ", " ")


def load_dataset_from_path(path: str) -> pd.DataFrame:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    df = pd.read_excel(file_path)

    # Clean column names
    original_columns = df.columns.tolist()
    normalized_to_original = {normalize_column_name(c): c for c in original_columns}

    new_columns = {}

    for norm, original in normalized_to_original.items():
        if norm in COLUMN_MAPPING:
            # Use our required system name
            new_columns[original] = COLUMN_MAPPING[norm]
        else:
            # Keep original for extra unused columns
            new_columns[original] = original

    # Rename recognized columns
    df.rename(columns=new_columns, inplace=True)

    # Check required columns exist after mapping
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required mapped columns: {', '.join(missing)}\n\n"
            f"Detected columns: {', '.join(df.columns)}"
        )

    # Cleanup and convert types
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Demand"] = pd.to_numeric(df["Demand"], errors="coerce")
    df["Size"] = pd.to_numeric(df["Size"], errors="coerce")

    df = df.dropna(subset=["Year", "Area"])
    df["Area"] = df["Area"].astype(str).str.strip()

    return df
