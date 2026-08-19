from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import include, path, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/menu/', include('menu.urls')),
    path('api/tables/', include('tables.urls')),
    path('api/orders/', include('orders.urls')),
]


def spa_index(request, *args, **kwargs):
    """Serve the built React app's index.html for any non-API route, so
    client-side routes (e.g. /tables/3) work on a direct load/refresh."""
    index_file = settings.FRONTEND_DIST / 'index.html'
    if not index_file.exists():
        return HttpResponseNotFound(
            "Frontend build not found. Run 'npm run build' in frontend/ first."
        )
    return HttpResponse(index_file.read_text(encoding='utf-8'))


urlpatterns += [
    re_path(r'^(?!api/|admin/|static/).*$', spa_index),
]
