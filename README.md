# 📊 Customer Churn Analysis — Subscription Service

> **End-to-end data analysis project** identifying why customers cancel and who's at highest risk of churning next.  
> Built with PostgreSQL · Python · Pandas · Seaborn · Matplotlib

---

## 🔍 Project Overview

Subscription businesses lose revenue every time a customer cancels. This project simulates the full workflow a data analyst would follow at a streaming or SaaS company — from raw data ingestion to actionable business recommendations.

**Business Question:** *Which customers are most likely to churn, and what factors drive cancellation?*

**Answer Found:** Three factors account for the majority of churn risk:
1. 🔴 **Low engagement** — customers logging in < 3×/month churn at 3–4× the rate of active users
2. 🟡 **Short tenure** — customers in their first 0–3 months have the highest churn rate
3. 🟠 **Billing issues** — even 1 failed payment doubles a customer's churn probability

---

## 📁 Repository Structure

```
customer-churn-analysis/
│
├── data/                         # Auto-generated when you run generate_data.py
│   ├── customers_raw.csv         # Raw dataset (includes intentional data quality issues)
│   ├── customers_clean.csv       # Cleaned dataset ready for SQL import
│   └── subscriptions.csv        # Subscription plan lookup table
│
├── outputs/                      # Auto-generated when you run churn_analysis.py
│   ├── top3_churn_factors.png    # ⭐ Main findings chart
│   ├── correlation_heatmap.png   # Feature correlation matrix
│   ├── churn_by_plan.png
│   ├── churn_by_region.png
│   ├── churn_by_engagement.png
│   └── churn_summary_report.txt  # Plain-text findings report
│
├── generate_data.py              # Step 1: Synthetic data generation + cleaning pipeline
├── sql_schema.sql                # Step 2: PostgreSQL database schema (4 normalized tables)
├── sql_queries.sql               # Step 3: 12 analytical SQL queries
├── churn_analysis.py             # Step 4: EDA, correlation analysis, visualizations
│
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Data generation, cleaning, analysis |
| PostgreSQL | 14+ | Relational database & SQL analysis |
| pandas | 2.x | Data manipulation |
| matplotlib | 3.x | Visualizations |
| seaborn | 0.13+ | Statistical charts |
| numpy | 1.x | Numerical operations |

---

## 🚀 How to Run This Project

### Prerequisites

Make sure you have Python and PostgreSQL installed.

```bash
# Check Python version (need 3.10+)
python3 --version

# Install required Python libraries
pip install pandas numpy matplotlib seaborn scikit-learn
```

---

### Step 1 — Generate the Dataset

```bash
python3 generate_data.py
```

**What this does:**
- Generates **10,500 synthetic customer records** with realistic churn behavior
- Intentionally introduces data quality issues (duplicates, nulls, mixed date formats, inconsistent capitalization)
- Cleans the data (removing 141 duplicates, filling 535 null plan prices, standardizing dates)
- Saves `data/customers_raw.csv` and `data/customers_clean.csv`

**Output preview:**
```
✅ Generated 10,500 customer records. Churn rate: 28.7%
✅ Dataset now has 10,700 rows (including duplicates & nulls)
[1/6] Removed 141 duplicate rows → 10,559 remaining
[4/6] Filled 535 missing plan_price values using plan lookup
✅ Cleaning complete! Final dataset: 10,559 rows
```

---

### Step 2 — Set Up PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE churn_analysis;
\c churn_analysis

# Run the schema file
\i path/to/sql_schema.sql
```

Then import the cleaned CSV data:
```sql
-- Update the file path to match your local system
COPY customers (customer_id, age, age_group, region, payment_method,
                join_date, tenure_months, is_churned, cancellation_date,
                cancellation_reason, customer_lifetime_days)
FROM '/full/path/to/data/customers_clean.csv'
DELIMITER ',' CSV HEADER;
```

---

### Step 3 — Run SQL Queries

Open `sql_queries.sql` in pgAdmin or run via terminal:

```bash
psql -U postgres -d churn_analysis -f sql_queries.sql
```

The file contains **12 queries** organized into 4 sections:
- **Section 1:** Core KPIs (overall churn rate, avg lifetime, MRR, revenue lost)
- **Section 2:** Churn by segment (region, age group, tenure, plan × region)
- **Section 3:** Time-series analysis (monthly churn, net growth, 30-day rolling churn)
- **Section 4:** Engagement analysis (login tiers, billing issues, high-risk customer identification)

---

### Step 4 — Run Python Analysis

```bash
python3 churn_analysis.py
```

