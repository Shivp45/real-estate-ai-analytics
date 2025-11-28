======== backend/.env.example ========

DEBUG=True
SECRET_KEY=change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Path to your default dataset relative to backend root
DEFAULT_DATASET_PATH=data/real_estate_data.xlsx

# Optional OpenAI key – if not provided, rule-based summarizer is used
OPENAI_API_KEY=your_openai_api_key_here


======== backend/manage.py ========

#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_analytics.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django. Is it installed?") from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()


======== backend/requirements.txt ========

Django==5.0.6
djangorestframework==3.15.2
django-cors-headers==4.4.0
pandas==2.2.2
openpyxl==3.1.5
python-dotenv==1.0.1
openai==0.28.0


======== backend/real_estate_analytics/__init__.py ========

# empty


======== backend/real_estate_analytics/asgi.py ========

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_analytics.settings")
application = get_asgi_application()


======== backend/real_estate_analytics/settings.py ========

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret-key-for-dev")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "analytics",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "real_estate_analytics.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "real_estate_analytics.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ]
}

CORS_ALLOW_ALL_ORIGINS = True

DEFAULT_DATASET_PATH = os.getenv(
    "DEFAULT_DATASET_PATH",
    str(BASE_DIR / "data" / "real_estate_data.xlsx"),
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()


======== backend/real_estate_analytics/urls.py ========

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("analytics.urls")),
]


======== backend/real_estate_analytics/wsgi.py ========

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real_estate_analytics.settings")
application = get_wsgi_application()


======== backend/analytics/__init__.py ========

# empty


======== backend/analytics/apps.py ========

from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"


======== backend/analytics/serializers.py ========

from rest_framework import serializers

class AnalyzeRequestSerializer(serializers.Serializer):
    query = serializers.CharField(allow_blank=False, max_length=500)


class DatasetUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith((".xlsx", ".xls")):
            raise serializers.ValidationError("Only Excel files (.xlsx, .xls) are allowed.")
        return value


======== backend/analytics/urls.py ========

from django.urls import path
from .views import AnalyzeView, DatasetUploadView, HealthCheckView

urlpatterns = [
    path("analyze/", AnalyzeView.as_view(), name="analyze"),
    path("dataset/upload/", DatasetUploadView.as_view(), name="dataset-upload"),
    path("health/", HealthCheckView.as_view(), name="health"),
]


======== backend/analytics/views.py ========

import os
from datetime import datetime
from pathlib import Path

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import AnalyzeRequestSerializer, DatasetUploadSerializer
from .services.data_repository import DataRepository
from .services.ai_summarizer import AISummarizer
from .utils.query_parser import parse_query_intent
from .utils.analytics_core import analyze_intent


class HealthCheckView(APIView):
    def get(self, request):
        try:
            df = DataRepository.get_dataframe()
            dataset_ok = not df.empty
        except Exception:
            dataset_ok = False
        return Response(
            {
                "status": "ok",
                "dataset_loaded": dataset_ok,
                "dataset_path": DataRepository.get_current_path(),
            }
        )


class AnalyzeView(APIView):
    """
    POST /api/analyze/
    Body: { "query": "Analyze Wakad" }
    """

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Please provide a non-empty query.",
                        "details": serializer.errors,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query = serializer.validated_data["query"].strip()

        try:
            df = DataRepository.get_dataframe()
        except FileNotFoundError:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "DATASET_NOT_FOUND",
                        "message": (
                            "Dataset file is missing. Please upload a new Excel file "
                            "or configure DEFAULT_DATASET_PATH correctly."
                        ),
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except ValueError as e:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "DATASET_INVALID",
                        "message": str(e),
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "DATASET_ERROR",
                        "message": f"Unexpected error when loading dataset: {e}",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if df.empty:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "EMPTY_DATASET",
                        "message": "The current dataset has no records.",
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        intent = parse_query_intent(df, query)

        if intent.get("intent_type") == "invalid":
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_QUERY",
                        "message": "Your query seems empty or invalid. Please try again.",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        areas = intent.get("areas") or []
        if not areas:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "UNKNOWN_LOCALITY",
                        "message": (
                            "I could not find any matching locality in the dataset. "
                            "Please check the spelling or try another area."
                        ),
                    },
                },
                status=status.HTTP_200_OK,
            )

        analysis = analyze_intent(df, intent)

        if not analysis["table"]["rows"]:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "NO_DATA_FOR_FILTER",
                        "message": (
                            "I found the locality, but there is no data matching "
                            "the specified time window or filters."
                        ),
                    },
                },
                status=status.HTTP_200_OK,
            )

        summarizer = AISummarizer()
        summary_text = summarizer.summarize(query, intent, analysis["insights"])

        response_data = {
            "success": True,
            "data": {
                "query": query,
                "intent": intent,
                "summary": summary_text,
                "charts": analysis["charts"],
                "table": analysis["table"],
            },
        }

        return Response(response_data, status=status.HTTP_200_OK)


