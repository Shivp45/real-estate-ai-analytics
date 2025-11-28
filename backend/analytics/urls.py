from django.urls import path
from .views import (
    HealthCheckView,
    AnalyzeView,
    DatasetUploadView,
    MyHistoryView,
    AdminUserHistoryView,
    ExportAllHistoryView
)

urlpatterns = [
    path("health/", HealthCheckView.as_view()),
    path("analyze/", AnalyzeView.as_view()),
    path("dataset/upload/", DatasetUploadView.as_view()),
    path("history/my/", MyHistoryView.as_view()),
    path("history/admin/<int:user_id>/", AdminUserHistoryView.as_view()),
    path("history/export-all/", ExportAllHistoryView.as_view()),  # NEW
]

