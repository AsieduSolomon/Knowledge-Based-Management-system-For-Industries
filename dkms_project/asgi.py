import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dkms_project.settings')

# get_asgi_application() runs django.setup() internally. This must happen
# before importing anything that touches models (routing -> consumers ->
# models), or those imports fail with "settings are not configured" when
# this file is loaded directly by an ASGI server (e.g. daphne on Render)
# instead of via manage.py, which normally sets Django up first.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from maintenance.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})