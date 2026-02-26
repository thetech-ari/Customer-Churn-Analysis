-- ============================================================
-- sql_queries.sql
-- Customer Churn Analysis - Analytical SQL Queries
-- Author: Arianna
-- Project: Portfolio Project 1 - Customer Churn Analysis
--
-- HOW TO USE:
--   Run each query independently in pgAdmin or psql.
--   Each query is self-contained with a comment explaining:
--     - WHAT it calculates
--     - WHY it matters (business value)
--     - HOW the SQL technique works
-- ============================================================


-- ============================================================
-- SECTION 1: CORE CHURN METRICS
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- Query 1.1: Overall Churn Rate
-- WHAT: The percentage of all customers who have churned.
-- WHY:  The single most important KPI for a subscription business.
--       A healthy SaaS product targets < 5% monthly churn.
-- HOW:  AVG on a boolean (0/1) column gives us the proportion.
-- ──────────────────────────────────────────────────────────
SELECT
    COUNT(*)                                            AS total_customers,
    SUM(is_churned::INT)                                AS total_churned,
    COUNT(*) - SUM(is_churned::INT)                     AS total_active,
    ROUND(AVG(is_churned::NUMERIC) * 100, 2)            AS churn_rate_pct,
    ROUND((1 - AVG(is_churned::NUMERIC)) * 100, 2)      AS retention_rate_pct
FROM customers;


-- ──────────────────────────────────────────────────────────
-- Query 1.2: Average Customer Lifetime
-- WHAT: How long customers stay on average (in days/months).
-- WHY:  Directly feeds into LTV (Lifetime Value) calculations.
--       Longer lifetime = more revenue per acquired customer.
-- HOW:  customer_lifetime_days is pre-computed in generate_data.py.
--       For churned customers it's days until cancel; for active,
--       it's days since joining.
-- ──────────────────────────────────────────────────────────
SELECT
    CASE WHEN is_churned THEN 'Churned' ELSE 'Active' END   AS customer_status,
    COUNT(*)                                                AS customer_count,
    ROUND(AVG(customer_lifetime_days), 0)                   AS avg_lifetime_days,
    ROUND(AVG(customer_lifetime_days) / 30.0, 1)            AS avg_lifetime_months,
    ROUND(MIN(customer_lifetime_days), 0)                   AS min_lifetime_days,
    ROUND(MAX(customer_lifetime_days), 0)                   AS max_lifetime_days
FROM customers
GROUP BY is_churned
ORDER BY is_churned;


-- ──────────────────────────────────────────────────────────
-- Query 1.3: Monthly Revenue by Plan (MRR breakdown)
-- WHAT: Monthly Recurring Revenue split by subscription tier.
-- WHY:  Tells us which plan drives the most revenue — and which
--       tier's churn is most costly to the business.
-- HOW:  JOIN customers → subscriptions → subscription_plans.
--       FILTER to active only for current MRR snapshot.
-- ──────────────────────────────────────────────────────────
SELECT
    sp.plan_name,
    sp.price                                            AS monthly_price,
    COUNT(c.customer_id)                                AS active_subscribers,
    ROUND(COUNT(c.customer_id) * sp.price, 2)           AS monthly_revenue,
    ROUND(AVG(c.is_churned::NUMERIC) * 100, 2)          AS churn_rate_pct
FROM customers         c
JOIN subscriptions     s  ON c.customer_id = s.customer_id
JOIN subscription_plans sp ON s.plan_id    = sp.plan_id
WHERE s.is_active = TRUE
GROUP BY sp.plan_name, sp.price
ORDER BY sp.price DESC;


-- ──────────────────────────────────────────────────────────
-- Query 1.4: Revenue Lost to Churn
-- WHAT: Monthly revenue that would have continued if churned
--       customers had stayed.
-- WHY:  Puts a dollar amount on churn — critical for justifying
--       retention program investments.
-- ──────────────────────────────────────────────────────────
SELECT
    sp.plan_name,
    COUNT(c.customer_id)                                AS churned_customers,
    ROUND(COUNT(c.customer_id) * sp.price, 2)           AS monthly_revenue_lost,
    ROUND(COUNT(c.customer_id) * sp.price * 12, 2)      AS annualized_revenue_lost
