from django.conf import settings
from django.core.servers.basehttp import WSGIRequestHandler
from django.db import connection

from devserver.utils.time import ms_from_timedelta

from datetime import datetime

class SlimWSGIRequestHandler(WSGIRequestHandler):
    """
    Hides all requests that originate from ```MEDIA_URL`` as well as any
    request originating with a prefix included in ``DEVSERVER_IGNORED_PREFIXES``.
    """
    def handle(self, *args, **kwargs):
        self._start_request = datetime.now()
        return WSGIRequestHandler.handle(self, *args, **kwargs)
        
    def log_message(self, format, *args):
        duration = datetime.now() - self._start_request

        env = self.get_environ()
        
        if settings.MEDIA_URL.startswith('http:'):
            if ('http://%s%s' % (env['HTTP_HOST'], self.path)).startswith(settings.MEDIA_URL):
                return
        
        # if self.path.startswith(settings.MEDIA_URL):
        #     return
        for path in getattr(settings, 'DEVSERVER_IGNORED_PREFIXES', []):
            if self.path.startswith(path):
                return
        
        format += " (time: %.2fs; sql: %dms (%dq))"
        args = list(args) + [
            ms_from_timedelta(duration) / 1000,
            sum(float(c.get('time', 0)) for c in connection.queries) * 1000,
            len(connection.queries),
        ]
        return WSGIRequestHandler.log_message(self, format, *args)