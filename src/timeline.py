"""Longitudinal analysis for MindWatch 2.0.

Provides daily, weekly, and monthly emotional-signal tracking, date-range filtering,
recurring themes frequency analysis, period comparisons, and downloadable reports.
Supports both uploaded external text (txt/csv/json) and user's saved database records.
Depression and anxiety are characterized by persistence, so longitudinal trends
provide significantly more meaningful insight than isolated posts.
"""
import csv
import io
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.lang import is_supported
from src.predict import load_model
from src.risk import detect_themes, grade, has_crisis_language


def _parse_date(s: Any) -> date:
    """Parse string or date object into date."""
    if isinstance(s, date):
        return s
    s_str = str(s).strip()[:10]
    y, m, d = map(int, s_str.split("-"))
    return date(y, m, d)


def parse_lines(raw: str) -> List[Tuple[date, str]]:
    posts = []
    for line in raw.splitlines():
        if "|" not in line:
            continue
        d, text = line.split("|", 1)
        try:
            posts.append((_parse_date(d), text.strip()))
        except ValueError:
            continue
    return sorted(posts, key=lambda x: x[0])


def parse_csv(raw: str) -> List[Tuple[date, str]]:
    posts = []
    for row in csv.DictReader(io.StringIO(raw)):
        row = {k.lower().strip(): v for k, v in row.items() if k}
        try:
            posts.append((_parse_date(row["date"]), row["text"].strip()))
        except (KeyError, ValueError, AttributeError):
            continue
    return sorted(posts, key=lambda x: x[0])


def parse_json(raw: str) -> List[Tuple[date, str]]:
    posts = []
    try:
        data = json.loads(raw)
    except ValueError:
        return posts
    for row in data if isinstance(data, list) else []:
        try:
            posts.append((_parse_date(row["date"]), str(row["text"]).strip()))
        except (KeyError, ValueError, TypeError):
            continue
    return sorted(posts, key=lambda x: x[0])


def parse_upload(filename: str, raw: str) -> List[Tuple[date, str]]:
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return parse_csv(raw)
    if name.endswith(".json"):
        return parse_json(raw)
    return parse_lines(raw)


