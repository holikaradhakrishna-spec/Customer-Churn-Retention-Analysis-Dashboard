-- ====================================================================
-- Project: Customer Churn & Retention Analysis Dashboard
-- Author: R Holika (Reg. No: 22MID0307)
-- Script: 03_churn_classification.sql
-- Description: Core customer churn classification using a 30-day
--              inactivity threshold against reference date (2025-12-20).
-- ====================================================================

-- --------------------------------------------------------------------
-- STEP 1: Find the latest (most recent) activity date for each customer
-- --------------------------------------------------------------------
SELECT 
    customer_id,
    MAX(activity_date) AS last_activity_date
FROM customer_activity
GROUP BY customer_id;


-- --------------------------------------------------------------------
-- STEP 2: Left Join with customers table
-- Ensures customers with NO activity records are not excluded (preserves NULLs)
-- --------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.customer_name,
    c.country,
    c.signup_date,
    MAX(a.activity_date) AS last_activity_date
FROM customers c
LEFT JOIN customer_activity a
    ON c.customer_id = a.customer_id
GROUP BY 
    c.customer_id, 
    c.customer_name,
    c.country,
    c.signup_date;


-- --------------------------------------------------------------------
-- STEP 3: Core Churn Classification Logic
-- Business Rule:
-- 1. If MAX(activity_date) IS NULL -> 'Churned' (Signed up but never active)
-- 2. If DATEDIFF('2025-12-20', MAX(activity_date)) > 30 -> 'Churned' (Inactive > 30 days)
-- 3. Otherwise (<= 30 days inactive) -> 'Active'
-- --------------------------------------------------------------------

-- MySQL Syntax:
SELECT 
    c.customer_id,
    c.customer_name,
    c.country,
    s.plan_type,
    s.monthly_fee,
    MAX(a.activity_date) AS last_activity_date,
    DATEDIFF('2025-12-20', MAX(a.activity_date)) AS days_inactive,
    CASE
        WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
        WHEN DATEDIFF('2025-12-20', MAX(a.activity_date)) > 30 THEN 'Churned'
        ELSE 'Active'
    END AS customer_status
FROM customers c
LEFT JOIN subscriptions s
    ON c.customer_id = s.customer_id
LEFT JOIN customer_activity a
    ON c.customer_id = a.customer_id
GROUP BY 
    c.customer_id,
    c.customer_name,
    c.country,
    s.plan_type,
    s.monthly_fee
ORDER BY c.customer_id;

/*
-- Cross-Database Dialect Equivalents:
-- SQLite:
--   WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
--   WHEN CAST(julianday('2025-12-20') - julianday(MAX(a.activity_date)) AS INT) > 30 THEN 'Churned'
--   ELSE 'Active'

-- PostgreSQL:
--   WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
--   WHEN ('2025-12-20'::DATE - MAX(a.activity_date)) > 30 THEN 'Churned'
--   ELSE 'Active'

-- SQL Server (T-SQL):
--   WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
--   WHEN DATEDIFF(day, MAX(a.activity_date), '2025-12-20') > 30 THEN 'Churned'
--   ELSE 'Active'
*/
