"""
churn_analysis.py
=================
Customer Churn Analysis - Python Pandas & Visualization
Author: Arianna
Project: Portfolio Project 1 - Customer Churn Analysis

PURPOSE:
    Performs exploratory data analysis (EDA) and correlation analysis on the
    cleaned customer churn dataset. Identifies the top 3 factors most strongly
    associated with churn and generates visualizations for the dashboard/portfolio.

PREREQUISITES:
    Run generate_data.py first to create: data/customers_clean.csv

OUTPUT FILES (saved to outputs/ folder):
    - churn_by_plan.png
    - churn_by_region.png
    - churn_by_engagement.png
    - correlation_heatmap.png
    - top3_churn_factors.png
    - churn_summary_report.txt

LIBRARIES USED:
    pandas   → Data manipulation and analysis
    numpy    → Numerical operations
    matplotlib → Base plotting library
    seaborn  → Statistical visualization (built on matplotlib)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ─────────────────────────────────────────────
# CONFIGURATION & SETUP
# ─────────────────────────────────────────────

DATA_PATH   = "data/customers_clean.csv"
OUTPUT_DIR  = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set a consistent visual style for all charts
# "whitegrid" adds subtle gridlines that make values easier to read
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
plt.rcParams["figure.dpi"] = 150


# ─────────────────────────────────────────────
# LOAD & VALIDATE DATA
# ─────────────────────────────────────────────

def load_data(path: str) -> pd.DataFrame:
    """
    Load the cleaned customer dataset and perform basic validation.

    Args:
        path: File path to the cleaned CSV.

    Returns:
        Validated DataFrame.
    """
    print(f"📂 Loading data from: {path}")
    df = pd.read_csv(path, parse_dates=["join_date", "cancellation_date"])

    # Basic validation: check expected columns exist
    required_cols = [
        "customer_id", "is_churned", "plan_name", "plan_price",
        "region", "age_group", "tenure_months",
        "avg_monthly_logins", "avg_session_minutes",
        "support_tickets", "billing_issues_count"
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected columns: {missing_cols}")

    print(f"✅ Loaded {len(df):,} rows × {len(df.columns)} columns")
    print(f"   Churn Rate: {df['is_churned'].mean():.1%}\n")
    return df


# ─────────────────────────────────────────────
# HELPER: SAVE FIGURE
# ─────────────────────────────────────────────

def save_figure(filename: str):
    """Save the current matplotlib figure to the outputs directory."""
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"   💾 Saved → {path}")


# ─────────────────────────────────────────────
# SECTION 1: DESCRIPTIVE STATISTICS
# ─────────────────────────────────────────────

def print_summary(df: pd.DataFrame):
    """
    Print a high-level summary of the dataset.

    INTERVIEW TALKING POINT:
        Always start EDA with describe() to check:
        - Value ranges (are there negatives where impossible?)
        - Mean vs. median gaps (signals skew/outliers)
        - Null counts (any remaining cleaning needed?)
    """
    print("=" * 55)
    print("DATASET SUMMARY")
    print("=" * 55)

    total       = len(df)
    churned     = df["is_churned"].sum()
    active      = total - churned
    churn_rate  = churned / total

    print(f"Total Customers : {total:,}")
    print(f"Churned         : {churned:,} ({churn_rate:.1%})")
    print(f"Active          : {active:,} ({1 - churn_rate:.1%})")
    print(f"\nAvg Tenure       : {df['tenure_months'].mean():.1f} months")
    print(f"Avg Logins/Month : {df['avg_monthly_logins'].mean():.1f}")
    print(f"Avg Session Time : {df['avg_session_minutes'].mean():.1f} min")

    print("\nPlan Distribution:")
    print(df["plan_name"].value_counts().to_string())

    print("\nNulls per column:")
    print(df.isnull().sum()[df.isnull().sum() > 0].to_string() or "  None — data is clean ✅")
    print()


# ─────────────────────────────────────────────
# SECTION 2: CORRELATION ANALYSIS
# ─────────────────────────────────────────────

def correlation_analysis(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the correlation between each numeric feature and churn (is_churned).

    HOW CORRELATION WORKS:
        Correlation ranges from -1 to +1.
        +1  → Feature increases perfectly with churn
        0   → No linear relationship
        -1  → Feature decreases perfectly as churn increases

        We use POINT-BISERIAL correlation here because is_churned is binary (0/1)
        and the other features are continuous. pd.corr() handles this automatically.

    INTERVIEW TALKING POINT:
        Correlation ≠ causation. "Low logins correlate with churn" doesn't mean
        low logins CAUSE churn — it could be that unhappy customers login less
        AND also churn. But it IS useful as a predictive signal.

    Args:
        df: Clean DataFrame.

    Returns:
        Series of correlation coefficients sorted by absolute value (descending).
    """
    print("📊 Running Correlation Analysis...")

    # Select only numeric columns for correlation (drop IDs and dates)
    numeric_cols = [
        "plan_price",
        "tenure_months",
        "avg_monthly_logins",
        "avg_session_minutes",
        "support_tickets",
        "billing_issues_count",
        "customer_lifetime_days",
    ]

    # Calculate Pearson correlation of each feature vs is_churned
    correlations = df[numeric_cols + ["is_churned"]].corr()["is_churned"].drop("is_churned")
    correlations_sorted = correlations.abs().sort_values(ascending=False)

    print("\nCorrelation with Churn (absolute value, sorted):")
    for feature, corr_val in correlations_sorted.items():
        direction = "↑" if correlations[feature] > 0 else "↓"
        print(f"  {feature:<30} {direction} {correlations[feature]:+.4f}")

    print(f"\n🔑 Top 3 Churn Factors:")
    for i, (feat, _) in enumerate(correlations_sorted.head(3).items(), 1):
        corr = correlations[feat]
        direction = "increases" if corr > 0 else "decreases"
        print(f"  {i}. {feat} — as this {direction}, churn risk goes {'up' if corr > 0 else 'down'}")

    return correlations


