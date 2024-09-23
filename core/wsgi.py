"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.local')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', "core.settings")

application = get_wsgi_application()

"""
application = ProtocolTypeRouter({
    'http': get_wsgi_application(),
    # 'websocket': URLRouter(
    #    # your websocket routing here
    # ),
})
"""
