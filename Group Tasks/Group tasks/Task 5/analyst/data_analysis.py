import pandas as pd


def analyse_table(rows: list[dict]) -> dict:
    """For every metric: count, average, highest, lowest and a ranking (best value first)."""
    if not rows:
        return {}

    df = pd.DataFrame(rows)
    result = {}
    for metric, group in df.groupby("metric"):
        ranked = group.sort_values("value", ascending=False)
        top = ranked.iloc[0]
        low = ranked.iloc[-1]
        result[metric] = {
            "count": len(group),
            "average": round(float(group["value"].mean()), 3),
            "highest": {"item": top["item"], "value": float(top["value"])},
            "lowest": {"item": low["item"], "value": float(low["value"])},
            "ranking": [{"item": r["item"], "value": float(r["value"])} for _, r in ranked.iterrows()],
        }
    return result