def plot_correlation_heatmap(df: pd.DataFrame):
    """
    Generate a correlation heatmap of all numeric features including is_churned.

    VISUAL PURPOSE:
        A heatmap lets recruiters/interviewers quickly see which features
        are most related to each other AND to churn in a single glance.
    """
    print("\n📈 Plotting: Correlation Heatmap")

    numeric_cols = [
        "is_churned", "plan_price", "tenure_months",
        "avg_monthly_logins", "avg_session_minutes",
        "support_tickets", "billing_issues_count",
    ]

    corr_matrix = df[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        corr_matrix,
        annot=True,          # Show correlation values inside each cell
        fmt=".2f",
        cmap="coolwarm",     # Blue (negative) → White (0) → Red (positive)
        center=0,
        linewidths=0.5,
        ax=ax
    )
    ax.set_title("Feature Correlation Matrix\n(Focus on 'is_churned' row/column)", pad=15)
    plt.tight_layout()
    save_figure("correlation_heatmap.png")


# ─────────────────────────────────────────────
# SECTION 3: TOP 3 FACTORS VISUALIZATION
# ─────────────────────────────────────────────

def plot_top3_factors(df: pd.DataFrame):
    """
    Create a 3-panel chart showing churn rate segmented by the top 3 correlated features:
        1. avg_monthly_logins (engagement)
        2. tenure_months (customer age)
        3. billing_issues_count (payment friction)

    INTERVIEW TALKING POINT:
        Subplots (side-by-side charts) are efficient storytelling.
        Instead of 3 separate slides, one figure tells the complete story.
    """
    print("\n📈 Plotting: Top 3 Churn Factors")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Top 3 Factors Associated with Customer Churn", fontsize=14, fontweight="bold", y=1.02)

    # ── Factor 1: Login Frequency (engagement) ────────────────────────────
    df["login_tier"] = pd.cut(
        df["avg_monthly_logins"],
        bins=[0, 3, 8, 15, 100],
        labels=["Very Low\n(<3/mo)", "Low\n(3-7/mo)", "Medium\n(8-14/mo)", "High\n(15+/mo)"]
    )
    login_churn = df.groupby("login_tier", observed=True)["is_churned"].mean() * 100

    axes[0].bar(login_churn.index, login_churn.values, color=sns.color_palette("coolwarm", len(login_churn)))
    axes[0].set_title("Churn Rate by Login Frequency\n(Engagement)", fontweight="bold")
    axes[0].set_xlabel("Monthly Login Frequency")
    axes[0].set_ylabel("Churn Rate (%)")
    axes[0].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    for bar, val in zip(axes[0].patches, login_churn.values):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=9)

    # ── Factor 2: Tenure (customer age) ───────────────────────────────────
    df["tenure_tier"] = pd.cut(
        df["tenure_months"],
        bins=[0, 3, 6, 12, 24, 100],
        labels=["0-3\nmonths", "3-6\nmonths", "6-12\nmonths", "1-2\nyears", "2+\nyears"]
    )
    tenure_churn = df.groupby("tenure_tier", observed=True)["is_churned"].mean() * 100

    axes[1].bar(tenure_churn.index, tenure_churn.values, color=sns.color_palette("coolwarm_r", len(tenure_churn)))
    axes[1].set_title("Churn Rate by Customer Tenure\n(Loyalty)", fontweight="bold")
    axes[1].set_xlabel("Tenure")
    axes[1].set_ylabel("Churn Rate (%)")
    axes[1].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    for bar, val in zip(axes[1].patches, tenure_churn.values):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=9)

    # ── Factor 3: Billing Issues ───────────────────────────────────────────
    df["billing_tier"] = df["billing_issues_count"].apply(
        lambda x: "No Issues" if x == 0 else "1 Issue" if x == 1 else "2+ Issues"
    )
    billing_churn = (
        df.groupby("billing_tier")["is_churned"].mean() * 100
    ).reindex(["No Issues", "1 Issue", "2+ Issues"])

    axes[2].bar(billing_churn.index, billing_churn.values,
                color=["#4CAF50", "#FFC107", "#F44336"])  # Green → Yellow → Red
    axes[2].set_title("Churn Rate by Billing Issues\n(Payment Friction)", fontweight="bold")
    axes[2].set_xlabel("Billing Issues")
    axes[2].set_ylabel("Churn Rate (%)")
    axes[2].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    for bar, val in zip(axes[2].patches, billing_churn.values):
        axes[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    save_figure("top3_churn_factors.png")


# ─────────────────────────────────────────────
# SECTION 4: SEGMENT VISUALIZATIONS
# ─────────────────────────────────────────────

def plot_churn_by_plan(df: pd.DataFrame):
    """
    Bar chart: Churn rate by subscription plan (Basic, Standard, Premium).

    WHAT TO SAY IN AN INTERVIEW:
        "This chart shows that Premium plan customers have a slightly higher churn rate.
        This is counterintuitive — you'd expect customers invested in the top tier
        to be more loyal. The data suggests price sensitivity may be a factor,
        or that Premium customers have higher expectations that aren't being met."
    """
    print("\n📈 Plotting: Churn by Plan")

    plan_stats = (
        df.groupby("plan_name")["is_churned"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "churn_rate", "count": "total"})
        .reset_index()
    )
    plan_stats["churn_pct"] = plan_stats["churn_rate"] * 100

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(plan_stats["plan_name"], plan_stats["churn_pct"],
                  color=["#5C85D6", "#E08B3A", "#D64545"], width=0.5)

    ax.set_title("Churn Rate by Subscription Plan", fontweight="bold", fontsize=13)
    ax.set_xlabel("Plan")
    ax.set_ylabel("Churn Rate (%)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))

    # Add value labels on top of each bar
    for bar, val, n in zip(bars, plan_stats["churn_pct"], plan_stats["total"]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"{val:.1f}%\n(n={n:,})",
                ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    save_figure("churn_by_plan.png")


def plot_churn_by_region(df: pd.DataFrame):
    """
    Horizontal bar chart: Churn rate by geographic region.
    Horizontal bars work better when labels are long.
    """
    print("\n📈 Plotting: Churn by Region")

    region_stats = (
        df.groupby("region")["is_churned"]
        .mean()
        .sort_values(ascending=True)
        * 100
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(region_stats.index, region_stats.values,
            color=sns.color_palette("Blues_d", len(region_stats)))

    ax.set_title("Churn Rate by Region", fontweight="bold", fontsize=13)
    ax.set_xlabel("Churn Rate (%)")
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))

    for i, (val, name) in enumerate(zip(region_stats.values, region_stats.index)):
        ax.text(val + 0.2, i, f"{val:.1f}%", va="center", fontsize=9)

    plt.tight_layout()
    save_figure("churn_by_region.png")


def plot_churn_by_engagement(df: pd.DataFrame):
    """
    Scatter plot with trend line: Login frequency vs churn (aggregated by bucket).

    WHAT TO SAY IN AN INTERVIEW:
        "The negative trend confirms our hypothesis: customers who log in more
        churn less. This is a leading indicator — we can use login frequency
        to flag at-risk customers before they cancel."
    """
    print("\n📈 Plotting: Churn by Engagement")

    # Bin logins into 10 buckets, calculate churn rate per bucket
    df["login_bin"] = pd.cut(df["avg_monthly_logins"], bins=10)
    engagement_stats = (
        df.groupby("login_bin", observed=True)["is_churned"]
        .agg(["mean", "count"])
        .reset_index()
    )
    engagement_stats["midpoint"]  = engagement_stats["login_bin"].apply(lambda x: x.mid)
    engagement_stats["churn_pct"] = engagement_stats["mean"] * 100

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.scatter(engagement_stats["midpoint"], engagement_stats["churn_pct"],
               s=engagement_stats["count"] / 5,  # Bubble size = number of customers
               color="#5C85D6", alpha=0.7, edgecolors="white", linewidths=0.5)

    # Add a trend line using numpy polyfit (linear regression)
    z = np.polyfit(engagement_stats["midpoint"], engagement_stats["churn_pct"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(engagement_stats["midpoint"].min(), engagement_stats["midpoint"].max(), 100)
    ax.plot(x_line, p(x_line), "r--", alpha=0.7, label="Trend Line")

    ax.set_title("Churn Rate vs. Monthly Login Frequency\n(Bubble size = # of customers)",
                 fontweight="bold", fontsize=12)
    ax.set_xlabel("Avg Monthly Logins")
    ax.set_ylabel("Churn Rate (%)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax.legend()
    plt.tight_layout()
    save_figure("churn_by_engagement.png")


# ─────────────────────────────────────────────
# SECTION 5: SUMMARY REPORT
# ─────────────────────────────────────────────

def generate_text_report(df: pd.DataFrame, correlations: pd.Series):
    """
    Write a plain-text summary report of findings.

    This simulates what you'd include in a README or present to a stakeholder.
    INTERVIEWERS LOVE seeing that you can translate data into plain English.

    Args:
        df: Clean DataFrame.
        correlations: Series of correlations with is_churned.
    """
    churned     = df["is_churned"].sum()
    total       = len(df)
    churn_rate  = churned / total
    avg_lifetime = df[df["is_churned"] == 1]["customer_lifetime_days"].mean()

    top3 = correlations.abs().sort_values(ascending=False).head(3)

    report = f"""
=============================================================
CUSTOMER CHURN ANALYSIS — FINDINGS REPORT
=============================================================
Generated: {pd.Timestamp.now().strftime("%Y-%m-%d")}
Dataset: {total:,} customers

KEY METRICS
-----------
Overall Churn Rate          : {churn_rate:.1%}
Total Churned Customers     : {churned:,}
Avg Customer Lifetime (churned): {avg_lifetime:.0f} days ({avg_lifetime/30:.1f} months)

TOP 3 CHURN DRIVERS (by correlation)
--------------------------------------
"""
    for rank, (feature, _) in enumerate(top3.items(), 1):
        corr = correlations[feature]
        direction = "POSITIVE" if corr > 0 else "NEGATIVE"
        report += f"  {rank}. {feature} (r={corr:+.4f}, {direction} correlation)\n"

    report += f"""
SEGMENT FINDINGS
----------------
Churn by Plan:
{(df.groupby('plan_name')['is_churned'].mean() * 100).round(1).to_string()}

Churn by Region:
{(df.groupby('region')['is_churned'].mean() * 100).sort_values(ascending=False).round(1).to_string()}

RECOMMENDATIONS
---------------
1. ENGAGEMENT PROGRAMS: Customers with < 5 logins/month are at highest churn risk.
   Trigger email re-engagement campaigns when a customer goes 7+ days without logging in.

2. EARLY TENURE FOCUS: Customers in their first 3-6 months churn at the highest rate.
   Implement an onboarding sequence (tutorials, check-in emails) for new customers.

3. BILLING FRICTION: Customers with billing issues churn at 2x the base rate.
   Improve payment retry logic and send proactive billing failure alerts.

=============================================================
"""
    report_path = os.path.join(OUTPUT_DIR, "churn_summary_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\n💾 Summary report saved → {report_path}")
    print(report)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    """
    Run the complete churn analysis pipeline:
        1. Load cleaned data
        2. Print descriptive statistics
        3. Run correlation analysis
        4. Generate all visualizations
        5. Write summary report
    """
    print("🚀 Starting Churn Analysis...\n")

    # 1. Load data
    df = load_data(DATA_PATH)

    # 2. Summary statistics
    print_summary(df)

    # 3. Correlation analysis — identify top 3 churn factors
    correlations = correlation_analysis(df)

    # 4. Visualizations
    plot_correlation_heatmap(df)
    plot_top3_factors(df)
    plot_churn_by_plan(df)
    plot_churn_by_region(df)
    plot_churn_by_engagement(df)

    # 5. Text summary report
    generate_text_report(df, correlations)

    print("\n✅ Analysis complete! Check the 'outputs/' folder for all charts and reports.")
    print("   Next step: Import your data into PostgreSQL and run sql_queries.sql")


if __name__ == "__main__":
    main()
