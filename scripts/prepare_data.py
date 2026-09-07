#!/usr/bin/env python3
"""Rebuild and validate the cleaned Microsoft Financial Sample."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - CLI dependency guidance
    raise SystemExit(
        "This script requires pandas and openpyxl: "
        "python3 -m pip install pandas openpyxl"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COLUMNS = [
    "Segment",
    "Country",
    "Product",
    "Discount Band",
    "Units Sold",
    "Manufacturing Price",
    "Sale Price",
    "Gross Sales",
    "Discounts",
    "Sales",
    "COGS",
    "Profit",
    "Date",
    "Month Number",
    "Month Name",
    "Year",
]
OUTPUT_COLUMNS = [
    *SOURCE_COLUMNS[:9],
    "Net Sales",
    *SOURCE_COLUMNS[10:],
    "Profit Margin",
    "Discount Rate",
    "Loss Making Flag",
]
EXPECTED_ROWS = 700
EXPECTED_NET_SALES = 118_726_350.26
EXPECTED_PROFIT = 16_893_702.26
EXPECTED_MARGIN_PCT = 14.23
EXPECTED_UNITS = 1_125_806.0
EXPECTED_DISCOUNTS = 9_205_248.24
EXPECTED_LOSSES = 58
EXPECTED_SHA256 = "ce8b6426b8fb475e850d7edb697caaa5b6dfa97ce6d12c1447ace4e966b1ddf0"


def prepare(source: Path) -> pd.DataFrame:
    """Standardise fields and derive the documented financial measures."""
    frame = pd.read_excel(source, engine="openpyxl")
    frame.columns = [str(column).strip() for column in frame.columns]
    missing = [column for column in SOURCE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Source workbook is missing columns: {', '.join(missing)}")

    frame = frame[SOURCE_COLUMNS].copy()
    frame["Discount Band"] = frame["Discount Band"].fillna("None").replace("", "None")
    frame = frame.rename(columns={"Sales": "Net Sales"})
    frame["Date"] = pd.to_datetime(frame["Date"]).dt.strftime("%Y-%m-%d")

    numeric_columns = [
        "Units Sold",
        "Manufacturing Price",
        "Sale Price",
        "Gross Sales",
        "Discounts",
        "Net Sales",
        "COGS",
        "Profit",
        "Month Number",
        "Year",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    frame["Profit Margin"] = frame["Profit"] / frame["Net Sales"]
    frame["Discount Rate"] = frame["Discounts"] / frame["Gross Sales"]
    frame["Loss Making Flag"] = frame["Profit"].lt(0).astype(int)
    return frame[OUTPUT_COLUMNS]


def validate(frame: pd.DataFrame) -> None:
    """Fail when row identities or documented aggregate KPIs do not reconcile."""
    sales_difference = (
        frame["Gross Sales"] - frame["Discounts"] - frame["Net Sales"]
    ).abs().max()
    profit_difference = (
        frame["Net Sales"] - frame["COGS"] - frame["Profit"]
    ).abs().max()
    if sales_difference > 0.01:
        raise ValueError(
            f"Net Sales identity failed; maximum difference is {sales_difference:.2f}."
        )
    if profit_difference > 0.01:
        raise ValueError(
            f"Profit identity failed; maximum difference is {profit_difference:.2f}."
        )

    net_sales = frame["Net Sales"].sum()
    checks = {
        "records": (len(frame), EXPECTED_ROWS),
        "net sales": (round(net_sales, 2), EXPECTED_NET_SALES),
        "profit": (round(frame["Profit"].sum(), 2), EXPECTED_PROFIT),
        "profit margin": (
            round(100 * frame["Profit"].sum() / net_sales, 2),
            EXPECTED_MARGIN_PCT,
        ),
        "units sold": (round(frame["Units Sold"].sum(), 2), EXPECTED_UNITS),
        "discounts": (round(frame["Discounts"].sum(), 2), EXPECTED_DISCOUNTS),
        "loss-making records": (
            int(frame["Loss Making Flag"].sum()),
            EXPECTED_LOSSES,
        ),
    }
    failures = [
        f"{name}: expected {expected!r}, got {actual!r}"
        for name, (actual, expected) in checks.items()
        if actual != expected
    ]
    if failures:
        raise ValueError("Validation failed:\n- " + "\n- ".join(failures))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare Microsoft's Financial Sample for this project."
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=ROOT / "data" / "Financial Sample.xlsx",
        help="source workbook (default: data/Financial Sample.xlsx)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "financial_sample_clean.csv",
        help="clean CSV destination (default: data/financial_sample_clean.csv)",
    )
    args = parser.parse_args()

    frame = prepare(args.source.resolve())
    validate(frame)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    frame.to_csv(temporary, index=False, lineterminator="\n")
    digest = sha256(temporary)
    if digest != EXPECTED_SHA256:
        temporary.unlink(missing_ok=True)
        raise ValueError(
            f"Output SHA-256 mismatch: expected {EXPECTED_SHA256}, got {digest}"
        )
    os.replace(temporary, output)

    print(f"Prepared {len(frame):,} financial records in {output}.")
    print(f"Net sales: ${frame['Net Sales'].sum():,.2f}")
    print(f"Profit: ${frame['Profit'].sum():,.2f}")
    print(f"Loss-making records: {frame['Loss Making Flag'].sum():,}")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
