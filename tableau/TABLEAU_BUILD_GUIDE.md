# Tableau Dashboard Build Guide

> **Project status:** Build specification only. The Tableau dashboard is not yet complete or published.

This guide turns the documented financial-analysis results into a reproducible Tableau dashboard. It is designed to prevent KPI drift, misleading comparisons and premature publication.

## 1. Dashboard objective

Create a fixed-size executive dashboard that answers five questions:

1. What are total net sales, profit, profit margin, units sold and discounts?
2. How do net sales and profit change over time?
3. Which countries and products contribute the most profit?
4. How does discounting relate to margin across customer segments?
5. Where are the loss-making product-market exceptions?

**Canvas:** 1366 × 768 pixels  
**Primary audience:** finance and commercial decision-makers  
**Source:** [Microsoft Financial Sample](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-financial-download)

## 2. Required fields

Confirm these fields are available before building worksheets:

| Business field | Expected purpose |
|---|---|
| Date | Monthly performance trend |
| Year | Dashboard filter |
| Segment | Customer-segment comparison |
| Country | Geographic performance |
| Product | Product performance |
| Discount Band | Discount and margin comparison |
| Units Sold | Volume KPI |
| Gross Sales | Pre-discount sales |
| Discounts | Discount KPI |
| Sales / Net Sales | Post-discount sales |
| COGS | Cost of goods sold |
| Profit | Profit KPI |

Rename the source field **Sales** to **Net Sales** in Tableau so the workbook matches the project documentation.

## 3. Validation gate

Before formatting any chart, reproduce the documented totals:

| KPI | Expected displayed value |
|---|---:|
| Net Sales | $118.73M |
| Profit | $16.89M |
| Profit Margin | 14.23% |
| Units Sold | 1.13M |
| Discounts | $9.21M |
| Loss-making records | 58 |

These are rounded display values. Preserve full precision in Tableau and round only through number formatting. If a total does not reconcile, stop and check field types, filters, duplicate rows and aggregation choices before continuing.

Also verify:

- **Net Sales = Gross Sales − Discounts**
- **Profit = Net Sales − COGS**
- Date is recognised as a date, not text.
- Currency and unit fields are numeric.
- No dashboard filter changes the opening KPI values unexpectedly.

## 4. Calculated fields

### Profit Margin

```tableau
IF SUM([Net Sales]) = 0 THEN
    NULL
ELSE
    SUM([Profit]) / SUM([Net Sales])
END
```

Format as a percentage with two decimal places.

### Discount Rate

```tableau
IF SUM([Gross Sales]) = 0 THEN
    NULL
ELSE
    SUM([Discounts]) / SUM([Gross Sales])
END
```

Format as a percentage with two decimal places.

### Loss-Making Record

```tableau
IF [Profit] < 0 THEN 1 ELSE 0 END
```

Use `SUM([Loss-Making Record])` for the exception count. Keeping this calculation at row level ensures the count represents records rather than aggregated groups.

### Year Month

```tableau
DATETRUNC('month', [Date])
```

Display as `MMM YYYY` and keep the underlying value continuous for chronological sorting.

## 5. Worksheet specifications

Use these worksheet names so the workbook remains easy to audit.

### KPI — Net Sales

- Marks: Text
- Measure: `SUM([Net Sales])`
- Format: Currency, millions, two decimals
- Expected display: **$118.73M**

Repeat the same structure for:

- `KPI — Profit`
- `KPI — Profit Margin`
- `KPI — Units Sold`
- `KPI — Discounts`

### Trend — Monthly Net Sales

- Columns: `Year Month` continuous
- Rows: `SUM([Net Sales])`
- Marks: Line
- Tooltip: Month, Net Sales, Profit and Profit Margin
- Show complete months and use chronological order.

### Trend — Monthly Profit

Build this as a separate aligned panel under the net-sales trend. Separate panels avoid a misleading dual-axis comparison between measures with different scales.

- Columns: `Year Month` continuous
- Rows: `SUM([Profit])`
- Marks: Line
- Add a zero reference line.
- Use a warning colour only where monthly profit is negative.

### Performance — Country

