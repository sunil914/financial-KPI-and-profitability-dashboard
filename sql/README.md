# SQLite analysis

Run `python3 scripts/build_database.py` to load and validate the committed 700-row Microsoft Financial Sample, then create `project.db` and its analysis views.

The views cover project KPIs, monthly trends, product and country results, segment × discount-band margins, and loss-making exceptions. Expected reconciliation: **$118,726,350.26 net sales**, **$16,893,702.26 profit**, **14.23% profit margin** and **58 loss-making records**.

The generated database can be opened in DB Browser for SQLite and is ignored by Git because it is reproducible from the committed CSV.

