"""Service 2 - business logic. Pure functions over parsed records (no I/O)."""
from collections import defaultdict
from statistics import mean, median


def totals_by_category(records):
    out = defaultdict(float)
    for r in records:
        out[r["category"]] += r["amount"]
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def monthly_totals(records):
    out = defaultdict(float)
    for r in records:
        out[r["date"][:7]] += r["amount"]
    return dict(sorted(out.items()))


def summary_stats(records):
    amounts = [r["amount"] for r in records]
    if not amounts:
        return {"count": 0, "total": 0.0, "mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    return {"count": len(amounts), "total": round(sum(amounts), 2), "mean": round(mean(amounts), 2),
            "median": round(median(amounts), 2), "min": min(amounts), "max": max(amounts)}


def flag_outliers(records, k=3.0):
    """Flag amounts more than k * MAD (scaled) from the median."""
    amounts = [r["amount"] for r in records]
    if len(amounts) < 5:
        return []
    med = median(amounts)
    mad = median(abs(a - med) for a in amounts) * 1.4826
    if mad == 0:
        return []
    return [r for r in records if abs(r["amount"] - med) / mad > k]
