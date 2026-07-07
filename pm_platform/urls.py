from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path("dashboard/admin/", include("dashboard.urls")),
    path('api/', include('pm_platform.api_urls')),
    path('', root_redirect, name='root_redirect'),
    path('', include('accounts.urls')),
    path('projects/', include('projects.urls')),
    path('tasks/', include('tasks.urls')),
    path('', include('communication.urls')),
    path('', include('integrations.urls')),
    path('', include('exports.urls')),
    path(
    "notifications/",
    include("accounts.urls_notifications"),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