class DatasetUploadView(APIView):
    """
    POST /api/dataset/upload/
    Form-data: file=<Excel>
    """

    def post(self, request):
        serializer = DatasetUploadSerializer(data=request.data, files=request.FILES)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_UPLOAD",
                        "message": "Please upload a valid Excel file.",
                        "details": serializer.errors,
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file = serializer.validated_data["file"]

        upload_dir = Path(settings.MEDIA_ROOT) / "datasets"
        upload_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        dest_path = upload_dir / f"dataset_{timestamp}_{file.name}"

        with dest_path.open("wb+") as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        try:
            df = DataRepository.replace_with_file(str(dest_path))
        except Exception as e:
            # Remove invalid file
            try:
                os.remove(dest_path)
            except OSError:
                pass
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "DATASET_UPLOAD_FAILED",
                        "message": f"Failed to load uploaded dataset: {e}",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Dataset uploaded and activated successfully.",
                "rows_loaded": int(df.shape[0]),
                "columns": list(df.columns),
            },
            status=status.HTTP_200_OK,
        )


======== backend/analytics/services/__init__.py ========

# empty


======== backend/analytics/services/ai_summarizer.py ========

import json
from typing import Dict, Any

import openai
from django.conf import settings


class AISummarizer:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            openai.api_key = self.api_key

    def summarize(self, query: str, intent: Dict[str, Any], insights: Dict[str, Any]) -> str:
        """
        Try OpenAI first; if unavailable or fails, use rule-based fallback.
        """
        if self.api_key:
            try:
                return self._summarize_with_openai(query, intent, insights)
            except Exception:
                # Fallback to rule-based summarizer
                return self._rule_based_summary(query, intent, insights)
        else:
            return self._rule_based_summary(query, intent, insights)

    def _summarize_with_openai(self, query: str, intent: Dict[str, Any], insights: Dict[str, Any]) -> str:
        prompt_context = {
            "user_query": query,
            "intent": intent,
            "insights": insights,
        }

        system_message = (
            "You are an expert real estate market analyst. "
            "You will receive structured analytics data as JSON and must produce a concise, "
            "actionable 100–200 word summary. Focus on: price trend, demand, growth, "
            "comparisons between areas, anomalies, and practical recommendations for buyers/investors."
        )

        user_message = (
            "Here is the analytics context as JSON:\n\n"
            f"{json.dumps(prompt_context, indent=2)}\n\n"
            "Write a 100–200 word summary. Be specific and insights-focused."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=320,
            temperature=0.4,
        )

        return response.choices[0].message["content"].strip()

    def _rule_based_summary(self, query: str, intent: Dict[str, Any], insights: Dict[str, Any]) -> str:
        areas = insights.get("areas", [])
        years = insights.get("years", [])
        price_trend = insights.get("price_trend_direction", {})
        demand_trend = insights.get("demand_trend_direction", {})
        price_growth = insights.get("price_growth_pct", {})
        comparison = intent.get("intent_type") == "comparison"

        parts = []

        if not areas or not years:
            return (
                "I was unable to extract enough data to generate a detailed summary. "
                "Please check the locality name or try a different query."
            )

        year_span = f"from {min(years)} to {max(years)}"

        if comparison and len(areas) >= 2:
            parts.append(
                f"Comparing {', '.join(areas[:-1])} and {areas[-1]} {year_span}, "
                "we see notable differences in price and demand trends."
            )
        else:
            parts.append(
                f"Analyzing {', '.join(areas)} {year_span}, "
                "we can observe clear patterns in pricing and demand."
            )

        for area in areas:
            pt = price_trend.get(area, "flat")
            dt = demand_trend.get(area, "flat")
            growth = price_growth.get(area)
            trend_text = []

            if pt == "up":
                trend_text.append("prices have generally increased")
            elif pt == "down":
                trend_text.append("prices have generally decreased")
            else:
                trend_text.append("prices have been relatively stable")

            if dt == "up":
                trend_text.append("with rising demand")
            elif dt == "down":
                trend_text.append("with softening demand")
            else:
                trend_text.append("with stable demand")

            growth_text = ""
            if isinstance(growth, (int, float)):
                growth_text = f" Approximate overall price growth is around {growth:.1f}%."

            parts.append(f"In {area}, " + " ".join(trend_text) + "." + growth_text)

        if comparison and len(areas) >= 2:
            parts.append(
                "Areas with stronger price and demand growth may be better suited for investors, "
                "while stable or softening markets may offer more negotiation room for end-users."
            )
        else:
            parts.append(
                "If you are an investor, prioritize years and localities where prices and demand both trend upward. "
                "For homebuyers seeking value, flat or slightly declining price trends can indicate better deals."
            )

        return " ".join(parts)


