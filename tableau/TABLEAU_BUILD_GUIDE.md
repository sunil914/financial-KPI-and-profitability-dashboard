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

## 2. Validated Tableau sources

Run `python3 scripts/export_tableau_data.py` and connect each worksheet to the export that matches its analytical grain:

| Export | Grain | Intended use |
|---|---|---|
| `project_kpis.csv` | One project-total row | Five KPI cards and the loss-record count |
| `monthly_performance.csv` | Year × month | Net-sales and profit trends |
| `product_performance.csv` | Product | Product profitability |
| `country_performance.csv` | Country | Country profitability |
| `segment_discount_performance.csv` | Segment × discount band | Margin matrix |
| `loss_exceptions.csv` | Individual loss-making record | Exception table |

Treat these as independent, worksheet-specific sources. **Do not join or union the exports:** their grains differ, so combining them would multiply or mix already-aggregated values. Keep `project.db` and the SQL views as reconciliation evidence rather than extra tables in the Tableau model.

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

- `project_kpis.csv` contains exactly one row and the loss count is 58.
- `loss_exceptions.csv` contains exactly 58 rows.
- Each worksheet uses only its documented export and does not duplicate rows through joins.
- Currency, unit and percentage fields are numeric.
- Year and month number sort the monthly export chronologically.
- Clearing a worksheet filter or action restores that source's opening values.

The row-level identities **Net Sales = Gross Sales − Discounts** and **Profit = Net Sales − COGS** are enforced upstream by the preparation workflow. The exported aggregate files do not contain every component needed to recalculate those identities row by row, so verify them through the validated database build rather than inventing Tableau fields.

## 4. Calculated fields

The exports already contain `profit_margin_pct`. Display it as a percentage value without applying an additional ×100 conversion. Never average group margins to create a total.

If a view combines multiple rows from one aggregate source, calculate the weighted margin from its additive measures:

```tableau
IF SUM([Net Sales]) = 0 THEN
    NULL
ELSE
    SUM([Profit]) / SUM([Net Sales])
END
```

Format this result as a percentage with two decimal places.

Create a real monthly date from the fields that actually exist in `monthly_performance.csv`:

```tableau
MAKEDATE(INT([Year]), INT([Month Number]), 1)
```

Display it as `MMM YYYY` and keep it continuous for chronological sorting. The loss-exception source is already restricted to the 58 validated loss-making records, so do not recreate or sum a row-level loss flag in that worksheet.

## 5. Worksheet specifications

Use these worksheet names and sources so the workbook remains easy to audit.

### KPI — Net Sales

- Source: `project_kpis.csv`
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

- Source: `monthly_performance.csv`
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

- Source: `country_performance.csv`
- Rows: `Country`
- Columns: `SUM([Profit])`
- Marks: Horizontal bar
- Sort: Descending by profit
- Tooltip: Country, Net Sales, Profit and Profit Margin
- Add a zero reference line so losses are visible.

### Performance — Product

- Source: `product_performance.csv`
- Rows: `Product`
- Columns: `SUM([Profit])`
- Marks: Horizontal bar
- Sort: Descending by profit
- Tooltip: Product, Net Sales, Profit, Profit Margin and Units Sold
- Do not rank only by revenue; preserve profit context.

### Matrix — Segment × Discount Band

- Source: `segment_discount_performance.csv`
- Rows: `Segment`
- Columns: `Discount Band`
- Marks: Square
- Colour: `Profit Margin`
- Label: `Profit Margin`
- Tooltip: Segment, Discount Band, Records, Net Sales, Profit and Profit Margin
- Use a diverging palette centred at 0%.

### Exceptions — Loss-Making Records

- Source: `loss_exceptions.csv`
- Expected rows: **58**

The export is already filtered to loss-making records; do not add a second loss flag or claim that this exception-only source represents the full portfolio.

Include:

- Date
- Country
- Segment
- Product
- Discount Band
- Net Sales
- Profit

The loss export does not contain Discounts, COGS or a precomputed Profit Margin. Do not add those fields unless the exporter and validation contract are deliberately extended.

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

The six exports are independent aggregate sources, so a dimension may filter only worksheets whose source contains that field:

- Year and month belong to the monthly trend source.
- Country belongs to the country and loss-exception sources.
- Product belongs to the product and loss-exception sources.
- Segment and discount band belong to the matrix and loss-exception sources.
- Project KPI cards are fixed opening totals and must not appear to respond to unsupported cross-source filters.

Use worksheet highlighting or navigation where a dimension is absent from another source. Do not configure a country selection to imply that it can recalculate the product export, or a segment selection to imply that it can recalculate the country export. A fully cross-filterable dashboard would require a separate validated row-level source and is outside the current six-export model.

After configuring supported actions, clear every selection and repeat the opening reconciliation.

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

- [ ] Each worksheet uses the documented export and no exports are joined or unioned
- [ ] Opening KPIs reconcile to the documented totals
- [ ] Net Sales and Profit identities reconcile
- [ ] Filters and actions affect only sources that contain the selected dimension
- [ ] No control visually promises unsupported cross-source recalculation
- [ ] Months are chronologically sorted
- [ ] Negative profit is visible and clearly labelled
- [ ] Tooltips use consistent units and currency
- [ ] Dashboard fits 1366 × 768 without clipping
- [ ] Titles and captions explain what each view measures
- [ ] Workbook is labelled as a sample-data project
- [ ] No view claims causality
- [ ] Tableau Public link is added to the README
- [ ] Final dashboard screenshot is added under `images/`

## 11. Remaining publication evidence

The validated clean data, SQL analysis and six Tableau exports are already reproducible. The remaining evidence is:

- the Tableau workbook;
- a final dashboard screenshot under `images/`;
- a working Tableau Public URL; and
- a completed reconciliation, interaction and accessibility review.

Do not mark the dashboard complete until the workbook is published, the link works and the displayed KPIs pass the reconciliation gate.
