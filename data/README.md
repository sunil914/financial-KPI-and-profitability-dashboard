# Data

## File

`financial_sample_clean.csv` contains 700 financial sample records and 19 columns.

## Source

- Dataset: Microsoft Financial Sample workbook
- URL: https://learn.microsoft.com/en-us/power-bi/create-reports/sample-financial-download
- Publisher: Microsoft

## Preparation

Column whitespace was removed, `Sales` was renamed `Net Sales`, blank discount bands were labelled `None`, and dates use `YYYY-MM-DD`. `Profit Margin`, `Discount Rate` and `Loss Making Flag` were added using the documented reconciliation rules.

## Validation

| Check | Result |
|---|---:|
| Records | 700 |
| Net sales | $118,726,350.26 |
| Profit | $16,893,702.26 |
| Profit margin | 14.23% |
| Units sold | 1,125,806 |
| Discounts | $9,205,248.24 |
| Loss-making records | 58 |

SHA-256: `ce8b6426b8fb475e850d7edb697caaa5b6dfa97ce6d12c1447ace4e966b1ddf0`
