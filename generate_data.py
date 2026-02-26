"""
generate_data.py
================
Customer Churn Analysis - Synthetic Data Generator
Author: Arianna
Project: Portfolio Project 1 - Customer Churn Analysis

PURPOSE:
    Generates a realistic synthetic dataset of 10,000+ subscription service customers.
    This script simulates real-world subscription data including demographics,
    usage patterns, billing information, and churn events.

OUTPUT:
    - customers_raw.csv       → Raw dataset (intentionally includes dirty data to clean)
    - customers_clean.csv     → Cleaned dataset ready for SQL import
    - subscriptions.csv       → Subscription plan details lookup table

WHY SYNTHETIC DATA?
    Using synthetic data lets you demonstrate data generation, cleaning, and analysis
    skills without privacy concerns. In interviews, explain that you understand how to
    work with real datasets but used synthetic data to keep the project self-contained.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
RANDOM_SEED = 42          # Ensures reproducible results (important for portfolio demos)
NUM_CUSTOMERS = 10_500    # Generate slightly over 10k so we have rows to intentionally dirty/drop
OUTPUT_DIR = "data"

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# REFERENCE TABLES  (lookup values)
# ─────────────────────────────────────────────

SUBSCRIPTION_PLANS = {
    "Basic":    {"price": 9.99,  "features": "1 screen, SD quality"},
    "Standard": {"price": 15.99, "features": "2 screens, HD quality"},
    "Premium":  {"price": 22.99, "features": "4 screens, 4K quality"},
}

REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West", "International"]

PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer"]

CANCELLATION_REASONS = [
    "Too Expensive",
    "Not Enough Content",
    "Technical Issues",
    "Switching to Competitor",
    "No Longer Needed",
    "Found Better Alternative",
]

AGE_GROUPS = {
    "18-24": (18, 24),
    "25-34": (25, 34),
    "35-44": (35, 44),
    "45-54": (45, 54),
    "55-64": (55, 64),
    "65+":   (65, 80),
}


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def random_date(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between start and end (inclusive)."""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def calculate_churn_probability(row: dict) -> float:
    """
    Determine the probability that a customer will churn based on key factors.

    INTERVIEW TALKING POINT:
        These weights were intentionally designed so that the top churn drivers are:
        1. Low monthly login frequency (engagement)
        2. High plan price (affordability)
        3. Short customer tenure (newer customers churn more)

        This mirrors real-world churn research, making your analysis findings realistic.

    Args:
        row: Dictionary containing customer attributes.

    Returns:
        Float between 0 and 1 representing churn probability.
    """
    prob = 0.10  # Base churn rate of 10%

    # Low engagement customers churn more (biggest factor)
    if row["avg_monthly_logins"] < 3:
        prob += 0.35
    elif row["avg_monthly_logins"] < 8:
        prob += 0.15

    # Higher-tier plans have slightly more churn (price sensitivity)
    if row["plan_name"] == "Premium":
        prob += 0.08
    elif row["plan_name"] == "Standard":
        prob += 0.04

    # Newer customers (< 6 months) are at higher churn risk
    if row["tenure_months"] < 6:
        prob += 0.20
    elif row["tenure_months"] < 12:
        prob += 0.08

    # Customers who've had billing issues churn more
    if row["billing_issues_count"] > 0:
        prob += 0.12

    # Younger customers (18-24) churn more
    if row["age_group"] in ("18-24", "25-34"):
        prob += 0.06

    # International customers have higher churn
    if row["region"] == "International":
        prob += 0.10

    return min(prob, 0.95)  # Cap at 95% — no one is guaranteed to churn


# ─────────────────────────────────────────────
# DATA GENERATION
# ─────────────────────────────────────────────