FROM customers         c
JOIN subscriptions     s   ON c.customer_id = s.customer_id AND s.is_active = FALSE
JOIN subscription_plans sp ON s.plan_id     = sp.plan_id
WHERE c.is_churned = TRUE
GROUP BY sp.plan_name, sp.price
ORDER BY monthly_revenue_lost DESC;


-- ============================================================
-- SECTION 2: CHURN BY SEGMENT (WINDOW FUNCTIONS)
-- These use advanced SQL techniques: GROUP BY, CASE, ROLLUP
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- Query 2.1: Churn Rate by Region
-- WHAT: Which geographic regions have the highest churn?
-- WHY:  Could indicate region-specific pricing issues, content
--       gaps, or competitor presence.
-- HOW:  GROUP BY region, then calculate churn within each group.
-- ──────────────────────────────────────────────────────────
SELECT
    region,
    COUNT(*)                                            AS total_customers,
    SUM(is_churned::INT)                                AS churned,
    ROUND(AVG(is_churned::NUMERIC) * 100, 2)            AS churn_rate_pct,
    -- RANK() window function: ranks regions from highest to lowest churn
    RANK() OVER (ORDER BY AVG(is_churned::NUMERIC) DESC) AS churn_rank
FROM customers
GROUP BY region
ORDER BY churn_rate_pct DESC;


-- ──────────────────────────────────────────────────────────
-- Query 2.2: Churn Rate by Age Group
-- WHAT: Which age demographics churn the most?
-- WHY:  Helps marketing target retention campaigns at high-risk
--       age groups (e.g., younger subscribers who comparison-shop).
-- ──────────────────────────────────────────────────────────
SELECT
    age_group,
    COUNT(*)                                            AS total_customers,
    SUM(is_churned::INT)                                AS churned,
    ROUND(AVG(is_churned::NUMERIC) * 100, 2)            AS churn_rate_pct
FROM customers
GROUP BY age_group
ORDER BY age_group;


-- ──────────────────────────────────────────────────────────
-- Query 2.3: Churn Rate by Tenure Bucket
-- WHAT: Do customers churn more in their first 6 months?
-- WHY:  Onboarding problems often show up as early churn.
--       This tells us WHERE in the customer journey to intervene.
-- HOW:  CASE statement creates tenure buckets from raw tenure_months.
-- ──────────────────────────────────────────────────────────
SELECT
    CASE
        WHEN tenure_months < 3   THEN '0-3 months'
        WHEN tenure_months < 6   THEN '3-6 months'
        WHEN tenure_months < 12  THEN '6-12 months'
        WHEN tenure_months < 24  THEN '1-2 years'
        ELSE '2+ years'
    END                                                 AS tenure_bucket,
    COUNT(*)                                            AS total_customers,
    SUM(is_churned::INT)                                AS churned,
    ROUND(AVG(is_churned::NUMERIC) * 100, 2)            AS churn_rate_pct
FROM customers
GROUP BY tenure_bucket
ORDER BY
    CASE tenure_bucket
        WHEN '0-3 months'  THEN 1
        WHEN '3-6 months'  THEN 2
        WHEN '6-12 months' THEN 3
        WHEN '1-2 years'   THEN 4
        ELSE 5
    END;


-- ──────────────────────────────────────────────────────────
-- Query 2.4: Churn Rate by Plan × Region (pivot-style)
-- WHAT: Cross-tab of churn across plan type AND region.
-- WHY:  Finds combinations that are uniquely problematic.
--       (e.g., "Premium plan in International region churns at 60%")
-- HOW:  GROUP BY two dimensions, then use FILTER for conditional aggregates.
-- ──────────────────────────────────────────────────────────
SELECT
    c.region,
    sp.plan_name,
    COUNT(c.customer_id)                                AS total_customers,
    SUM(c.is_churned::INT)                              AS churned_count,
    ROUND(AVG(c.is_churned::NUMERIC) * 100, 2)          AS churn_rate_pct
