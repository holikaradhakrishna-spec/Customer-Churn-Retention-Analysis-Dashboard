-- ====================================================================
-- Project: Customer Churn & Retention Analysis Dashboard
-- Author: R Holika (Reg. No: 22MID0307)
-- Script: 04_kpi_metrics.sql
-- Description: Aggregates headline KPIs: Total Customers, Active Customers,
--              Churned Customers, and Overall Churn Percentage.
-- ====================================================================

-- --------------------------------------------------------------------
-- KPI Query 1: Count of Customers by Status (Active vs Churned)
-- Expected Output:
--   Active:  14
--   Churned: 16
-- --------------------------------------------------------------------
SELECT 
    customer_status,
    COUNT(*) AS total_customers
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
) classified_customers
GROUP BY customer_status;


-- --------------------------------------------------------------------
-- KPI Query 2: Executive KPI Summary in a Single Row
-- Expected Output:
--   total_customers: 30
--   active_customers: 14
--   churned_customers: 16
--   churn_percentage: 53.33%
-- --------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_customers,
    SUM(CASE WHEN customer_status = 'Active' THEN 1 ELSE 0 END) AS active_customers,
    SUM(CASE WHEN customer_status = 'Churned' THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(
        SUM(CASE WHEN customer_status = 'Churned' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
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
) classified_customers;
