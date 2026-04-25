from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # 🔥 REQUIRED for Google, GitHub, Facebook, LinkedIn login
    path("accounts/", include("allauth.urls")),

    # Your app URLs
    path("", include("users.urls")),
]

# MEDIA FILES SUPPORT
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)