import os
import json
from typing import Dict, Any

from django.conf import settings

try:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception:
    client = None  # graceful fallback if openai not installed or misconfigured


class AISummarizer:
    """
    Generates AI-written summary using OpenAI GPT-4o-mini.
    Falls back to rule-based summary if API call fails.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    def summarize(self, query: str, intent: Dict[str, Any], insights: Dict[str, Any]) -> str:
        # If OpenAI key exists, try LLM
        if self.api_key and client:
            try:
              return self._openai_summary(query, intent, insights)
            except Exception as e:
              print("⚠️ OpenAI Error:", e)
              return self._rule_based_summary(query, intent, insights)

        # Otherwise fallback
        return self._rule_based_summary(query, intent, insights)

    def _openai_summary(self, query: str, intent: Dict[str, Any], insights: Dict[str, Any]) -> str:
        structured_json = {
            "query": query,
            "intent": intent,
            "insights": insights,
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional real estate analyst. "
                    "Generate a clear, useful, 100-180 word explanation. "
                    "Explain trends, demand, price growth, risks, and recommendations."
                )
            },
            {
                "role": "user",
                "content": (
                    "Analyze the following structured data and write an expert summary:\n\n"
                    f"{json.dumps(structured_json, indent=2)}"
                )
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=280,
            temperature=0.5,
        )

        return response.choices[0].message.content.strip()

    def _rule_based_summary(self, query: str, intent: Dict[str, Any], insights: Dict[str, Any]) -> str:
        """Backup text generation if OpenAI unavailable."""
        areas = insights.get("areas", [])
        years = insights.get("years", [])
        trend = insights.get("price_trend_direction", {})
        demand = insights.get("demand_trend_direction", {})
        growth = insights.get("price_growth_pct", {})

        if not areas:
            return "No relevant locality found — try another location."

        summary = [f"Analysis for {', '.join(areas)}."]

        if years:
            summary.append(f"Data covers {min(years)} to {max(years)}.")

        for area in areas:
            t = trend.get(area, "stable")
            d = demand.get(area, "stable")
            g = growth.get(area, 0)

            summary.append(
                f"In {area}, prices show a **{t} trend** while demand appears **{d}**. "
                f"Approximate growth: **{g:.1f}%**."
            )

        summary.append(
            "Investors should focus on upward price + rising demand markets. "
            "Flat markets may offer negotiation leverage."
        )

        return " ".join(summary)
