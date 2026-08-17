# Financial KPI & Profitability Dashboard

> **Status:** Core analysis documented · Tableau dashboard in progress

## Overview

This project analyses Microsoft’s Financial Sample to explain how product mix, customer segment, geography, costs and discounting contribute to profitability.

**Dataset:** [Microsoft Financial Sample](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-financial-download)

## Key KPIs

| Metric | Result |
|---|---:|
| Net sales | $118.73M |
| Profit | $16.89M |
| Profit margin | 14.23% |
| Units sold | 1.13M |
| Discounts | $9.21M |
| Loss-making records | 58 |

## Analysis completed

- Standardised columns, category labels and dates.
- Renamed Sales to Net Sales for clearer interpretation.
- Reconciled Net Sales = Gross Sales − Discounts.
- Reconciled Profit = Net Sales − COGS.
- Created Profit Margin, Discount Rate and Loss-Making fields.
- Analysed monthly, product, country, segment and discount-band performance.

## Tableau dashboard — in progress

Planned fixed-size dashboard: **1366 × 768**

- Monthly net sales and profit trend
- Profit by country and product
- Segment × discount-band margin table
- Loss-making exception count
- Filters and dashboard actions for year, country, segment, product and discount band

## Key insights

- The sample generated **$118.73M net sales** and **$16.89M profit**.
- Overall profit margin was **14.23%**.
- Government was the largest segment, France the strongest country and Paseo the leading product by sales.
- Fifty-eight records were loss-making, showing why revenue and profit should be monitored together.

## Repository roadmap

- [x] Business problem and KPI definition
- [x] Cleaning and reconciliation approach
- [x] SQL analysis documented
- [x] Findings and recommendations documented
- [ ] Add cleaned data and reproducible preparation code
- [ ] Add complete SQL script and analysis outputs
- [ ] Build and publish Tableau dashboard
- [ ] Add dashboard screenshots and Tableau Public link

## Responsible interpretation

This is an official sample dataset, not a live company ledger. The findings demonstrate financial-analysis techniques and should not be presented as results from a real organisation.
