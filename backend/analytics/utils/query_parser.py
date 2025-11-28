import re
from typing import Dict, Any, List

import pandas as pd


def _extract_years(text: str) -> List[int]:
    years = set()
    for y in re.findall(r"\b(20[0-4]\d|19\d{2})\b", text):
        years.add(int(y))
    return sorted(years)


def _extract_last_n_years(text: str) -> int:
    match = re.search(r"last\s+(\d+)\s+years?", text)
    if match:
        return int(match.group(1))
    return 0


def _detect_intent_type(text: str) -> str:
    lowercase = text.lower()
    if any(k in lowercase for k in ["compare", "vs", "versus", "between"]):
        return "comparison"
    if any(k in lowercase for k in ["growth", "over the last", "change", "increase", "decrease"]):
        return "growth"
    return "single"


def _extract_areas_from_text(text: str, df: pd.DataFrame) -> List[str]:
    known_areas = sorted(df["Area"].dropna().unique().tolist(), key=len, reverse=True)
    lowercase = text.lower()
    matched = []
    for area in known_areas:
        if re.search(r"\b" + re.escape(area.lower()) + r"\b", lowercase):
            matched.append(area)
    # Fallback: if no explicit match and there is a word that matches exactly an Area
    if not matched:
        words = set(re.findall(r"[a-zA-Z]+(?:\s+[a-zA-Z]+)*", text))
        for area in known_areas:
            if area.lower() in {w.strip().lower() for w in words}:
                matched.append(area)
    # Deduplicate preserving order
    seen = set()
    ordered = []
    for a in matched:
        if a not in seen:
            seen.add(a)
            ordered.append(a)
    return ordered


def parse_query_intent(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    text = query.strip()
    if not text:
        return {
            "intent_type": "invalid",
            "areas": [],
            "years": [],
            "last_n_years": 0,
        }

    intent_type = _detect_intent_type(text)
    years = _extract_years(text)
    last_n = _extract_last_n_years(text)
    areas = _extract_areas_from_text(text, df)

    return {
        "intent_type": intent_type,
        "areas": areas,
        "years": years,
        "last_n_years": last_n,
    }
