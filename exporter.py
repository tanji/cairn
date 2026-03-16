"""CSV export for completed tasks."""

import csv
from pathlib import Path


def export_history_to_csv(rows, filepath: str) -> int:
    """Write completed task rows to a CSV file. Returns number of rows written."""
    fields = ["id", "name", "project", "deadline", "created_at", "completed_at"]
    path = Path(filepath)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fields})
            count += 1
    return count