FROM customers          c
JOIN subscriptions      s  ON c.customer_id = s.customer_id
JOIN subscription_plans sp ON s.plan_id     = sp.plan_id
GROUP BY c.region, sp.plan_name
ORDER BY churn_rate_pct DESC;


-- ============================================================
-- SECTION 3: TIME-SERIES CHURN (WINDOW FUNCTIONS)
-- These queries show trends over time — great for dashboards.
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- Query 3.1: Monthly Churn Count (time series)
-- WHAT: How many customers cancelled in each calendar month?
-- WHY:  Identifies seasonality and sudden churn spikes.
-- HOW:  DATE_TRUNC truncates dates to the first of each month,
--       enabling GROUP BY month.
-- ──────────────────────────────────────────────────────────
SELECT
    DATE_TRUNC('month', cancellation_date)              AS churn_month,
    COUNT(*)                                            AS customers_churned,
    -- Running total of churned customers over time (cumulative churn)
    SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', cancellation_date)) AS cumulative_churned
FROM customers
WHERE is_churned = TRUE
  AND cancellation_date IS NOT NULL
GROUP BY churn_month
ORDER BY churn_month;


-- ──────────────────────────────────────────────────────────
-- Query 3.2: New Subscriptions vs Churn per Month (net growth)
-- WHAT: Were we growing or shrinking each month?
-- WHY:  Net Growth = New Signups − Churned. Negative net growth
--       means churn is outpacing acquisition.
-- HOW:  CTEs (WITH clause) compute new signups and churn separately,
--       then we JOIN them on month for the final result.
--
-- KEY CONCEPT — CTE (Common Table Expression):
--   A CTE is a named temporary result set defined with WITH.
--   Think of it as a "named subquery". CTEs make complex queries
--   readable by breaking them into logical steps.
-- ──────────────────────────────────────────────────────────
WITH monthly_signups AS (
    -- Step 1: Count new customers per month
    SELECT
        DATE_TRUNC('month', join_date)  AS month,
        COUNT(*)                        AS new_customers
    FROM customers
    GROUP BY month
),
monthly_churn AS (
    -- Step 2: Count churned customers per month
    SELECT
        DATE_TRUNC('month', cancellation_date)  AS month,
        COUNT(*)                                AS churned_customers
    FROM customers
    WHERE is_churned = TRUE
      AND cancellation_date IS NOT NULL
    GROUP BY month
)
-- Step 3: Combine both CTEs
SELECT
    COALESCE(s.month, c.month)          AS month,
    COALESCE(s.new_customers, 0)        AS new_customers,
    COALESCE(c.churned_customers, 0)    AS churned_customers,
    -- Net growth: positive = growing, negative = shrinking
    COALESCE(s.new_customers, 0) - COALESCE(c.churned_customers, 0) AS net_growth
FROM monthly_signups s
FULL OUTER JOIN monthly_churn c ON s.month = c.month
ORDER BY month;


-- ──────────────────────────────────────────────────────────
-- Query 3.3: 30-Day Rolling Churn Rate
-- WHAT: Churn rate calculated over the past 30 days at any point.
-- WHY:  Smoother than a monthly snapshot — shows trends more clearly
--       and matches how many SaaS dashboards report churn.
-- HOW:  LAG() window function looks back at prior rows.
--       This is a PostgreSQL-specific advanced technique.
-- ──────────────────────────────────────────────────────────
WITH daily_churn AS (
    SELECT
        cancellation_date::DATE                         AS churn_date,
        COUNT(*)                                        AS daily_churned
    FROM customers
    WHERE is_churned = TRUE
      AND cancellation_date IS NOT NULL
    GROUP BY churn_date
)
SELECT
    churn_date,
    daily_churned,
    -- SUM over a moving 30-day window (preceding 29 rows + current row)
    SUM(daily_churned) OVER (
        ORDER BY churn_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    )                                                   AS rolling_30d_churn
FROM daily_churn
ORDER BY churn_date;


