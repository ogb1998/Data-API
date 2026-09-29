"""Service 1 - parsing & validation. Turns raw CSV text or JSON rows into clean records."""
import csv
import io
from datetime import date

REQUIRED = ("category", "amount", "date")


class ParseError(ValueError):
    """Raised with a list of human-readable problems."""
    def __init__(self, errors):
        super().__init__("; ".join(errors))
        self.errors = errors


def _clean_row(row: dict, line: int, errors: list):
    missing = [c for c in REQUIRED if not str(row.get(c, "")).strip()]
    if missing:
        errors.append(f"row {line}: missing {', '.join(missing)}")
        return None
    try:
        amount = float(str(row["amount"]).replace(",", ""))
    except ValueError:
        errors.append(f"row {line}: amount '{row['amount']}' is not a number")
        return None
    try:
        d = date.fromisoformat(str(row["date"]).strip())
    except ValueError:
        errors.append(f"row {line}: date '{row['date']}' is not YYYY-MM-DD")
        return None
    return {"category": str(row["category"]).strip().lower(), "amount": amount, "date": d.isoformat()}


def parse_rows(rows) -> list[dict]:
    errors, out = [], []
    for i, row in enumerate(rows, start=1):
        rec = _clean_row(row, i, errors)
        if rec:
            out.append(rec)
    if errors:
        raise ParseError(errors)
    if not out:
        raise ParseError(["no rows provided"])
    return out


def parse_csv(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text.strip()))
    if not reader.fieldnames or any(c not in reader.fieldnames for c in REQUIRED):
        raise ParseError([f"CSV must have columns: {', '.join(REQUIRED)}"])
    return parse_rows(reader)
