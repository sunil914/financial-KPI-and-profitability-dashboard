DROP TABLE IF EXISTS financials;

CREATE TABLE financials (
    segment TEXT, country TEXT, product TEXT, discount_band TEXT,
    units_sold REAL, manufacturing_price REAL, sale_price REAL,
    gross_sales REAL, discounts REAL, net_sales REAL, cogs REAL,
    profit REAL, date TEXT, month_number INTEGER, month_name TEXT,
    year INTEGER, profit_margin REAL, discount_rate REAL,
    loss_making_flag INTEGER
);

CREATE INDEX idx_financial_date ON financials (date);
CREATE INDEX idx_financial_product ON financials (product);