======== backend/analytics/services/data_repository.py ========

import threading
from typing import Optional

import pandas as pd
from django.conf import settings

from analytics.utils.data_loader import load_dataset_from_path

class DataRepository:
    """
    Simple in-memory store for the active dataset.
    Thread-safe enough for typical small deployments.
    """

    _lock = threading.Lock()
    _df: Optional[pd.DataFrame] = None
    _path: Optional[str] = None

    @classmethod
    def get_dataframe(cls) -> pd.DataFrame:
        with cls._lock:
            if cls._df is None:
                cls._path = settings.DEFAULT_DATASET_PATH
                cls._df = load_dataset_from_path(cls._path)
            return cls._df

    @classmethod
    def replace_with_file(cls, file_path: str) -> pd.DataFrame:
        with cls._lock:
            df = load_dataset_from_path(file_path)
            cls._df = df
            cls._path = file_path
            return df

    @classmethod
    def get_current_path(cls) -> Optional[str]:
        with cls._lock:
            return cls._path


======== backend/analytics/utils/__init__.py ========

# empty


======== backend/analytics/utils/analytics_core.py ========

from typing import Dict, Any

import numpy as np
import pandas as pd


def _filter_by_intent(df: pd.DataFrame, intent: Dict[str, Any]) -> pd.DataFrame:
    filtered = df.copy()

    areas = intent.get("areas") or []
    if areas:
        filtered = filtered[filtered["Area"].isin(areas)]

    years = intent.get("years") or []
    last_n = intent.get("last_n_years") or 0

    if years:
        filtered = filtered[filtered["Year"].isin(years)]

    if last_n and not years:
        max_year = filtered["Year"].max()
        min_year = max_year - last_n + 1
        filtered = filtered[(filtered["Year"] >= min_year) & (filtered["Year"] <= max_year)]

    return filtered


def _trend_direction(values):
    values = list(values)
    if len(values) < 2:
        return "flat"
    if values[-1] > values[0] * 1.03:
        return "up"
    if values[-1] < values[0] * 0.97:
        return "down"
    return "flat"


def _compute_growth_pct(first: float, last: float) -> float:
    if first <= 0:
        return 0.0
    return (last - first) / first * 100.0


