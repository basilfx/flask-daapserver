import zeroconf
import socket


class Bonjour(object):
    """
    """

    def __init__(self):
        """
        """

        self.zeroconf = zeroconf.Zeroconf()
        self.servers = {}

    def publish(self, server):
        """
        """

        if server in self.servers:
            self.unpublish(server)

        ip = "127.0.0.1" if server.ip == "0.0.0.0" else server.ip
        description = {
            "txtvers": 1,
            "Password": int(bool(server.password)),
            "Machine Name": server.server_name
        }

        self.servers[server] = zeroconf.ServiceInfo(
            "_daap._tcp.local.", server.server_name + "._daap._tcp.local.",
            socket.inet_aton(ip), server.port, 0, 0,
            description)
        self.zeroconf.register_service(self.servers[server])

    def unpublish(self, server):
        """
        """

        if server not in self.servers:
            return

        self.zeroconf.unregister_service(self.servers[server])

        del self.servers[server]

    def close(self):
        """
        """

        self.zeroconf.close()