def generate_customers(n: int) -> pd.DataFrame:
    """
    Generate a synthetic customer dataset with realistic distributions.

    Each row represents one customer with subscription, usage, and demographic data.

    Args:
        n: Number of customer records to generate.

    Returns:
        DataFrame with n rows of customer data.
    """
    print(f"⚙️  Generating {n:,} customer records...")

    # Date range: customers joined over the past 3 years
    join_date_start = datetime(2021, 1, 1)
    join_date_end   = datetime(2024, 6, 30)

    records = []

    for i in range(1, n + 1):
        # ── Demographics ──────────────────────────────────
        age_group = random.choices(
            list(AGE_GROUPS.keys()),
            weights=[15, 30, 25, 15, 10, 5],  # Realistic age distribution for streaming service
            k=1
        )[0]
        age = random.randint(*AGE_GROUPS[age_group])
        region = random.choices(REGIONS, weights=[20, 15, 20, 15, 20, 10], k=1)[0]

        # ── Subscription ──────────────────────────────────
        plan_name = random.choices(
            list(SUBSCRIPTION_PLANS.keys()),
            weights=[40, 40, 20],  # Most customers pick Basic or Standard
            k=1
        )[0]
        plan_price = SUBSCRIPTION_PLANS[plan_name]["price"]
        payment_method = random.choice(PAYMENT_METHODS)

        # ── Dates ─────────────────────────────────────────
        join_date = random_date(join_date_start, join_date_end)
        tenure_months = (datetime(2024, 9, 30) - join_date).days // 30

        # ── Usage Patterns ────────────────────────────────
        # Login frequency correlates with engagement (churners login less)
        avg_monthly_logins = max(0, round(np.random.normal(loc=12, scale=7), 1))
        avg_session_minutes = max(0, round(np.random.normal(loc=45, scale=20), 1))
        support_tickets = np.random.poisson(lam=0.5)       # Most customers contact support rarely
        billing_issues_count = np.random.poisson(lam=0.3)  # Rare billing issues

        row = {
            "customer_id":          i,
            "age":                  age,
            "age_group":            age_group,
            "region":               region,
            "plan_name":            plan_name,
            "plan_price":           plan_price,
            "payment_method":       payment_method,
            "join_date":            join_date,
            "tenure_months":        tenure_months,
            "avg_monthly_logins":   avg_monthly_logins,
            "avg_session_minutes":  avg_session_minutes,
            "support_tickets":      support_tickets,
            "billing_issues_count": billing_issues_count,
        }

        # ── Churn Decision ────────────────────────────────
        churn_prob = calculate_churn_probability(row)
        churned = random.random() < churn_prob

        if churned:
            # Churned customers have a cancellation date after joining
            cancel_date = random_date(
                join_date + timedelta(days=30),
                min(join_date + timedelta(days=tenure_months * 30), datetime(2024, 9, 30))
            )
            row["is_churned"]          = 1
            row["cancellation_date"]   = cancel_date
            row["cancellation_reason"] = random.choice(CANCELLATION_REASONS)
            row["customer_lifetime_days"] = (cancel_date - join_date).days
        else:
            row["is_churned"]             = 0
            row["cancellation_date"]      = None
            row["cancellation_reason"]    = None
            row["customer_lifetime_days"] = (datetime(2024, 9, 30) - join_date).days

        records.append(row)

    df = pd.DataFrame(records)
    print(f"✅ Generated {len(df):,} customer records. Churn rate: {df['is_churned'].mean():.1%}")
    return df