def analyze_timeline(
    posts: List[Tuple[date, str]],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """Comprehensive longitudinal timeline analysis with multi-period metrics."""
    if start_date:
        posts = [p for p in posts if p[0] >= start_date]
    if end_date:
        posts = [p for p in posts if p[0] <= end_date]

    supported = [(d, t) for d, t in posts if t and is_supported(t)]
    skipped = len(posts) - len(supported)

    if not supported:
        return {
            "weeks": [],
            "months": [],
            "days": [],
            "trend": "insufficient data",
            "slope": 0.0,
            "crisis_posts": 0,
            "skipped": skipped,
            "total_supported": 0,
            "themes_frequency": {},
            "signal_frequency": {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRISIS": 0},
            "comparison": None,
            "date_range": {"start": None, "end": None}
        }

    # Batch model prediction
    probs = load_model().predict_proba([t for _, t in supported])[:, 1]

    daily = defaultdict(list)
    weekly = defaultdict(list)
    monthly = defaultdict(list)
    themes_counter = Counter()
    signal_counter = Counter()
    crisis_count = 0

    evaluated_records = []
    for (d, text), p in zip(supported, probs):
        is_crisis = has_crisis_language(text)
        if is_crisis:
            crisis_count += 1
        lvl = grade(p, is_crisis)
        signal_counter[lvl] += 1

        t_themes = detect_themes(text)
        for th in t_themes:
            themes_counter[th] += 1

        entry = {
            "date": d,
            "risk": float(p),
            "level": lvl,
            "crisis": is_crisis,
            "themes": t_themes
        }
        evaluated_records.append(entry)

        # Aggregation keys
        daily[d.isoformat()].append(entry)
        iso = d.isocalendar()
        weekly[(iso[0], iso[1])].append(float(p))
        monthly[(d.year, d.month)].append(float(p))

    # Build weekly timeline
    weeks = [
        {
            "week": f"{y}-W{w:02d}",
            "mean_risk": round(float(np.mean(v)), 3),
            "posts": len(v),
            "peak_risk": round(float(np.max(v)), 3)
        }
        for (y, w), v in sorted(weekly.items())
    ]

    # Build monthly timeline
    months = [
        {
            "month": f"{y}-{m:02d}",
            "mean_risk": round(float(np.mean(v)), 3),
            "posts": len(v),
            "peak_risk": round(float(np.max(v)), 3)
        }
        for (y, m), v in sorted(monthly.items())
    ]

    # Build daily timeline
    days = [
        {
            "date": d_str,
            "mean_risk": round(float(np.mean([e["risk"] for e in items])), 3),
            "posts": len(items),
            "highest_level": max([e["level"] for e in items], key=lambda x: ["LOW", "MODERATE", "HIGH", "CRISIS"].index(x) if x in ["LOW", "MODERATE", "HIGH", "CRISIS"] else -1)
        }
        for d_str, items in sorted(daily.items())
    ]

    # Trend calculation on weekly data (needs >= 3 weeks)
    slope = 0.0
    if len(weeks) >= 3:
        slope = float(np.polyfit(range(len(weeks)), [w["mean_risk"] for w in weeks], 1)[0])

    if len(weeks) < 3:
        trend = "insufficient data (need 3+ weeks)"
    elif slope > 0.04:
        trend = "worsening"
    elif slope < -0.04:
        trend = "improving"
    else:
        trend = "stable"

    # Period comparison (first half vs second half if at least 4 posts exist)
    comparison = None
    if len(evaluated_records) >= 4:
        mid = len(evaluated_records) // 2
        p1 = [e["risk"] for e in evaluated_records[:mid]]
        p2 = [e["risk"] for e in evaluated_records[mid:]]
        mean1 = round(float(np.mean(p1)), 3)
        mean2 = round(float(np.mean(p2)), 3)
        diff = round(mean2 - mean1, 3)

        if diff > 0.05:
            comp_trend = "higher emotional distress in the more recent period"
        elif diff < -0.05:
            comp_trend = "clear improvement in the more recent period"
        else:
            comp_trend = "broadly steady across both periods"

        comparison = {
            "earlier_period_mean": mean1,
            "recent_period_mean": mean2,
            "delta": diff,
            "summary": comp_trend
        }

    return {
        "weeks": weeks,
        "months": months,
        "days": days,
        "trend": trend,
        "slope": round(slope, 3),
        "skipped": skipped,
        "crisis_posts": crisis_count,
        "total_supported": len(supported),
        "themes_frequency": dict(themes_counter.most_common(8)),
        "signal_frequency": {
            "LOW": signal_counter.get("LOW", 0),
            "MODERATE": signal_counter.get("MODERATE", 0),
            "HIGH": signal_counter.get("HIGH", 0),
            "CRISIS": signal_counter.get("CRISIS", 0)
        },
        "comparison": comparison,
        "date_range": {
            "start": supported[0][0].isoformat(),
            "end": supported[-1][0].isoformat()
        }
    }


def generate_timeline_csv(timeline_data: Dict[str, Any]) -> str:
    """Generate CSV report from timeline data."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Period Type", "Period", "Mean Language Risk Score", "Posts Count", "Peak Score"])

    for w in timeline_data.get("weeks", []):
        writer.writerow(["Weekly", w["week"], w["mean_risk"], w["posts"], w.get("peak_risk", "")])
    for m in timeline_data.get("months", []):
        writer.writerow(["Monthly", m["month"], m["mean_risk"], m["posts"], m.get("peak_risk", "")])
    for d in timeline_data.get("days", []):
        writer.writerow(["Daily", d["date"], d["mean_risk"], d["posts"], d.get("highest_level", "")])

    return out.getvalue()
