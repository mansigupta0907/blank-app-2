"""
data_cleaning.py
-----------------
Nassau Candy Distributor - Factory-to-Customer Shipping Route Efficiency Analysis

What this script does (in order):
1. Load the raw CSV
2. Inspect structure, nulls, and dtypes
3. Fix date formats (source dates are DD-MM-YYYY strings)
4. Detect and handle the Ship Date data-quality issue (implausible/negative lead times)
5. Standardize geographic text fields
6. Map each product to its manufacturing factory (needed to build "routes")
7. Engineer the core analysis features: Shipping Lead Time, Route, Order Month
8. Export a clean CSV ready for SQL / Power BI

Beginner-friendly: every step is a small, named function so you can run
pieces individually in a notebook if you want to inspect intermediate output.
"""

import pandas as pd

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
RAW_PATH = "data/Nassau_Candy_Distributor.csv"
CLEAN_PATH = "data/Nassau_Candy_Distributor_clean.csv"

# A reasonable business rule: shipments should not realistically take longer
# than ~30 days to leave the factory. Anything beyond that (or negative) is
# treated as a data entry error rather than a real shipment.
MAX_PLAUSIBLE_LEAD_DAYS = 30

# Product ID prefix -> Factory mapping (derived from the project's
# "Products and Factories Correlation" reference table)
PRODUCT_PREFIX_TO_FACTORY = {
    "CHO": "Lot's O' Nuts",       # Chocolate division products default factory
    "SUG": "Sugar Shack",         # Sugar division products
    # "Other" division products are split across Secret Factory / The Other
    # Factory / Wicked Choccy's depending on the specific SKU — see the
    # project's product/factory reference table and extend this mapping
    # (or better: load it as its own small lookup CSV) as needed.
}


def load_raw_data(path: str) -> pd.DataFrame:
    """Step 1: Load the raw CSV into a DataFrame."""
    df = pd.read_csv(path)
    print(f"Loaded {len(df):,} rows and {df.shape[1]} columns from {path}")
    return df


def inspect_data(df: pd.DataFrame) -> None:
    """Step 2: Quick data-quality inspection before touching anything."""
    print("\n--- dtypes ---")
    print(df.dtypes)

    print("\n--- null counts ---")
    print(df.isnull().sum())

    print("\n--- duplicate rows ---")
    print(f"{df.duplicated().sum()} exact duplicate rows found")


def fix_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Step 3: Convert Order Date and Ship Date from DD-MM-YYYY strings
    into proper datetime objects so we can do date math on them."""
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y", errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y", errors="coerce")

    # Any row where parsing failed becomes NaT (Not a Time) - report it
    bad_order_dates = df["Order Date"].isna().sum()
    bad_ship_dates = df["Ship Date"].isna().sum()
    if bad_order_dates or bad_ship_dates:
        print(f"Warning: {bad_order_dates} unparseable Order Dates, "
              f"{bad_ship_dates} unparseable Ship Dates")

    return df


def calculate_lead_time(df: pd.DataFrame) -> pd.DataFrame:
    """Step 4: Engineer Shipping Lead Time and flag/remove implausible values.

    This dataset has a known issue: some Ship Date values are years after
    the Order Date, producing lead times of 900+ days. Rather than silently
    keep or silently drop these, we:
      a) calculate the raw lead time,
      b) flag rows outside a plausible business range,
      c) drop the flagged rows into a separate DataFrame for transparency,
      d) keep only plausible rows in the main cleaned dataset.
    """
    df["Shipping_Lead_Time_Days"] = (df["Ship Date"] - df["Order Date"]).dt.days

    invalid_mask = (
        df["Shipping_Lead_Time_Days"].isna()
        | (df["Shipping_Lead_Time_Days"] < 0)
        | (df["Shipping_Lead_Time_Days"] > MAX_PLAUSIBLE_LEAD_DAYS)
    )

    invalid_rows = df[invalid_mask].copy()
    clean_rows = df[~invalid_mask].copy()

    print(f"\nLead time validation: {len(invalid_rows):,} rows flagged as "
          f"invalid/implausible out of {len(df):,} total "
          f"({len(invalid_rows) / len(df):.1%})")

    # Keep an audit trail of what was removed and why - good practice, and
    # something you can point to directly in an interview.
    if len(invalid_rows) > 0:
        invalid_rows.to_csv("data/removed_invalid_lead_times.csv", index=False)
        print("Removed rows saved to data/removed_invalid_lead_times.csv for audit")

    return clean_rows


def standardize_geography(df: pd.DataFrame) -> pd.DataFrame:
    """Step 5: Standardize text fields so grouping/joining doesn't silently
    fail because of casing or stray whitespace."""
    text_cols = ["City", "State/Province", "Country/Region", "Region", "Division"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip().str.title()

    # Ship Mode and Product Name are display-sensitive (e.g. "First Class")
    # so we only strip whitespace, not re-case them.
    df["Ship Mode"] = df["Ship Mode"].astype(str).str.strip()
    df["Product Name"] = df["Product Name"].astype(str).str.strip()

    return df


def assign_factory(df: pd.DataFrame) -> pd.DataFrame:
    """Step 6: Assign each order line to its manufacturing factory using the
    Product ID prefix, so we can build Factory -> Customer routes.

    Product IDs follow the pattern "CHO-MIL-31000", "SUG-XXX-#####", etc.
    We use the first 3 characters as the division prefix.
    """
    prefix = df["Product ID"].str[:3]
    df["Factory"] = prefix.map(PRODUCT_PREFIX_TO_FACTORY).fillna("Unmapped")

    unmapped = (df["Factory"] == "Unmapped").sum()
    if unmapped:
        print(f"\nNote: {unmapped} rows could not be mapped to a factory "
              "using the simple prefix rule - extend PRODUCT_PREFIX_TO_FACTORY "
              "with the full product/factory lookup table for full coverage.")

    return df


def engineer_route_features(df: pd.DataFrame) -> pd.DataFrame:
    """Step 7: Build the final analysis-ready features."""
    df["Route"] = df["Factory"] + " -> " + df["State/Province"]
    df["Order_Month"] = df["Order Date"].dt.to_period("M").astype(str)
    return df


def export_clean_data(df: pd.DataFrame, path: str) -> None:
    """Step 8: Write the cleaned, feature-engineered dataset to disk."""
    df.to_csv(path, index=False)
    print(f"\nSaved cleaned dataset: {len(df):,} rows -> {path}")


def main():
    df = load_raw_data(RAW_PATH)
    inspect_data(df)
    df = fix_date_columns(df)
    df = calculate_lead_time(df)
    df = standardize_geography(df)
    df = assign_factory(df)
    df = engineer_route_features(df)
    export_clean_data(df, CLEAN_PATH)


if __name__ == "__main__":
    main()
