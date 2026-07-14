#!/usr/bin/env python3
"""Parse GA4 multi-section CSV exports into a compact auditable summary."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def number(value: str):
    cleaned = value.strip().replace(",", "").replace("%", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_sections(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    sections: list[dict] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line or line.startswith("#"):
            index += 1
            continue
        header = next(csv.reader([lines[index]]))
        rows: list[list[str]] = []
        index += 1
        while index < len(lines):
            candidate = lines[index]
            if not candidate.strip() or candidate.lstrip().startswith("#"):
                break
            row = next(csv.reader([candidate]))
            if len(row) == len(header):
                rows.append(row)
            index += 1
        sections.append({"header": header, "rows": rows})
    return sections


def summarize(path: Path) -> dict:
    output = {"file": str(path), "sections": []}
    for section in parse_sections(path):
        header = section["header"]
        rows = section["rows"]
        row_dicts = [dict(zip(header, row)) for row in rows]
        metric = header[-1]
        ranked = sorted(
            row_dicts,
            key=lambda row: number(row.get(metric, "")) if number(row.get(metric, "")) is not None else -1,
            reverse=True,
        )
        output["sections"].append(
            {
                "name": header[0],
                "header": header,
                "row_count": len(rows),
                "top_rows": ranked[:15],
            }
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = [summarize(path) for path in args.files]
    payload = json.dumps(result, indent=2)
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
