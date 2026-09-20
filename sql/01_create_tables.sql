-- ====================================================================
-- Project: Customer Churn & Retention Analysis Dashboard
-- Author: R Holika (Reg. No: 22MID0307)
-- Script: 01_create_tables.sql
-- Description: Creates the normalized relational tables for customers,
--              subscriptions, and customer activity logs.
-- Compatible with: MySQL 8+, PostgreSQL 12+, SQL Server 2016+, SQLite 3
-- ====================================================================

-- 1. Customers Table: Master customer demographic and registration information
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    signup_date DATE NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- 2. Subscriptions Table: Current subscription tier and monthly billing
CREATE TABLE IF NOT EXISTS subscriptions (
    customer_id INT PRIMARY KEY,
    plan_type VARCHAR(50) NOT NULL,
    monthly_fee DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 3. Customer Activity Table: Log of customer usage and interactions over time
CREATE TABLE IF NOT EXISTS customer_activity (
    activity_id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    activity_date DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
