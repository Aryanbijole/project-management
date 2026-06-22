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
    path('api/', include('pm_platform.api_urls')),
    path('', root_redirect, name='root_redirect'),
    path('', include('accounts.urls')),
    path('', include('projects.urls')),
    path('', include('tasks.urls')),
    path('', include('communication.urls')),
    path('', include('integrations.urls')),
    path('', include('exports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