- Rows: `Country`
- Columns: `SUM([Profit])`
- Marks: Horizontal bar
- Sort: Descending by profit
- Tooltip: Country, Net Sales, Profit, Profit Margin and Discounts
- Add a zero reference line so losses are visible.

### Performance — Product

- Rows: `Product`
- Columns: `SUM([Profit])`
- Marks: Horizontal bar
- Sort: Descending by profit
- Tooltip: Product, Net Sales, Profit, Profit Margin and Units Sold
- Do not rank only by revenue; preserve profit context.

### Matrix — Segment × Discount Band

- Rows: `Segment`
- Columns: `Discount Band`
- Marks: Square
- Colour: `Profit Margin`
- Label: `Profit Margin`
- Tooltip: Segment, Discount Band, Net Sales, Profit, Margin and Discounts
- Use a diverging palette centred at 0%.

### Exceptions — Loss-Making Records

Filter to `Loss-Making Record = 1`.

Include:

- Country
- Segment
- Product
- Discount Band
- Net Sales
- Discounts
- Profit
- Profit Margin

Sort by Profit ascending so the largest losses appear first. This sheet supports investigation; it must not imply that discounting alone caused a loss.

## 6. Dashboard layout

Recommended fixed layout:

1. **Header:** title, short purpose statement and last-updated note
2. **Top row:** five KPI cards
3. **Left centre:** monthly net-sales and profit panels
4. **Right centre:** country and product profit views
5. **Bottom left:** segment × discount-band margin matrix
6. **Bottom right:** loss-making exception summary
7. **Filter rail:** Year, Country, Segment, Product and Discount Band

Keep padding and spacing consistent. Avoid decorative elements that do not support interpretation.

## 7. Interactivity

Configure filters to apply to all relevant worksheets using the same data source:

- Year
- Country
- Segment
- Product
- Discount Band

Add dashboard actions:

- Selecting a country filters product and exception views.
- Selecting a segment filters the margin matrix and exception view.
- Clearing a selection restores the complete dashboard.
- Hover tooltips provide full values without overcrowding labels.

After configuring actions, repeat the KPI reconciliation with all filters cleared.

## 8. Formatting and accessibility

- Use one neutral colour for positive performance and one restrained warning colour for losses.
- Do not rely on red and green alone; include labels or signs.
- Keep body text at least 11–12 px and KPI values clearly larger.
- Use descriptive worksheet titles rather than technical field names.
- Format currency consistently across cards, axes and tooltips.
- Include visible zero reference lines wherever negative profit can occur.
- Check that every chart remains readable at the fixed dashboard size.

## 9. Responsible interpretation

The Microsoft Financial Sample is demonstration data, not a live company ledger. The dashboard should describe patterns without claiming causal effects.

In particular:

- High discounts may coincide with lower margins, but the dashboard does not prove that discounting caused every loss.
- Compare revenue, profit and margin together.
- Investigate loss-making combinations before making pricing recommendations.
- Do not present sample results as the performance of a real organisation.

## 10. Publishing checklist

Before publishing to Tableau Public:

- [ ] Opening KPIs reconcile to the documented totals
- [ ] Net Sales and Profit identities reconcile
- [ ] All filters and actions work as intended
- [ ] Months are chronologically sorted
- [ ] Negative profit is visible and clearly labelled
- [ ] Tooltips use consistent units and currency
- [ ] Dashboard fits 1366 × 768 without clipping
- [ ] Titles and captions explain what each view measures
- [ ] Workbook is labelled as a sample-data project
- [ ] No view claims causality
- [ ] Tableau Public link is added to the README
- [ ] Final dashboard screenshot is added under `images/`

## 11. Next repository assets

The next implementation phase should add:

```text
data/financial_clean.csv
sql/analysis.sql
analysis/kpis.json
tableau/monthly_performance.csv
tableau/country_performance.csv
tableau/product_performance.csv
tableau/segment_performance.csv
tableau/discount_band_performance.csv
images/dashboard.png
```

Do not mark the dashboard complete until the workbook is published, the link works and the displayed KPIs pass the reconciliation gate.
