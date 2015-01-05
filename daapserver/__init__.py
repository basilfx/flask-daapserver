from gevent.pywsgi import WSGIServer

from daapserver.bonjour import Bonjour
from daapserver.server import create_server_app

__all__ = ["DaapServer", "Bonjour", "create_server_app"]

__version__ = "2.2.0"


class DaapServer(object):
    """
    DAAP Server instance. Combine all components from this module in a ready
    to use class.
    """

    def __init__(self, provider, server_name, password=None, ip="0.0.0.0",
                 port=3689, cache=True, cache_timeout=3600, bonjour=True,
                 debug=False):
        """
        Construct a new DAAP Server.
        """

        self.provider = provider
        self.server_name = server_name
        self.password = password
        self.ip = ip
        self.port = port
        self.cache = cache
        self.cache_timeout = cache_timeout
        self.bonjour = Bonjour() if bonjour else None
        self.debug = debug

        # Create DAAP server app
        self.app = create_server_app(
            self.provider, self.server_name, self.password, self.cache,
            self.debug)

    def serve_forever(self):
        """
        Run the DAAP server. Start by advertising the server via Bonjour. Then
        serve requests until CTRL + C is received.
        """

        # Create WSGI server
        self.server = WSGIServer((self.ip, self.port), application=self.app)

        # Register Bonjour
        if self.bonjour:
            self.bonjour.publish(self)

        # Start server until finished
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass

        # Unregister Bonjour
        if self.bonjour:
            self.bonjour.unpublish(self)
