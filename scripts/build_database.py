#!/usr/bin/env python3
"""Build the project SQLite database from the committed cleaned CSV."""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = (
    ("data/online_retail_clean.csv.gz.part-*", "customer_sales", 397_884),
    ("data/bank_marketing_clean.csv.gz", "campaign_contacts", 41_188),
    ("data/financial_sample_clean.csv", "financials", 700),
    ("data/hr_attrition_clean.csv", "hr_employees", 1_470),
    ("data/ecommerce_funnel_clean.csv.gz.part-*", "ecommerce_sessions", 120_000),
)


def sql_name(value: str) -> str:
    value = value.strip().replace("&", " and ")
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    return value.strip("_").lower()


def detect_project() -> tuple[list[Path], str, int]:
    for pattern, table, expected_rows in CONFIGS:
        matches = sorted(ROOT.glob(pattern))
        if matches:
            return matches, table, expected_rows
    raise FileNotFoundError("No supported project dataset was found under data/.")


@contextmanager
def csv_text_stream(files: list[Path]):
    if len(files) > 1:
        compressed = io.BytesIO(b"".join(path.read_bytes() for path in files))
        binary = gzip.GzipFile(fileobj=compressed, mode="rb")
        text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
    elif files[0].suffix == ".gz":
        text = gzip.open(files[0], mode="rt", encoding="utf-8", newline="")
    else:
        text = files[0].open(mode="r", encoding="utf-8", newline="")
    try:
        yield text
    finally:
        text.close()


def insert_csv(connection: sqlite3.Connection, table: str, files: list[Path]) -> int:
    with csv_text_stream(files) as stream:
        reader = csv.reader(stream)
        source_headers = next(reader)
        headers = [sql_name(header) for header in source_headers]
        if len(headers) != len(set(headers)):
            raise ValueError("Column normalisation produced duplicate names.")
        columns = ", ".join(f'"{column}"' for column in headers)
        placeholders = ", ".join("?" for _ in headers)
        statement = f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders})'

        inserted = 0
        batch: list[list[str | None]] = []
        for row in reader:
            batch.append([value if value != "" else None for value in row])
            if len(batch) == 5_000:
                connection.executemany(statement, batch)
                inserted += len(batch)
                batch.clear()
        if batch:
            connection.executemany(statement, batch)
            inserted += len(batch)
        return inserted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        default=str(ROOT / "project.db"),
        help="SQLite database path (default: project.db in the repository root)",
    )
    args = parser.parse_args()

    files, table, expected_rows = detect_project()
    database = Path(args.database).resolve()
    schema = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    analysis = (ROOT / "sql" / "analysis.sql").read_text(encoding="utf-8")

    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)
        inserted = insert_csv(connection, table, files)
        if inserted != expected_rows:
            raise ValueError(f"Expected {expected_rows:,} rows, loaded {inserted:,}.")
        connection.executescript(analysis)
        integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {integrity}")
        columns = [column[0] for column in connection.execute("SELECT * FROM v_project_kpis").description]
        values = connection.execute("SELECT * FROM v_project_kpis").fetchone()

    print(f"Built {database} with {inserted:,} rows in {table}.")
    for column, value in zip(columns, values):
        print(f"{column}: {value}")


if __name__ == "__main__":
    main()
