#!/usr/bin/env python3
"""Validate the financial SQLite model and export Tableau-ready CSV files."""

from __future__ import annotations

import argparse
import csv
import math
import os
import sqlite3
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = (
    ("v_project_kpis", ""),
    ("v_monthly_performance", "ORDER BY year, month_number"),
    ("v_product_performance", "ORDER BY product"),
    ("v_country_performance", "ORDER BY country"),
    (
        "v_segment_discount_performance",
        "ORDER BY segment, discount_band",
    ),
    (
        "v_loss_exceptions",
        "ORDER BY date, country, segment, product, discount_band",
    ),
)
EXPECTED_KPIS = {
    "records": 700,
    "units_sold": 1_125_806.0,
    "discounts": 9_205_248.24,
    "net_sales": 118_726_350.26,
    "profit": 16_893_702.26,
    "profit_margin_pct": 14.23,
    "loss_making_records": 58,
}
EXPECTED_EXPORT_COLUMNS = {
    "v_project_kpis": (
        "records",
        "units_sold",
        "discounts",
        "net_sales",
        "profit",
        "profit_margin_pct",
        "loss_making_records",
    ),
    "v_monthly_performance": (
        "year",
        "month_number",
        "month_name",
        "net_sales",
        "profit",
        "profit_margin_pct",
    ),
    "v_product_performance": (
        "product",
        "units_sold",
        "net_sales",
        "profit",
        "profit_margin_pct",
    ),
    "v_country_performance": (
        "country",
        "net_sales",
        "profit",
        "profit_margin_pct",
    ),
    "v_segment_discount_performance": (
        "segment",
        "discount_band",
        "records",
        "net_sales",
        "profit",
        "profit_margin_pct",
    ),
    "v_loss_exceptions": (
        "date",
        "country",
        "segment",
        "product",
        "discount_band",
        "net_sales",
        "profit",
    ),
}

EXPECTED_UNIQUE_GRAINS = {
    "v_monthly_performance": ("year", "month_number"),
    "v_product_performance": ("product",),
    "v_country_performance": ("country",),
    "v_segment_discount_performance": ("segment", "discount_band"),
}

EXPECTED_RECONCILIATIONS = {
    "v_monthly_performance": ("net_sales", "profit"),
    "v_product_performance": ("units_sold", "net_sales", "profit"),
    "v_country_performance": ("net_sales", "profit"),
    "v_segment_discount_performance": ("records", "net_sales", "profit"),
}
AGGREGATE_ROUNDING_TOLERANCE = 0.015


def validate_export_grains(connection: sqlite3.Connection) -> None:
    """Reject empty, null or duplicate rows at each Tableau export grain."""
    project_rows = connection.execute(
        "SELECT COUNT(*) FROM v_project_kpis"
    ).fetchone()[0]
    if project_rows != 1:
        raise ValueError(
            f"v_project_kpis must contain exactly one row; got {project_rows}."
        )

    for view, grain_columns in EXPECTED_UNIQUE_GRAINS.items():
        quoted_columns = ", ".join(f'"{column}"' for column in grain_columns)
        blank_checks = " OR ".join(
            f'"{column}" IS NULL OR TRIM(CAST("{column}" AS TEXT)) = \'\''
            for column in grain_columns
        )
        row_count = connection.execute(
            f'SELECT COUNT(*) FROM "{view}"'
        ).fetchone()[0]
        blank_rows = connection.execute(
            f'SELECT COUNT(*) FROM "{view}" WHERE {blank_checks}'
        ).fetchone()[0]
        duplicate_grains = connection.execute(
            f'SELECT COUNT(*) FROM ('
            f'SELECT {quoted_columns} FROM "{view}" '
            f'GROUP BY {quoted_columns} HAVING COUNT(*) > 1)'
        ).fetchone()[0]
        if row_count == 0 or blank_rows or duplicate_grains:
            raise ValueError(
                f"{view} grain check failed: rows={row_count}, "
                f"blank grain rows={blank_rows}, "
                f"duplicate grains={duplicate_grains}."
            )

    invalid_losses = connection.execute(
        "SELECT COUNT(*) FROM v_loss_exceptions "
        "WHERE profit IS NULL OR profit >= 0"
    ).fetchone()[0]
    if invalid_losses:
        raise ValueError(
            "v_loss_exceptions contains "
            f"{invalid_losses} rows without strictly negative profit."
        )