**What this does:**
- Prints a full descriptive statistics summary
- Runs Pearson/point-biserial correlation analysis against `is_churned`
- Generates 5 charts saved to `outputs/`
- Writes a plain-text findings report to `outputs/churn_summary_report.txt`

---

## 📊 Key Findings

### Overall Metrics
| Metric | Value |
|--------|-------|
| Total Customers | 10,559 |
| Overall Churn Rate | 28.8% |
| Avg Customer Lifetime (churned) | 11.6 months |
| Avg Customer Lifetime (active) | 24+ months |

### Churn Rate by Subscription Plan
| Plan | Price | Churn Rate |
|------|-------|-----------|
| Basic | $9.99/mo | 25.5% |
| Standard | $15.99/mo | 29.4% |
| Premium | $22.99/mo | 33.7% |

### Churn Rate by Region
| Region | Churn Rate |
|--------|-----------|
| International | 37.5% |
| Northeast | 28.9% |
| Southwest | 28.6% |
| West | 27.5% |
| Southeast | 26.9% |
| Midwest | 26.3% |

---

## 📈 Visualizations

### Top 3 Churn Drivers
![Top 3 Churn Factors](outputs/top3_churn_factors.png)

### Feature Correlation Heatmap
![Correlation Heatmap](outputs/correlation_heatmap.png)

---

## 💡 Business Recommendations

Based on the analysis, three high-impact interventions could meaningfully reduce churn:

1. **Re-engagement campaigns** — Trigger automated emails when a customer goes 7+ days without logging in. Low-login customers churn at 3–4× the baseline rate.

2. **Onboarding sequence for new subscribers** — Customers in month 0–3 have the highest churn rate. A structured welcome sequence (tutorials, feature tips, check-in emails) can reduce early dropout.

3. **Billing failure recovery** — Customers with even 1 billing issue churn at 2× the rate. Improving payment retry logic and sending proactive notifications before a card declines is one of the highest-ROI interventions available.

---

## 🧹 Data Cleaning Techniques Used

| Issue | Scale | Fix Applied |
|-------|-------|-------------|
| Duplicate rows | 141 rows | `drop_duplicates()` |
| Inconsistent capitalization | ~10% of plan_name | `str.title()` |
| Mixed date formats | ~8% of join_date | `pd.to_datetime(format='mixed')` |
| Missing plan_price | 535 rows (5%) | Lookup fill from plan_name |
| Missing region | 321 rows (3%) | Filled with `'Unknown'` |
| Invalid date order | Validated | Checked `cancellation_date >= join_date` |

---

## 🗄️ Database Schema

```
subscription_plans          customers
─────────────────          ─────────────────────────────
plan_id (PK)           ←── plan_name (via subscriptions)
plan_name                   customer_id (PK)
price                       age, age_group, region
features                    payment_method
                            join_date, tenure_months
                            is_churned
subscriptions               cancellation_date, reason
─────────────────           customer_lifetime_days
subscription_id (PK)
customer_id (FK) ──────────────────────────────────────
plan_id (FK)               usage_metrics
start_date, end_date       ─────────────────────────────
is_active                   metric_id (PK)
                            customer_id (FK) ───────────
                            avg_monthly_logins
                            avg_session_minutes
                            support_tickets
                            billing_issues_count
```

---

## 📚 SQL Techniques Demonstrated

- `JOIN` (INNER, LEFT, FULL OUTER) across multiple tables
- `WITH` clause (CTEs) for readable, multi-step queries
- Window functions: `RANK()`, `SUM() OVER()`, `ROWS BETWEEN` (rolling aggregates)
- `CASE` statements for categorical bucketing and risk scoring
- `DATE_TRUNC()` for time-series grouping by month
- `COALESCE()` for null-safe calculations
- Constraint-based data integrity validation

---

## 🧠 Python Skills Demonstrated

- Synthetic data generation with realistic statistical distributions (`numpy`, `random`)
- Full data cleaning pipeline with documented decision-making
- Pearson / point-biserial correlation analysis via `df.corr()`
- Multi-panel `matplotlib` subplots for storytelling
- `seaborn` heatmaps and statistical charts
- Professional docstrings with interview talking points

---

## 👤 Author

**Arianna** | [@thetech-ari](https://github.com/thetech-ari)  
Computer Science Student (AI Concentration) · Full Sail University  
Graduating Fall 2026

---

*Part of a 10-project data analyst portfolio. Built to demonstrate SQL mastery, Python data skills, and business-focused analytical thinking.*
#   C u s t o m e r - C h u r n - A n a l y s i s  
 