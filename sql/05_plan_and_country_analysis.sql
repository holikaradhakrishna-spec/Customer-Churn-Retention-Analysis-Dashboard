-- ====================================================================
-- Project: Customer Churn & Retention Analysis Dashboard
-- Author: R Holika (Reg. No: 22MID0307)
-- Script: 05_plan_and_country_analysis.sql
-- Description: Breakdown of churn and retention performance across
--              subscription plans and geographical countries.
-- ====================================================================

-- --------------------------------------------------------------------
-- Query 1: Churn Performance by Subscription Plan
-- Expected Output:
--   Basic:   11 Churned / 15 Total (73.33% Churn)
--   Premium:  5 Churned / 15 Total (33.33% Churn)
-- --------------------------------------------------------------------
SELECT 
    s.plan_type,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN cs.customer_status = 'Active' THEN 1 ELSE 0 END) AS active_customers,
    SUM(CASE WHEN cs.customer_status = 'Churned' THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(
        SUM(CASE WHEN cs.customer_status = 'Churned' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS churn_percentage
FROM (
    SELECT 
        c.customer_id,
        CASE
            WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
            WHEN DATEDIFF('2025-12-20', MAX(a.activity_date)) > 30 THEN 'Churned'
            ELSE 'Active'
        END AS customer_status
    FROM customers c
    LEFT JOIN customer_activity a
        ON c.customer_id = a.customer_id
    GROUP BY c.customer_id
) cs
JOIN subscriptions s
    ON cs.customer_id = s.customer_id
GROUP BY s.plan_type
ORDER BY churn_percentage DESC;


-- --------------------------------------------------------------------
-- Query 2: Churn Performance by Country
-- Expected Output:
--   UK:    5 Churned /  6 Total (83.33% Churn)
--   USA:   3 Churned /  6 Total (50.00% Churn)
--   India: 8 Churned / 18 Total (44.44% Churn)
-- --------------------------------------------------------------------
SELECT 
    c.country,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN cs.customer_status = 'Active' THEN 1 ELSE 0 END) AS active_customers,
    SUM(CASE WHEN cs.customer_status = 'Churned' THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(
        SUM(CASE WHEN cs.customer_status = 'Churned' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS churn_percentage
FROM (
    SELECT 
        c.customer_id,
        CASE
            WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
            WHEN DATEDIFF('2025-12-20', MAX(a.activity_date)) > 30 THEN 'Churned'
            ELSE 'Active'
        END AS customer_status
    FROM customers c
    LEFT JOIN customer_activity a
        ON c.customer_id = a.customer_id
    GROUP BY c.customer_id
) cs
JOIN customers c
    ON cs.customer_id = c.customer_id
GROUP BY c.country
ORDER BY churn_percentage DESC;


-- --------------------------------------------------------------------
-- Query 3: Master Churn Dataset (View / Export for Power BI)
-- Combines demographic, subscription, latest activity, and status
-- --------------------------------------------------------------------
SELECT 
    c.customer_id,
    c.customer_name,
    c.country,
    c.signup_date,
    s.plan_type,
    s.monthly_fee,
    MAX(a.activity_date) AS last_activity_date,
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
    c.signup_date,
    s.plan_type,
    s.monthly_fee
ORDER BY c.customer_id;
