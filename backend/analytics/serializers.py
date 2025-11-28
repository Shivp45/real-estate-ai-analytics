from rest_framework import serializers
from .models import SearchHistory


class AnalyzeRequestSerializer(serializers.Serializer):
    query = serializers.CharField(allow_blank=False, max_length=500)


class DatasetUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.lower().endswith((".xlsx", ".xls")):
            raise serializers.ValidationError("Only Excel files (.xlsx, .xls) are allowed.")
        return value


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = [
            "id",
            "query",
            "summary",
            "intent_type",
            "areas",
            "time_window",
            "created_at",
        ]
