import os
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .serializers import AnalyzeRequestSerializer, DatasetUploadSerializer, SearchHistorySerializer
from .services.data_repository import DataRepository
from .services.ai_summarizer import AISummarizer
from .utils.query_parser import parse_query_intent
from .utils.analytics_core import analyze_intent
from .models import SearchHistory


class HealthCheckView(APIView):
    def get(self, request):
        try:
            df = DataRepository.get_dataframe()
            dataset_ok = not df.empty
            rows = int(df.shape[0]) if dataset_ok else 0
        except Exception:
            dataset_ok = False
            rows = 0
        return Response(
            {
                "status": "ok",
                "dataset_loaded": dataset_ok,
                "dataset_path": DataRepository.get_current_path(),
                "rows": rows,
            }
        )


class AnalyzeView(APIView):
    """
    POST /api/analyze/
    Body: { "query": "Analyze Wakad" }

    Now stores full chatbot response in DB for replay later.
    """
    permission_classes = [IsAuthenticated]

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

        # Build full response payload (this gets stored + returned)
        full_response = {
            "query": query,
            "intent": intent,
            "summary": summary_text,
            "charts": analysis["charts"],
            "table": analysis["table"],
        }

        # Save user-specific full history
        user = request.user
        years = analysis["insights"].get("years", [])
        time_window = ""
        if years:
            time_window = f"{min(years)} - {max(years)}"

        SearchHistory.objects.create(
            user=user,
            query=query,
            summary=summary_text,
            full_response=full_response,  # <-- full chatbot memory stored here
            intent_type=intent.get("intent_type", ""),
            areas=", ".join(analysis["insights"].get("areas", [])),
            time_window=time_window,
        )

        return Response({"success": True, "data": full_response}, status=status.HTTP_200_OK)


class DatasetUploadView(APIView):
    """
    POST /api/dataset/upload/
    Form-data: file=<Excel>
    Only admins can upload.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_admin():
            return Response(
                {"success": False, "message": "Only admins can upload dataset."},
                status=status.HTTP_403_FORBIDDEN,
            )

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


class MyHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = SearchHistory.objects.filter(user=request.user).order_by("-created_at")
        serializer = SearchHistorySerializer(qs, many=True)
        return Response({"success": True, "history": serializer.data})


class AdminUserHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, user_id):
        qs = SearchHistory.objects.filter(user_id=user_id).order_by("-created_at")
        serializer = SearchHistorySerializer(qs, many=True)
        return Response({"success": True, "history": serializer.data})
    
class ExportAllHistoryView(APIView):
    """
    Admin only: returns all stored conversations in raw JSON for export purposes.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        qs = SearchHistory.objects.all().order_by("-created_at")
        serializer = SearchHistorySerializer(qs, many=True)
        return Response({"success": True, "export": serializer.data})

