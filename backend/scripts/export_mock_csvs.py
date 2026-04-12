"""Regenerate mock CSVs from app.mock_data.lessons_data (run from backend/: python scripts/export_mock_csvs.py)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.mock_data.lessons_data import _RAW, instructor_name_to_id  # noqa: E402

OUT = ROOT / "app" / "mock_data"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    mapping = instructor_name_to_id()
    with (OUT / "instructors.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instructor_user_id", "full_name"])
        for name, uid in sorted(mapping.items(), key=lambda x: x[1]):
            w.writerow([uid, name])
    with (OUT / "lessons.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "lesson_id",
                "course_title",
                "subject_description",
                "course_number",
                "crn",
                "instructor",
                "available_seats",
                "lessons_per_week",
                "instructor_user_id",
            ]
        )
        for row in _RAW:
            w.writerow([*row, mapping[row[5]]])
    print(f"Wrote {OUT / 'instructors.csv'} and {OUT / 'lessons.csv'}")


if __name__ == "__main__":
    main()