def validate_database(connection: sqlite3.Connection) -> None:
    """Fail before export if integrity, views or documented KPIs drift."""
    integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"SQLite integrity check failed: {integrity}")

    available = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view'"
        )
    }
    missing = [view for view, _ in EXPORTS if view not in available]
    if missing:
        raise ValueError(f"Missing required views: {', '.join(missing)}")

    for view, expected_columns in EXPECTED_EXPORT_COLUMNS.items():
        cursor = connection.execute(f'SELECT * FROM "{view}" LIMIT 0')
        actual_columns = tuple(column[0] for column in cursor.description)
        if actual_columns != expected_columns:
            raise ValueError(
                f"{view} column contract mismatch: expected "
                f"{expected_columns}, got {actual_columns}"
            )

    validate_export_grains(connection)

    row = connection.execute("SELECT * FROM v_project_kpis").fetchone()
    if row is None:
        raise ValueError("v_project_kpis returned no data.")
    actual = dict(row)

    for key in ("records", "loss_making_records"):
        if actual[key] != EXPECTED_KPIS[key]:
            raise ValueError(
                f"{key} mismatch: expected {EXPECTED_KPIS[key]}, got {actual[key]}"
            )
    for key in (
        "units_sold",
        "discounts",
        "net_sales",
        "profit",
        "profit_margin_pct",
    ):
        if not math.isclose(
            actual[key], EXPECTED_KPIS[key], rel_tol=0, abs_tol=0.005
        ):
            raise ValueError(
                f"{key} mismatch: expected {EXPECTED_KPIS[key]}, got {actual[key]}"
            )

    for view, measures in EXPECTED_RECONCILIATIONS.items():
        select_list = ", ".join(
            f'SUM("{measure}") AS "{measure}"' for measure in measures
        )
        totals = dict(
            connection.execute(
                f'SELECT {select_list} FROM "{view}"'
            ).fetchone()
        )
        failures = []
        for measure in measures:
            expected = EXPECTED_KPIS[measure]
            actual_total = totals[measure]
            if measure == "records":
                if actual_total != expected:
                    failures.append(
                        f"{measure}: expected {expected}, got {actual_total}"
                    )
            elif not math.isclose(
                actual_total,
                expected,
                rel_tol=0,
                abs_tol=AGGREGATE_ROUNDING_TOLERANCE,
            ):
                failures.append(
                    f"{measure}: expected {expected}, got {actual_total}"
                )
        if failures:
            raise ValueError(
                f"{view} aggregate reconciliation failed:\n- "
                + "\n- ".join(failures)
            )

    loss_rows = connection.execute(
        "SELECT COUNT(*) FROM v_loss_exceptions"
    ).fetchone()[0]
    if loss_rows != EXPECTED_KPIS["loss_making_records"]:
        raise ValueError(
            "v_loss_exceptions mismatch: "
            f"expected {EXPECTED_KPIS['loss_making_records']}, got {loss_rows}"
        )


def export_view(
    connection: sqlite3.Connection,
    view: str,
    order_by: str,
    destination: Path,
) -> int:
    cursor = connection.execute(f'SELECT * FROM "{view}" {order_by}')
    headers = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    with destination.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate project.db and export Tableau-ready CSV files."
    )
    parser.add_argument(
        "--database",
        default=str(ROOT / "project.db"),
        help="SQLite database path (default: project.db in the repository root)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "tableau" / "exports"),
        help="CSV destination (default: tableau/exports)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate the database and required views without writing CSV files.",
    )
    args = parser.parse_args()

    database = Path(args.database).resolve()
    output_dir = Path(args.output_dir).resolve()
    if not database.is_file():
        raise FileNotFoundError(
            f"{database} does not exist. Run scripts/build_database.py first."
        )

    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        validate_database(connection)

        if args.check_only:
            print(
                "Validation passed: SQLite integrity, six required views, "
                "six export column and grain contracts, four aggregate "
                "reconciliations, seven KPIs and 58 loss records."
            )
            return

        output_dir.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="tableau-export-", dir=output_dir.parent
        ) as temporary:
            temporary_dir = Path(temporary)
            exported: list[tuple[str, int]] = []
            for view, order_by in EXPORTS:
                filename = f"{view.removeprefix('v_')}.csv"
                row_count = export_view(
                    connection, view, order_by, temporary_dir / filename
                )
                exported.append((filename, row_count))

            output_dir.mkdir(parents=True, exist_ok=True)
            for filename, _ in exported:
                os.replace(temporary_dir / filename, output_dir / filename)

    for filename, row_count in exported:
        print(f"Exported {row_count:,} rows to {output_dir / filename}")


if __name__ == "__main__":
    main()