def analyze_intent(df: pd.DataFrame, intent: Dict[str, Any]) -> Dict[str, Any]:
    filtered = _filter_by_intent(df, intent)

    if filtered.empty:
        return {
            "filtered_df": filtered,
            "charts": [],
            "table": {"columns": [], "rows": []},
            "insights": {
                "areas": intent.get("areas", []),
                "years": [],
                "price_trend_direction": {},
                "demand_trend_direction": {},
                "price_growth_pct": {},
            },
        }

    areas = sorted(filtered["Area"].unique().tolist())
    years = sorted(filtered["Year"].dropna().unique().tolist())

    group = (
        filtered.groupby(["Area", "Year"])
        .agg({"Price": "mean", "Demand": "mean"})
        .reset_index()
        .sort_values(["Area", "Year"])
    )

    price_trend_direction = {}
    demand_trend_direction = {}
    price_growth_pct = {}

    price_chart_series = []
    demand_chart_series = []

    for area in areas:
        area_data = group[group["Area"] == area].sort_values("Year")
        prices = area_data["Price"].tolist()
        demands = area_data["Demand"].tolist()
        yrs = area_data["Year"].tolist()

        if not yrs:
            continue

        price_trend_direction[area] = _trend_direction(prices)
        demand_trend_direction[area] = _trend_direction(demands)

        if len(prices) >= 2:
            price_growth_pct[area] = _compute_growth_pct(prices[0], prices[-1])
        else:
            price_growth_pct[area] = 0.0

        price_chart_series.append(
            {
                "name": area,
                "data": [
                    {"Year": int(y), "Price": float(p)} for y, p in zip(yrs, prices)
                ],
            }
        )

        demand_chart_series.append(
            {
                "name": area,
                "data": [
                    {"Year": int(y), "Demand": float(d)} for y, d in zip(yrs, demands)
                ],
            }
        )

    charts = [
        {
            "id": "price_trend",
            "title": "Price Trend by Year",
            "type": "line",
            "xKey": "Year",
            "yKeys": ["Price"],
            "series": price_chart_series,
        },
        {
            "id": "demand_trend",
            "title": "Demand Trend by Year",
            "type": "line",
            "xKey": "Year",
            "yKeys": ["Demand"],
            "series": demand_chart_series,
        },
    ]

    table_columns = ["Year", "Area", "Price", "Demand", "Size"]
    table_rows = []

    filtered_sorted = filtered.sort_values(["Area", "Year"])

    for _, row in filtered_sorted.iterrows():
        table_rows.append(
            {
                "Year": int(row["Year"]),
                "Area": str(row["Area"]),
                "Price": float(row["Price"]) if not np.isnan(row["Price"]) else None,
                "Demand": float(row["Demand"]) if not np.isnan(row["Demand"]) else None,
                "Size": float(row["Size"]) if not np.isnan(row["Size"]) else None,
            }
        )

    insights = {
        "areas": areas,
        "years": years,
        "price_trend_direction": price_trend_direction,
        "demand_trend_direction": demand_trend_direction,
        "price_growth_pct": price_growth_pct,
    }

    return {
        "filtered_df": filtered_sorted,
        "charts": charts,
        "table": {"columns": table_columns, "rows": table_rows},
        "insights": insights,
    }


======== backend/analytics/utils/data_loader.py ========

from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = ["Year", "Area", "Price", "Demand", "Size"]


def load_dataset_from_path(path: str) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    df = pd.read_excel(file_path)

    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {', '.join(missing)}. "
            f"Found columns: {', '.join(df.columns)}"
        )

    # Basic cleaning
    df = df[REQUIRED_COLUMNS].copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Demand"] = pd.to_numeric(df["Demand"], errors="coerce")
    df["Size"] = pd.to_numeric(df["Size"], errors="coerce")

    df = df.dropna(subset=["Year", "Area"])
    df["Area"] = df["Area"].astype(str).str.strip()

    return df


======== backend/analytics/utils/query_parser.py ========

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


======== frontend/.env.example ========

VITE_API_BASE_URL=http://127.0.0.1:8000/api


======== frontend/index.html ========

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Real Estate Analytics Chatbot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body class="bg-light">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>


======== frontend/package.json ========

{
  "name": "real-estate-analytics-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.7",
    "bootstrap": "^5.3.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "recharts": "^2.12.7"
  },
  "devDependencies": {
    "@vitejs/plugin-react-swc": "^3.7.0",
    "vite": "^6.0.0"
  }
}


======== frontend/vite.config.mjs ========

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  }
});


======== frontend/src/App.jsx ========

import React, { useState } from "react";
import ChatLayout from "./components/ChatLayout.jsx";
import { useChatHistory } from "./hooks/useChatHistory.js";
import { analyzeQuery, uploadDataset } from "./api/client.js";