def add_dirty_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Intentionally introduce data quality issues to simulate real-world messy data.

    INTERVIEW TALKING POINT:
        Real datasets are never clean. This function simulates common issues:
        - Duplicate rows (data pipeline re-runs)
        - Missing values (NULL plan_price, NULL region)
        - Date format inconsistencies (mix of YYYY-MM-DD and MM/DD/YYYY)
        - Inconsistent capitalization (e.g., 'basic' vs 'Basic')

        Showing you can IDENTIFY and FIX these issues is a key data analyst skill.

    Args:
        df: Clean DataFrame to dirty.

    Returns:
        DataFrame with intentional data quality issues introduced.
    """
    print("🪣  Introducing data quality issues for cleaning practice...")
    dirty_df = df.copy()

    rng = np.random.default_rng(RANDOM_SEED)

    # 1) Add ~200 exact duplicate rows
    dup_indices = rng.choice(df.index, size=200, replace=False)
    duplicates  = df.loc[dup_indices].copy()
    dirty_df    = pd.concat([dirty_df, duplicates], ignore_index=True)

    # 2) Randomly null out ~5% of plan_price values
    null_price_idx = rng.choice(dirty_df.index, size=int(len(dirty_df) * 0.05), replace=False)
    dirty_df.loc[null_price_idx, "plan_price"] = None

    # 3) Randomly null out ~3% of region values
    null_region_idx = rng.choice(dirty_df.index, size=int(len(dirty_df) * 0.03), replace=False)
    dirty_df.loc[null_region_idx, "region"] = None

    # 4) Introduce inconsistent plan_name capitalization on ~10% of rows
    inconsistent_idx = rng.choice(dirty_df.index, size=int(len(dirty_df) * 0.10), replace=False)
    dirty_df.loc[inconsistent_idx, "plan_name"] = (
        dirty_df.loc[inconsistent_idx, "plan_name"].str.lower()
    )

    # 5) Mix date formats (some rows use MM/DD/YYYY instead of YYYY-MM-DD)
    # We'll store join_date as a string for these rows to simulate mixed formats
    date_format_idx = rng.choice(dirty_df.index, size=int(len(dirty_df) * 0.08), replace=False)
    dirty_df.loc[date_format_idx, "join_date"] = (
        dirty_df.loc[date_format_idx, "join_date"]
        .apply(lambda d: d.strftime("%m/%d/%Y") if pd.notnull(d) else d)
    )

    print(f"✅ Dataset now has {len(dirty_df):,} rows (including duplicates & nulls)")
    return dirty_df


def clean_data(dirty_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply data cleaning steps to the raw dataset.

    Steps:
        1. Remove duplicate rows.
        2. Standardize plan_name capitalization.
        3. Standardize date formats to YYYY-MM-DD.
        4. Fill missing plan_price using plan_name as the source of truth.
        5. Fill missing region with 'Unknown'.
        6. Validate that cancellation_date >= join_date (data integrity check).

    INTERVIEW TALKING POINT:
        Always document EVERY cleaning decision. Interviewers want to know:
        - WHY you made each choice (e.g., fill vs drop for nulls)
        - How you validated the fix worked

    Args:
        dirty_df: Raw DataFrame with data quality issues.

    Returns:
        Cleaned DataFrame ready for SQL import.
    """
    print("🧹 Cleaning data...")
    df = dirty_df.copy()
    original_rows = len(df)

    # ── Step 1: Remove Duplicates ──────────────────────────────────────────
    # Drop exact duplicate rows. Keep first occurrence.
    df = df.drop_duplicates()
    print(f"   [1/6] Removed {original_rows - len(df):,} duplicate rows → {len(df):,} remaining")

    # ── Step 2: Standardize plan_name capitalization ───────────────────────
    # Convert all plan names to Title Case (e.g., 'basic' → 'Basic')
    df["plan_name"] = df["plan_name"].str.title()

    # ── Step 3: Standardize join_date format ───────────────────────────────
    # pd.to_datetime handles both YYYY-MM-DD and MM/DD/YYYY automatically
    df["join_date"] = pd.to_datetime(df["join_date"], format="mixed")

    # Standardize cancellation_date the same way
    df["cancellation_date"] = pd.to_datetime(df["cancellation_date"], errors="coerce")
    print("   [3/6] Standardized all date columns to datetime format")

    # ── Step 4: Fill missing plan_price from plan lookup ───────────────────
    price_lookup = {k: v["price"] for k, v in SUBSCRIPTION_PLANS.items()}
    missing_price_count = df["plan_price"].isnull().sum()
    df["plan_price"] = df.apply(
        lambda row: price_lookup.get(row["plan_name"], row["plan_price"])
        if pd.isnull(row["plan_price"]) else row["plan_price"],
        axis=1
    )
    print(f"   [4/6] Filled {missing_price_count:,} missing plan_price values using plan lookup")

    # ── Step 5: Fill missing region ────────────────────────────────────────
    # Use 'Unknown' rather than dropping so we don't lose other data in the row
    missing_region_count = df["region"].isnull().sum()
    df["region"] = df["region"].fillna("Unknown")
    print(f"   [5/6] Filled {missing_region_count:,} missing region values with 'Unknown'")

    # ── Step 6: Validate date integrity ────────────────────────────────────
    # A cancellation_date that is BEFORE the join_date is logically impossible
    invalid_dates = df[
        df["cancellation_date"].notnull() &
        (df["cancellation_date"] < df["join_date"])
    ]
    if len(invalid_dates) > 0:
        print(f"   [6/6] ⚠️  Found {len(invalid_dates):,} rows where cancellation_date < join_date — setting cancellation_date to NULL")
        df.loc[invalid_dates.index, "cancellation_date"] = None
        df.loc[invalid_dates.index, "is_churned"] = 0
        df.loc[invalid_dates.index, "cancellation_reason"] = None
    else:
        print("   [6/6] ✅ Date integrity check passed — all cancellation_dates are after join_dates")

    print(f"\n✅ Cleaning complete! Final dataset: {len(df):,} rows")
    return df


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    """
    Orchestrate the full data generation and cleaning pipeline.

    Run this file first before any SQL or analysis work.
    """
    # Step 1: Generate clean source data
    df_generated = generate_customers(NUM_CUSTOMERS)

    # Step 2: Save raw version (with intentional dirty data for the cleaning demo)
    df_dirty = add_dirty_data(df_generated)
    raw_path = os.path.join(OUTPUT_DIR, "customers_raw.csv")
    df_dirty.to_csv(raw_path, index=False)
    print(f"\n💾 Raw (dirty) dataset saved → {raw_path}")

    # Step 3: Clean the data
    df_clean = clean_data(df_dirty)
    clean_path = os.path.join(OUTPUT_DIR, "customers_clean.csv")
    df_clean.to_csv(clean_path, index=False)
    print(f"💾 Clean dataset saved → {clean_path}")

    # Step 4: Save subscription plans lookup table
    plans_df = pd.DataFrame([
        {"plan_name": k, "price": v["price"], "features": v["features"]}
        for k, v in SUBSCRIPTION_PLANS.items()
    ])
    plans_path = os.path.join(OUTPUT_DIR, "subscriptions.csv")
    plans_df.to_csv(plans_path, index=False)
    print(f"💾 Subscription plans saved → {plans_path}")

    # Step 5: Print data summary
    print("\n" + "="*50)
    print("DATASET SUMMARY")
    print("="*50)
    print(f"Total Customers:  {len(df_clean):,}")
    print(f"Churned:          {df_clean['is_churned'].sum():,} ({df_clean['is_churned'].mean():.1%})")
    print(f"Active:           {(~df_clean['is_churned'].astype(bool)).sum():,}")
    print(f"\nPlan Distribution:\n{df_clean['plan_name'].value_counts().to_string()}")
    print(f"\nRegion Distribution:\n{df_clean['region'].value_counts().to_string()}")


if __name__ == "__main__":
    main()