-- ============================================================
-- SECTION 4: ENGAGEMENT & USAGE ANALYSIS
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- Query 4.1: Churn Rate by Login Frequency Tier
-- WHAT: Do low-engagement customers churn more?
-- WHY:  Engagement is often the #1 leading indicator of churn.
--       This proves (or disproves) that hypothesis in your data.
-- HOW:  CASE bins logins into buckets; then we compare churn rates.
-- ──────────────────────────────────────────────────────────
SELECT
    CASE
        WHEN um.avg_monthly_logins < 3  THEN 'Very Low (0-2/mo)'
        WHEN um.avg_monthly_logins < 8  THEN 'Low (3-7/mo)'
        WHEN um.avg_monthly_logins < 15 THEN 'Medium (8-14/mo)'
        ELSE                                 'High (15+/mo)'
    END                                                 AS engagement_tier,
    COUNT(c.customer_id)                                AS total_customers,
    SUM(c.is_churned::INT)                              AS churned,
    ROUND(AVG(c.is_churned::NUMERIC) * 100, 2)          AS churn_rate_pct,
    ROUND(AVG(um.avg_monthly_logins), 1)                AS avg_logins
FROM customers    c
JOIN usage_metrics um ON c.customer_id = um.customer_id
GROUP BY engagement_tier
ORDER BY churn_rate_pct DESC;


-- ──────────────────────────────────────────────────────────
-- Query 4.2: Billing Issues vs Churn
-- WHAT: Are customers with billing problems more likely to churn?
-- WHY:  A failed payment often triggers an involuntary churn.
--       Fixing billing flows can directly reduce churn.
-- ──────────────────────────────────────────────────────────
SELECT
    CASE
        WHEN um.billing_issues_count = 0 THEN 'No Issues'
        WHEN um.billing_issues_count = 1 THEN '1 Issue'
        ELSE '2+ Issues'
    END                                                 AS billing_issue_tier,
    COUNT(c.customer_id)                                AS total_customers,
    SUM(c.is_churned::INT)                              AS churned,
    ROUND(AVG(c.is_churned::NUMERIC) * 100, 2)          AS churn_rate_pct
FROM customers    c
JOIN usage_metrics um ON c.customer_id = um.customer_id
GROUP BY billing_issue_tier
ORDER BY churn_rate_pct DESC;


-- ──────────────────────────────────────────────────────────
-- Query 4.3: High-Risk Customer Identification
-- WHAT: Flag currently active customers who show churn risk signals.
-- WHY:  This is actionable — the business can reach out to these
--       customers proactively before they cancel.
-- HOW:  Multi-condition WHERE + JOIN across 3 tables.
--
-- CHURN RISK FLAGS:
--   - Tenure < 6 months (new and still evaluating)
--   - Login frequency < 5/month (low engagement)
--   - Any billing issues
-- ──────────────────────────────────────────────────────────
SELECT
    c.customer_id,
    c.age_group,
    c.region,
    sp.plan_name,
    sp.price                                            AS monthly_price,
    c.tenure_months,
    um.avg_monthly_logins,
    um.billing_issues_count,
    -- Risk score: more flags = higher score
    (
        CASE WHEN c.tenure_months < 6           THEN 1 ELSE 0 END +
        CASE WHEN um.avg_monthly_logins < 5     THEN 1 ELSE 0 END +
        CASE WHEN um.billing_issues_count > 0   THEN 1 ELSE 0 END
    )                                                   AS risk_score
FROM customers          c
JOIN subscriptions      s  ON c.customer_id = s.customer_id AND s.is_active = TRUE
JOIN subscription_plans sp ON s.plan_id     = sp.plan_id
JOIN usage_metrics      um ON c.customer_id = um.customer_id
WHERE c.is_churned = FALSE                             -- Active customers only
ORDER BY risk_score DESC, um.avg_monthly_logins ASC
LIMIT 100;


-- ──────────────────────────────────────────────────────────
-- Query 4.4: Top Cancellation Reasons
-- WHAT: Why do customers say they're leaving?
-- WHY:  Qualitative insight that complements quantitative churn rate.
--       Product teams use this to prioritize feature improvements.
-- ──────────────────────────────────────────────────────────
SELECT
    cancellation_reason,
    COUNT(*)                                            AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage_of_churned
FROM customers
WHERE is_churned = TRUE
  AND cancellation_reason IS NOT NULL
GROUP BY cancellation_reason
ORDER BY customer_count DESC;