const App = () => {
  const { messages, addUserMessage, addBotMessage } = useChatHistory();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async (text) => {
    setError("");
    addUserMessage(text);
    setLoading(true);
    try {
      const res = await analyzeQuery(text);
      if (!res.success) {
        const errorMessage =
          res?.error?.message ||
          "Something went wrong while analyzing your query.";
        addBotMessage({
          type: "bot",
          error: errorMessage
        });
        setError("");
      } else {
        const data = res.data;
        addBotMessage({
          type: "bot",
          summary: data.summary,
          charts: data.charts,
          table: data.table
        });
      }
    } catch (e) {
      setError("Unable to reach the server. Please check backend is running.");
      addBotMessage({
        type: "bot",
        error: "I could not contact the analytics backend."
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDatasetUpload = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    setError("");
    setLoading(true);
    try {
      const res = await uploadDataset(file);
      if (!res.success) {
        setError(res?.error?.message || "Dataset upload failed.");
      } else {
        setError("");
        addBotMessage({
          type: "bot",
          summary: `Dataset uploaded successfully with ${res.rows_loaded} rows.`,
          charts: [],
          table: { columns: [], rows: [] }
        });
      }
    } catch (err) {
      setError("Failed to upload dataset. Check backend or file format.");
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  };

  const clearError = () => setError("");

  return (
    <ChatLayout
      messages={messages}
      onSend={handleSend}
      loading={loading}
      error={error}
      clearError={clearError}
      onDatasetUpload={handleDatasetUpload}
    />
  );
};

export default App;


======== frontend/src/main.jsx ========

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "bootstrap/dist/css/bootstrap.min.css";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);


======== frontend/src/styles.css ========

body {
  background: #f5f6fa;
}

.chat-container {
  min-height: 100vh;
}

.chat-card {
  height: 70vh;
}

.message-list {
  max-height: 100%;
}

.user-bubble {
  border-radius: 1rem;
  padding: 0.6rem 0.9rem;
  max-width: 70%;
  word-wrap: break-word;
}

.bot-bubble {
  max-width: 100%;
}

code {
  font-size: 0.85rem;
}


======== frontend/src/api/client.js ========

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api"
});

export const analyzeQuery = async (query) => {
  const res = await api.post("/analyze/", { query });
  return res.data;
};

export const uploadDataset = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/dataset/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return res.data;
};

export default api;


======== frontend/src/hooks/useChatHistory.js ========

import { useState } from "react";

export function useChatHistory() {
  const [messages, setMessages] = useState([]);

  const addUserMessage = (text) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + "-user",
        type: "user",
        text
      }
    ]);
  };

  const addBotMessage = (payload) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + "-bot",
        type: "bot",
        ...payload
      }
    ]);
  };

  return {
    messages,
    addUserMessage,
    addBotMessage
  };
}


======== frontend/src/components/ChartView.jsx ========

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer
} from "recharts";

const colors = ["#0d6efd", "#198754", "#dc3545", "#fd7e14", "#6f42c1"];

