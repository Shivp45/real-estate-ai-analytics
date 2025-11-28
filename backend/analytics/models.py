from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="history")
    query = models.TextField()
    summary = models.TextField(blank=True, null=True)
    full_response = models.JSONField(null=True, blank=True)  # ← stores charts, tables, everything
    intent_type = models.CharField(max_length=100, blank=True, null=True)
    areas = models.CharField(max_length=255, blank=True, null=True)
    time_window = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.query[:30]}"
