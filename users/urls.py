from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # ---------- AUTH ----------
    path("", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # ---------- PASSWORD FLOW ----------
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/", views.reset_password, name="reset_password"),

    # ---------- DASHBOARD ----------
    path("home/", views.home, name="home"),

    # ---------- RESUME ----------
    path("upload/", views.upload_resume, name="upload"),
    path("history/", views.history, name="history"),
    path("compare/", views.compare_resumes, name="compare_resumes"),

    # ---------- FILE ACTIONS ----------
    path("download-report/<int:resume_id>/", views.download_report, name="download_report"),
    path("delete-resume/<int:id>/", views.delete_resume, name="delete_resume"),
    path("bulk-delete/", views.bulk_delete, name="bulk_delete"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