const ChartView = ({ chart }) => {
  if (!chart || !chart.series || chart.series.length === 0) {
    return null;
  }

  const xKey = chart.xKey;
  const yKey = chart.yKeys[0];

  const allPoints = {};
  chart.series.forEach((series) => {
    series.data.forEach((point) => {
      const xVal = point[xKey];
      if (!allPoints[xVal]) {
        allPoints[xVal] = { [xKey]: xVal };
      }
      allPoints[xVal][`${series.name}_${yKey}`] = point[yKey];
    });
  });

  const data = Object.values(allPoints).sort((a, b) => a[xKey] - b[xKey]);

  return (
    <div className="mt-3">
      <h6 className="fw-semibold">{chart.title}</h6>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          {chart.series.map((series, idx) => (
            <Line
              key={series.name}
              type="monotone"
              dataKey={`${series.name}_${yKey}`}
              name={`${series.name} ${yKey}`}
              stroke={colors[idx % colors.length]}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ChartView;


======== frontend/src/components/ChatLayout.jsx ========

import React from "react";
import MessageList from "./MessageList.jsx";
import MessageInput from "./MessageInput.jsx";
import ErrorAlert from "./ErrorAlert.jsx";
import LoadingSpinner from "./LoadingSpinner.jsx";

const ChatLayout = ({
  messages,
  onSend,
  loading,
  error,
  clearError,
  onDatasetUpload
}) => {
  return (
    <div className="container py-4 chat-container">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <div>
              <h3 className="mb-0">Real Estate Analytics Chatbot</h3>
              <small className="text-muted">
                Ask about locality trends, demand, and price growth.
              </small>
            </div>
            <div>
              <label className="btn btn-outline-secondary btn-sm mb-0">
                Upload Dataset
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  hidden
                  onChange={onDatasetUpload}
                />
              </label>
            </div>
          </div>

          <ErrorAlert message={error} onClose={clearError} />

          <div className="card border-0 shadow-sm chat-card">
            <div className="card-body d-flex flex-column">
              <div className="flex-grow-1 overflow-auto mb-2">
                <MessageList messages={messages} />
              </div>
              {loading && <LoadingSpinner />}
              <MessageInput onSend={onSend} disabled={loading} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatLayout;


======== frontend/src/components/DataTable.jsx ========

import React from "react";

const DataTable = ({ table }) => {
  if (!table || !table.rows || table.rows.length === 0) {
    return null;
  }

  return (
    <div className="mt-3">
      <h6 className="fw-semibold">Data Table</h6>
      <div className="table-responsive" style={{ maxHeight: "280px" }}>
        <table className="table table-sm table-striped align-middle">
          <thead className="table-light sticky-top">
            <tr>
              {table.columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, idx) => (
              <tr key={idx}>
                {table.columns.map((col) => (
                  <td key={col}>{row[col] !== null && row[col] !== undefined ? row[col] : "-"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTable;


======== frontend/src/components/ErrorAlert.jsx ========

import React from "react";

const ErrorAlert = ({ message, onClose }) => {
  if (!message) return null;
  return (
    <div className="alert alert-danger d-flex justify-content-between align-items-center mt-2" role="alert">
      <span>{message}</span>
      {onClose && (
        <button type="button" className="btn-close" onClick={onClose} aria-label="Close"></button>
      )}
    </div>
  );
};

export default ErrorAlert;


======== frontend/src/components/LoadingSpinner.jsx ========

import React from "react";

const LoadingSpinner = () => (
  <div className="d-flex justify-content-center my-3">
    <div className="spinner-border" role="status">
      <span className="visually-hidden">Loading...</span>
    </div>
  </div>
);

export default LoadingSpinner;


======== frontend/src/components/MessageInput.jsx ========

import React, { useState } from "react";

const MessageInput = ({ onSend, disabled }) => {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  };

  return (
    <form onSubmit={handleSubmit} className="mt-3">
      <div className="input-group">
        <input
          type="text"
          className="form-control"
          placeholder="Ask about localities, price trends, demand, growth..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
        />
        <button className="btn btn-primary" type="submit" disabled={disabled}>
          Send
        </button>
      </div>
      <div className="form-text">
        Example: <code>Compare Ambegaon Budruk and Aundh demand trends</code>
      </div>
    </form>
  );
};

export default MessageInput;


======== frontend/src/components/MessageList.jsx ========

import React from "react";
import ResponseCard from "./ResponseCard.jsx";

const MessageList = ({ messages }) => {
  if (!messages.length) {
    return (
      <div className="text-muted text-center py-5">
        <p className="mb-2">Start by asking something like:</p>
        <code className="d-block">Analyze Wakad</code>
        <code className="d-block mt-1">Compare Ambegaon Budruk and Aundh demand trends</code>
        <code className="d-block mt-1">Show price growth for Akurdi over the last 3 years</code>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg) => {
        if (msg.type === "user") {
          return (
            <div key={msg.id} className="d-flex justify-content-end mb-2">
              <div className="badge bg-primary text-wrap text-start user-bubble">
                {msg.text}
              </div>
            </div>
          );
        }
        if (msg.type === "bot") {
          return (
            <div key={msg.id} className="d-flex justify-content-start mb-2">
              <div className="bot-bubble flex-grow-1">
                {msg.error ? (
                  <div className="alert alert-warning mb-0">
                    <strong>Note:</strong> {msg.error}
                  </div>
                ) : (
                  <ResponseCard
                    summary={msg.summary}
                    charts={msg.charts}
                    table={msg.table}
                  />
                )}
              </div>
            </div>
          );
        }
        return null;
      })}
    </div>
  );
};

export default MessageList;


======== frontend/src/components/ResponseCard.jsx ========

import React from "react";
import ChartView from "./ChartView.jsx";
import DataTable from "./DataTable.jsx";

const ResponseCard = ({ summary, charts, table }) => {
  return (
    <div className="card mb-3 border-0 shadow-sm">
      <div className="card-body">
        <h5 className="card-title">AI Insight</h5>
        <p className="card-text">{summary}</p>

        {charts && charts.length > 0 && (
          <div className="mt-2">
            {charts.map((chart) => (
              <ChartView key={chart.id} chart={chart} />
            ))}
          </div>
        )}

        <DataTable table={table} />
      </div>
    </div>
  );
};

export default ResponseCard;


