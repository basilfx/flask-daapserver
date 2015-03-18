import zeroconf
import socket


class Bonjour(object):
    """
    """

    def __init__(self):
        """
        """

        self.zeroconf = zeroconf.Zeroconf(zeroconf.InterfaceChoice.All)
        self.servers = {}

    def publish(self, server):
        """
        """

        if server in self.servers:
            self.unpublish(server)

        # The IP 0.0.0.0 tells SubDaap to bind to all interfaces. However,
        # Bonjour advertises itself to others, so others need an actual IP.
        # There is definately a better way, but it works.
        address = server.ip

        if server.ip == "0.0.0.0":
            for ip in zeroconf.get_all_addresses(socket.AF_INET):
                if ip != "127.0.0.1":
                    address = ip
                    break

        # iTunes 11+ uses more properties, but this seems to be sufficient.
        description = {
            "txtvers": "1",
            "Password": str(int(bool(server.password))),
            "Machine Name": server.server_name
        }

        self.servers[server] = zeroconf.ServiceInfo(
            type="_daap._tcp.local.",
            name=server.server_name + "._daap._tcp.local.",
            address=socket.inet_aton(address),
            port=server.port,
            properties=description)
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
