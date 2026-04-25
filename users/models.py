from django.db import models
from django.contrib.auth.models import User


# ================= Resume Model =================
class Resume(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/')

    score = models.IntegerField(default=0)

    matched_skills = models.JSONField(blank=True, null=True)
    missing_skills = models.JSONField(blank=True, null=True)

    coverage = models.IntegerField(default=0)
    gap = models.IntegerField(default=0)

    recommended_roles = models.JSONField(blank=True, null=True)
    suggestions = models.JSONField(blank=True, null=True)
    predicted_salary = models.IntegerField(default=0)

    # ✅ NEW FEATURES (SAFE ADDITIONS)

    ai_summary = models.TextField(blank=True, null=True)

    version = models.IntegerField(default=1)

    comparison_group = models.CharField(max_length=100, blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Resume - {self.uploaded_at}"


    # NEW STORED ANALYSIS DATA
    matched_skills = models.JSONField(blank=True, null=True)
    missing_skills = models.JSONField(blank=True, null=True)

    coverage = models.IntegerField(default=0)
    gap = models.IntegerField(default=0)

    recommended_roles = models.JSONField(blank=True, null=True)
    suggestions = models.JSONField(blank=True, null=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Resume - {self.uploaded_at}"


# ================= Security Model =================
class UserSecurity(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_verified = models.BooleanField(default=False)
    failed_attempts = models.IntegerField(default=0)

    def __str__(self):
        return f"Security: {self.user.username}"


# ================= Activity Logs =================
class ActivityLog(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"
