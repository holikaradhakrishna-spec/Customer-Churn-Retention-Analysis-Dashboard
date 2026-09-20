"""
Project: Customer Churn & Retention Analysis Dashboard
Author: R Holika (Reg. No: 22MID0307)
Script: scripts/test_and_verify.py
Description: Automated test suite that validates the database schema, data integrity,
             SQL queries, 30-day churn classification logic, boundary cases,
             and headline KPIs.
"""

import sqlite3
import pandas as pd
from datetime import date, datetime
import os
import sys

def run_tests():
    print("=" * 70)
    print("CUSTOMER CHURN & RETENTION ANALYSIS - AUTOMATED VERIFICATION SUITE")
    print("Author: R Holika (Reg. No: 22MID0307)")
    print("=" * 70)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    # ---------------------------------------------------------
    # TEST 1: File Existence & Completeness
    # ---------------------------------------------------------
    print("\n[TEST 1] Checking Core Project Files...")
    required_files = [
        os.path.join(data_dir, 'customers.csv'),
        os.path.join(data_dir, 'subscriptions.csv'),
        os.path.join(data_dir, 'customer_activity.csv'),
        os.path.join(data_dir, 'churn_analysis_dataset.csv'),
        os.path.join(base_dir, 'power_bi', 'customer_churn_analysis_dashboard.pbix'),
        os.path.join(base_dir, 'sql', '01_create_tables.sql'),
        os.path.join(base_dir, 'sql', '02_insert_data.sql'),
        os.path.join(base_dir, 'sql', '03_churn_classification.sql'),
        os.path.join(base_dir, 'sql', '04_kpi_metrics.sql'),
        os.path.join(base_dir, 'sql', '05_plan_and_country_analysis.sql'),
    ]
    for rf in required_files:
        assert os.path.exists(rf), f"Missing required file: {rf}"
        print(f"  [OK] Found: {os.path.relpath(rf, base_dir)}")
    print("  -> File presence: PASSED")

    # ---------------------------------------------------------
    # TEST 2: In-Memory SQLite Database Setup & Schema Creation
    # ---------------------------------------------------------
    print("\n[TEST 2] Testing Database Setup & SQL Schema Creation...")
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    with open(os.path.join(base_dir, 'sql', '01_create_tables.sql'), 'r') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    assert 'customers' in tables, "Table 'customers' was not created!"
    assert 'subscriptions' in tables, "Table 'subscriptions' was not created!"
    assert 'customer_activity' in tables, "Table 'customer_activity' was not created!"
    print(f"  [OK] Successfully created tables: {tables}")
    print("  -> Schema verification: PASSED")

    # ---------------------------------------------------------
    # TEST 3: Data Ingestion & Referential Integrity
    # ---------------------------------------------------------
    print("\n[TEST 3] Loading Seed Data & Checking Integrity...")
    with open(os.path.join(base_dir, 'sql', '02_insert_data.sql'), 'r') as f:
        insert_sql = f.read()
    cursor.executescript(insert_sql)
    
    cursor.execute("SELECT COUNT(*) FROM customers;")
    n_cust = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM subscriptions;")
    n_subs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM customer_activity;")
    n_act = cursor.fetchone()[0]
    
    assert n_cust == 30, f"Expected 30 customers, got {n_cust}"
    assert n_subs == 30, f"Expected 30 subscriptions, got {n_subs}"
    assert n_act == 30, f"Expected 30 activity records, got {n_act}"
    print(f"  [OK] Record counts: {n_cust} customers, {n_subs} subscriptions, {n_act} activity rows")
    
    # Check no foreign key / orphan mismatches
    cursor.execute("""
        SELECT COUNT(*) FROM subscriptions s 
        LEFT JOIN customers c ON s.customer_id = c.customer_id 
        WHERE c.customer_id IS NULL;
    """)
    orphan_subs = cursor.fetchone()[0]
    assert orphan_subs == 0, f"Found {orphan_subs} orphan subscription rows!"

    cursor.execute("""
        SELECT COUNT(*) FROM customer_activity a 
        LEFT JOIN customers c ON a.customer_id = c.customer_id 
        WHERE c.customer_id IS NULL;
    """)
    orphan_acts = cursor.fetchone()[0]
    assert orphan_acts == 0, f"Found {orphan_acts} orphan activity rows!"
    print("  [OK] Zero orphan records, referential integrity confirmed")
    print("  -> Data ingestion: PASSED")

    # ---------------------------------------------------------
    # TEST 4: Churn Classification & 30-Day Logic Verification
    # ---------------------------------------------------------
    print("\n[TEST 4] Verifying 30-Day Inactivity Churn Classification Logic...")
    
    churn_query = """
    SELECT 
        c.customer_id,
        c.customer_name,
        c.country,
        s.plan_type,
        s.monthly_fee,
        MAX(a.activity_date) AS last_activity_date,
        CASE 
            WHEN MAX(a.activity_date) IS NULL THEN NULL
            ELSE CAST(julianday('2025-12-20') - julianday(MAX(a.activity_date)) AS INT)
        END AS days_inactive,
        CASE
            WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
            WHEN CAST(julianday('2025-12-20') - julianday(MAX(a.activity_date)) AS INT) > 30 THEN 'Churned'
            ELSE 'Active'
        END AS customer_status
    FROM customers c
    LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
    LEFT JOIN customer_activity a ON c.customer_id = a.customer_id
    GROUP BY c.customer_id, c.customer_name, c.country, s.plan_type, s.monthly_fee
    ORDER BY c.customer_id;
    """
    classified_df = pd.read_sql_query(churn_query, conn)
    assert len(classified_df) == 30, f"Expected 30 classified rows, got {len(classified_df)}"
    
    # Verify Boundary Cases:
    # 1. Zero activity customer (customer 29, 30) -> MUST be 'Churned'
    c29 = classified_df[classified_df['customer_id'] == 29].iloc[0]
    c30 = classified_df[classified_df['customer_id'] == 30].iloc[0]
    assert c29['customer_status'] == 'Churned' and pd.isna(c29['last_activity_date']), "Customer 29 must be Churned with NULL activity"
    assert c30['customer_status'] == 'Churned' and pd.isna(c30['last_activity_date']), "Customer 30 must be Churned with NULL activity"
    print("  [OK] Boundary Case 1 (NULL activity): Customers 29 & 30 correctly classified as Churned")
    
    # 2. Recently active (e.g. Customer 13, active on 2025-12-19 = 1 day ago) -> Active
    c13 = classified_df[classified_df['customer_id'] == 13].iloc[0]
    assert c13['customer_status'] == 'Active' and c13['days_inactive'] == 1, "Customer 13 must be Active"
    print("  [OK] Boundary Case 2 (1 day inactive): Customer 13 correctly classified as Active")

    # 3. Active within 30 days (e.g. Customer 16, active on 2025-11-30 = 20 days ago) -> Active
    c16 = classified_df[classified_df['customer_id'] == 16].iloc[0]
    assert c16['customer_status'] == 'Active' and c16['days_inactive'] == 20, "Customer 16 must be Active"
    print("  [OK] Boundary Case 3 (20 days inactive <= 30): Customer 16 correctly classified as Active")

    # 4. Inactive > 30 days (e.g. Customer 23, active on 2025-11-01 = 49 days ago) -> Churned
    c23 = classified_df[classified_df['customer_id'] == 23].iloc[0]
    assert c23['customer_status'] == 'Churned' and c23['days_inactive'] == 49, "Customer 23 must be Churned"
    print("  [OK] Boundary Case 4 (49 days inactive > 30): Customer 23 correctly classified as Churned")

    # 5. Long inactive (e.g. Customer 21, active on 2025-07-20 = 153 days ago) -> Churned
    c21 = classified_df[classified_df['customer_id'] == 21].iloc[0]
    assert c21['customer_status'] == 'Churned' and c21['days_inactive'] == 153, "Customer 21 must be Churned"
    print("  [OK] Boundary Case 5 (153 days inactive): Customer 21 correctly classified as Churned")
    print("  -> Churn logic verification: PASSED")

    # ---------------------------------------------------------
    # TEST 5: KPI Aggregation & Formula Consistency
    # ---------------------------------------------------------
    print("\n[TEST 5] Verifying KPI Calculations & Mathematical Consistency...")
    kpi_query = """
    SELECT 
        COUNT(*) AS total_customers,
        SUM(CASE WHEN customer_status = 'Active' THEN 1 ELSE 0 END) AS active_customers,
        SUM(CASE WHEN customer_status = 'Churned' THEN 1 ELSE 0 END) AS churned_customers,
        ROUND(SUM(CASE WHEN customer_status = 'Churned' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS churn_percentage
    FROM (
        SELECT 
            c.customer_id,
            CASE
                WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
                WHEN CAST(julianday('2025-12-20') - julianday(MAX(a.activity_date)) AS INT) > 30 THEN 'Churned'
                ELSE 'Active'
            END AS customer_status
        FROM customers c
        LEFT JOIN customer_activity a ON c.customer_id = a.customer_id
        GROUP BY c.customer_id
    );
    """
    cursor.execute(kpi_query)
    total, active, churned, churn_pct = cursor.fetchone()
    
    print(f"  - Total Customers:   {total}")
    print(f"  - Active Customers:  {active}")
    print(f"  - Churned Customers: {churned}")
    print(f"  - Overall Churn %:   {churn_pct}%")
    
    assert total == 30, f"Expected total 30, got {total}"
    assert active == 14, f"Expected active 14, got {active}"
    assert churned == 16, f"Expected churned 16, got {churned}"
    assert total == (active + churned), "Total must strictly equal active + churned!"
    expected_pct = round(16 * 100.0 / 30, 2)
    assert churn_pct == expected_pct, f"Expected churn % {expected_pct}, got {churn_pct}"
    print("  [OK] Headline KPIs verified against independent mathematical formulas")

    # Plan-Level KPIs
    print("\n[TEST 6] Verifying KPIs across Subscription Plans...")
    plan_query = """
    SELECT 
        s.plan_type,
        COUNT(*) AS total_customers,
        SUM(CASE WHEN cs.customer_status = 'Active' THEN 1 ELSE 0 END) AS active_customers,
        SUM(CASE WHEN cs.customer_status = 'Churned' THEN 1 ELSE 0 END) AS churned_customers,
        ROUND(SUM(CASE WHEN cs.customer_status = 'Churned' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS churn_percentage
    FROM (
        SELECT 
            c.customer_id,
            CASE
                WHEN MAX(a.activity_date) IS NULL THEN 'Churned'
                WHEN CAST(julianday('2025-12-20') - julianday(MAX(a.activity_date)) AS INT) > 30 THEN 'Churned'
                ELSE 'Active'
            END AS customer_status
        FROM customers c
        LEFT JOIN customer_activity a ON c.customer_id = a.customer_id
        GROUP BY c.customer_id
    ) cs
    JOIN subscriptions s ON cs.customer_id = s.customer_id
    GROUP BY s.plan_type
    ORDER BY s.plan_type;
    """
    cursor.execute(plan_query)
    plan_results = {r[0]: {'total': r[1], 'active': r[2], 'churned': r[3], 'pct': r[4]} for r in cursor.fetchall()}
    
    print(f"  - Basic Plan:   {plan_results['Basic']['churned']}/{plan_results['Basic']['total']} Churned ({plan_results['Basic']['pct']}%)")
    print(f"  - Premium Plan: {plan_results['Premium']['churned']}/{plan_results['Premium']['total']} Churned ({plan_results['Premium']['pct']}%)")
    
    assert plan_results['Basic']['total'] == 15
    assert plan_results['Basic']['churned'] == 11
    assert plan_results['Basic']['pct'] == 73.33
    
    assert plan_results['Premium']['total'] == 15
    assert plan_results['Premium']['churned'] == 5
    assert plan_results['Premium']['pct'] == 33.33
    print("  [OK] Plan-level churn performance confirmed")
    print("  -> Plan KPIs: PASSED")

    # ---------------------------------------------------------
    # TEST 7: Power BI PBIX File Inspection
    # ---------------------------------------------------------
    print("\n[TEST 7] Verifying Power BI Dashboard PBIX Contents...")
    import zipfile, json
    pbix_path = os.path.join(base_dir, 'power_bi', 'customer_churn_analysis_dashboard.pbix')
    with zipfile.ZipFile(pbix_path, 'r') as z:
        layout_raw = z.read('Report/Layout').decode('utf-16-le')
        layout = json.loads(layout_raw)
        sections = layout.get('sections', [])
        assert len(sections) >= 1, "PBIX has no report pages!"
        visuals = sections[0].get('visualContainers', [])
        print(f"  [OK] Power BI Report Page: '{sections[0].get('displayName')}' with {len(visuals)} visual containers")
        assert len(visuals) == 12, f"Expected 12 visuals, found {len(visuals)}"
        
        # Verify required measures and columns exist in layout
        required_dax = ['total customers', 'active customers', 'churned customers', 'churn %']
        for d in required_dax:
            assert d in layout_raw, f"Required DAX measure '{d}' not found in PBIX!"
            print(f"  [OK] Verified DAX visual binding: [{d}]")
            
        required_dims = ['plan_type', 'customer_status', 'country']
        for dim in required_dims:
            assert dim in layout_raw, f"Required dimension '{dim}' not found in PBIX!"
            print(f"  [OK] Verified dimension visual binding: [{dim}]")
            
    print("  -> Power BI Dashboard internal inspection: PASSED")

    print("\n" + "=" * 70)
    print("ALL 7 VERIFICATION TESTS PASSED SUCCESSFULLY! (100% ACCURACY)")
    print("=" * 70)
    return True

if __name__ == '__main__':
    success = run_tests()
    if not success:
        sys.exit(1)
