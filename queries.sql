-- ============================================================================
-- queries.sql
-- Nassau Candy Distributor — Factory-to-Customer Shipping Route Efficiency
-- ANSI SQL / MySQL-compatible. Run against the cleaned table produced by
-- data_cleaning.py (load Nassau_Candy_Distributor_clean.csv as `shipments`).
--
-- Table assumed: shipments (
--   Row_ID, Order_ID, Order_Date, Ship_Date, Ship_Mode, Customer_ID,
--   Country_Region, City, State_Province, Postal_Code, Division, Region,
--   Product_ID, Product_Name, Sales, Units, Gross_Profit, Cost,
--   Shipping_Lead_Time_Days, Factory, Route, Order_Month
-- )
-- ============================================================================


-- ----------------------------------------------------------------------------
-- QUERY 1: Overall KPIs
-- Business question: "At a glance, how big is our shipping operation and
-- how efficient is it — total volume, total transactions, and average
-- shipping lead time?"
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*)                               AS total_shipments,
    COUNT(DISTINCT Order_ID)               AS total_orders,
    ROUND(SUM(Sales), 2)                   AS total_sales,
    ROUND(AVG(Sales), 2)                   AS avg_order_value,
    ROUND(AVG(Shipping_Lead_Time_Days), 2) AS avg_lead_time_days
FROM shipments;


-- ----------------------------------------------------------------------------
-- QUERY 2: Trend Analysis
-- Business question: "Is shipping performance getting better or worse over
-- time, and are certain months consistently slower (seasonality)?"
-- ----------------------------------------------------------------------------
SELECT
    Order_Month,
    COUNT(*)                               AS shipment_count,
    ROUND(SUM(Sales), 2)                   AS monthly_sales,
    ROUND(AVG(Shipping_Lead_Time_Days), 2) AS avg_lead_time_days
FROM shipments
GROUP BY Order_Month
ORDER BY Order_Month;


-- ----------------------------------------------------------------------------
-- QUERY 3: Categorical Breakdown
-- Business question: "Which ship modes and regions handle the most volume,
-- and how does their average lead time compare?"
-- ----------------------------------------------------------------------------
SELECT
    Region,
    Ship_Mode,
    COUNT(*)                               AS shipment_count,
    ROUND(AVG(Shipping_Lead_Time_Days), 2) AS avg_lead_time_days,
    ROUND(SUM(Sales), 2)                   AS total_sales
FROM shipments
GROUP BY Region, Ship_Mode
ORDER BY shipment_count DESC;


-- ----------------------------------------------------------------------------
-- QUERY 4: Advanced Aggregation — Route Efficiency Ranking
-- Business question: "Which factory-to-customer routes are the most and
-- least efficient, ranked by average lead time, with enough volume to be
-- statistically meaningful (>= 5 shipments)?"
-- Uses a CTE + window function (RANK) — appropriate entry-level depth.
-- ----------------------------------------------------------------------------
WITH route_stats AS (
    SELECT
        Route,
        Factory,
        State_Province,
        COUNT(*)                               AS shipment_count,
        ROUND(AVG(Shipping_Lead_Time_Days), 2) AS avg_lead_time_days
    FROM shipments
    GROUP BY Route, Factory, State_Province
    HAVING COUNT(*) >= 5
)
SELECT
    Route,
    Factory,
    State_Province,
    shipment_count,
    avg_lead_time_days,
    RANK() OVER (ORDER BY avg_lead_time_days ASC)  AS efficiency_rank_fastest,
    RANK() OVER (ORDER BY avg_lead_time_days DESC) AS efficiency_rank_slowest
FROM route_stats
ORDER BY avg_lead_time_days ASC;


-- ----------------------------------------------------------------------------
-- QUERY 5: Business Query — Geographic Bottlenecks
-- Business question: "Which states have BOTH high shipment volume AND
-- above-average lead time — i.e. where should we prioritize logistics
-- investment first?"
-- ----------------------------------------------------------------------------
SELECT
    State_Province,
    COUNT(*)                               AS shipment_count,
    ROUND(AVG(Shipping_Lead_Time_Days), 2) AS avg_lead_time_days
FROM shipments
GROUP BY State_Province
HAVING
    COUNT(*) > (SELECT AVG(state_volume) FROM (
        SELECT COUNT(*) AS state_volume
        FROM shipments
        GROUP BY State_Province
    ) AS volume_by_state)
    AND AVG(Shipping_Lead_Time_Days) > (SELECT AVG(Shipping_Lead_Time_Days) FROM shipments)
ORDER BY avg_lead_time_days DESC;
