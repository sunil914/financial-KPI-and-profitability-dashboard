DROP VIEW IF EXISTS v_project_kpis;
DROP VIEW IF EXISTS v_monthly_performance;
DROP VIEW IF EXISTS v_product_performance;
DROP VIEW IF EXISTS v_country_performance;
DROP VIEW IF EXISTS v_segment_discount_performance;
DROP VIEW IF EXISTS v_loss_exceptions;

CREATE VIEW v_project_kpis AS
SELECT
    COUNT(*) AS records,
    ROUND(SUM(units_sold), 2) AS units_sold,
    ROUND(SUM(discounts), 2) AS discounts,
    ROUND(SUM(net_sales), 2) AS net_sales,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100.0 * SUM(profit) / SUM(net_sales), 2) AS profit_margin_pct,
    SUM(loss_making_flag) AS loss_making_records
FROM financials;

CREATE VIEW v_monthly_performance AS
SELECT
    year,
    month_number,
    month_name,
    ROUND(SUM(net_sales), 2) AS net_sales,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100.0 * SUM(profit) / SUM(net_sales), 2) AS profit_margin_pct
FROM financials
GROUP BY year, month_number, month_name;

CREATE VIEW v_product_performance AS
SELECT
    product,
    ROUND(SUM(units_sold), 2) AS units_sold,
    ROUND(SUM(net_sales), 2) AS net_sales,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100.0 * SUM(profit) / SUM(net_sales), 2) AS profit_margin_pct
FROM financials
GROUP BY product;

CREATE VIEW v_country_performance AS
SELECT
    country,
    ROUND(SUM(net_sales), 2) AS net_sales,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100.0 * SUM(profit) / SUM(net_sales), 2) AS profit_margin_pct
FROM financials
GROUP BY country;

CREATE VIEW v_segment_discount_performance AS
SELECT
    segment,
    discount_band,
    COUNT(*) AS records,
    ROUND(SUM(net_sales), 2) AS net_sales,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(100.0 * SUM(profit) / SUM(net_sales), 2) AS profit_margin_pct
FROM financials
GROUP BY segment, discount_band;

CREATE VIEW v_loss_exceptions AS
SELECT
    date, country, segment, product, discount_band,
    ROUND(net_sales, 2) AS net_sales,
    ROUND(profit, 2) AS profit
FROM financials
WHERE loss_making_flag = 1;

