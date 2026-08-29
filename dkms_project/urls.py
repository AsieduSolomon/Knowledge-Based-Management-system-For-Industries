from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('maintenance.urls')),
]

# Serve uploaded media (equipment photos, recordings, etc.) directly through
# Django, in production as well as development.
#
# Note: Django's usual `django.conf.urls.static.static()` helper has a
# built-in guard that no-ops unless settings.DEBUG is True — wrapping it in
# our own `if DEBUG` check (or not) makes no difference, it silently does
# nothing either way once DEBUG=False. We use the lower-level `serve` view
# directly instead, which has no such guard.
#
# This isn't the most performant setup at large scale (a dedicated file
# host/CDN would be better), but for this system's traffic level it's
# simple and works without extra infrastructure. Without this, DEBUG=False
# (which we need for security) means media files 404 with nothing serving
# them at all.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]