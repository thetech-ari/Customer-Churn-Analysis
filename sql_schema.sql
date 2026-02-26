-- ============================================================
-- sql_schema.sql
-- Customer Churn Analysis - PostgreSQL Database Schema
-- Author: Arianna
-- Project: Portfolio Project 1 - Customer Churn Analysis
-- ============================================================
--
-- PURPOSE:
--   Defines the database schema for the churn analysis project.
--   The design follows 3NF (Third Normal Form) to avoid data redundancy.
--
-- HOW TO RUN (PostgreSQL):
--   1. Open pgAdmin or terminal
--   2. Connect to your database: psql -U postgres -d churn_db
--   3. Run: \i path/to/sql_schema.sql
--
-- TABLE OVERVIEW:
--   subscription_plans  → Lookup table for plan types and pricing
--   customers           → Core customer demographics and status
--   subscriptions       → Customer plan enrollment history
--   usage_metrics       → Monthly engagement/usage data per customer
-- ============================================================


-- ────────────────────────────────────────────────────────────
-- SETUP: Drop existing tables if re-running (dev convenience)
-- In production you would NEVER drop tables like this!
-- ────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS usage_metrics    CASCADE;
DROP TABLE IF EXISTS subscriptions    CASCADE;
DROP TABLE IF EXISTS customers        CASCADE;
DROP TABLE IF EXISTS subscription_plans CASCADE;


-- ────────────────────────────────────────────────────────────
-- TABLE 1: subscription_plans
-- Lookup/reference table for plan metadata.
-- Separating this out avoids repeating price data in every row
-- (this is what "normalizing" means — removing redundancy).
-- ────────────────────────────────────────────────────────────
CREATE TABLE subscription_plans (
    plan_id     SERIAL       PRIMARY KEY,
    plan_name   VARCHAR(50)  NOT NULL UNIQUE,   -- 'Basic', 'Standard', 'Premium'
    price       NUMERIC(6,2) NOT NULL CHECK (price > 0),
    features    TEXT,
    created_at  TIMESTAMP    DEFAULT NOW()
);

-- Seed the lookup table with plan data
INSERT INTO subscription_plans (plan_name, price, features) VALUES
    ('Basic',    9.99,  '1 screen, SD quality'),
    ('Standard', 15.99, '2 screens, HD quality'),
    ('Premium',  22.99, '4 screens, 4K quality');


-- ────────────────────────────────────────────────────────────
-- TABLE 2: customers
-- Core customer identity and demographic information.
-- Churn-related columns (is_churned, cancellation_date) sit here
-- because churn is a permanent status on the customer record.
-- ────────────────────────────────────────────────────────────
CREATE TABLE customers (
    customer_id             SERIAL       PRIMARY KEY,
    age                     SMALLINT     CHECK (age BETWEEN 18 AND 100),
    age_group               VARCHAR(10),                       -- e.g., '25-34'
    region                  VARCHAR(30),                       -- e.g., 'Northeast'
    payment_method          VARCHAR(30),
    join_date               DATE         NOT NULL,
    tenure_months           SMALLINT,                          -- Months since joining
    is_churned              BOOLEAN      NOT NULL DEFAULT FALSE,
    cancellation_date       DATE,
    cancellation_reason     VARCHAR(100),
    customer_lifetime_days  INTEGER,                           -- Days from join to cancel (or today)
    created_at              TIMESTAMP    DEFAULT NOW(),

    -- Data integrity: cancellation can't happen before joining
    CONSTRAINT chk_cancellation_after_join
        CHECK (cancellation_date IS NULL OR cancellation_date >= join_date)
);


-- ────────────────────────────────────────────────────────────
-- TABLE 3: subscriptions
-- Tracks which plan each customer is (or was) on.
-- Designed as a separate table so you could theoretically store
-- plan change history (one customer, multiple plan rows over time).
-- ────────────────────────────────────────────────────────────
CREATE TABLE subscriptions (
    subscription_id     SERIAL       PRIMARY KEY,
    customer_id         INTEGER      NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    plan_id             INTEGER      NOT NULL REFERENCES subscription_plans(plan_id),
    plan_name           VARCHAR(50),                          -- Denormalized for query convenience
    plan_price          NUMERIC(6,2) NOT NULL,
    start_date          DATE         NOT NULL,
    end_date            DATE,                                 -- NULL if still active
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_end_after_start
        CHECK (end_date IS NULL OR end_date >= start_date)
);


-- ────────────────────────────────────────────────────────────
-- TABLE 4: usage_metrics
-- Monthly engagement data per customer.
-- Storing this separately allows for time-series analysis
-- and keeps the customers table lean.
-- ────────────────────────────────────────────────────────────
CREATE TABLE usage_metrics (
    metric_id               SERIAL   PRIMARY KEY,
    customer_id             INTEGER  NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    avg_monthly_logins      NUMERIC(5,1),   -- Average logins per month
    avg_session_minutes     NUMERIC(6,1),   -- Average minutes per session
    support_tickets         SMALLINT DEFAULT 0,
    billing_issues_count    SMALLINT DEFAULT 0,
    recorded_at             TIMESTAMP DEFAULT NOW()
);


-- ────────────────────────────────────────────────────────────
-- INDEXES: Speed up common query patterns
-- Without indexes, every query would do a full table scan.
-- These cover the most frequent JOIN and WHERE conditions.
-- ────────────────────────────────────────────────────────────

-- Frequently filter/GROUP BY churn status
CREATE INDEX idx_customers_is_churned    ON customers(is_churned);

-- Frequently filter/GROUP BY plan, region, join date
CREATE INDEX idx_customers_region        ON customers(region);
CREATE INDEX idx_customers_join_date     ON customers(join_date);

-- Frequently JOIN subscriptions to customers
CREATE INDEX idx_subscriptions_customer  ON subscriptions(customer_id);
CREATE INDEX idx_subscriptions_plan      ON subscriptions(plan_id);

-- Frequently JOIN usage_metrics to customers
CREATE INDEX idx_usage_customer          ON usage_metrics(customer_id);


-- ────────────────────────────────────────────────────────────
-- IMPORT DATA (after running generate_data.py)
-- Update file paths to match your local setup.
-- ────────────────────────────────────────────────────────────
/*
-- Import customers
COPY customers (customer_id, age, age_group, region, payment_method,
                join_date, tenure_months, is_churned, cancellation_date,
                cancellation_reason, customer_lifetime_days)
FROM '/path/to/data/customers_clean.csv'
DELIMITER ','
CSV HEADER;

-- Import subscriptions (map from customers_clean.csv plan columns)
INSERT INTO subscriptions (customer_id, plan_id, plan_name, plan_price, start_date, end_date, is_active)
SELECT
    c.customer_id,
    sp.plan_id,
    c.plan_name,
    c.plan_price,
    c.join_date,
    c.cancellation_date,
    NOT c.is_churned
FROM customers c
JOIN subscription_plans sp ON c.plan_name = sp.plan_name;

-- Import usage_metrics
COPY usage_metrics (customer_id, avg_monthly_logins, avg_session_minutes,
                    support_tickets, billing_issues_count)
FROM '/path/to/data/customers_clean.csv'
DELIMITER ','
CSV HEADER;
*/


-- Verify tables created successfully
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
