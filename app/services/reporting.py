"""Service 3 - reporting. Assembles logic outputs into a JSON-ready report."""
from . import logic


def build_report(session_id: str, records: list[dict]) -> dict:
    return {
        "session_id": session_id,
        "summary": logic.summary_stats(records),
        "by_category": logic.totals_by_category(records),
        "by_month": logic.monthly_totals(records),
        "outliers": logic.flag_outliers(records),
    }
