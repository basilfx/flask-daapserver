from daapserver.utils import generate_persistent_id

import zeroconf
import socket


class Bonjour(object):
    """
    DAAPServer Bonjour/Zeroconf handler.
    """

    def __init__(self):
        """
        Construct a new Bonjour/Zeroconf server. This server takes `DAAPServer`
        instances and advertises them.
        """

        self.zeroconf = zeroconf.Zeroconf(zeroconf.InterfaceChoice.All)
        self.daap_servers = {}

    def publish(self, daap_server, preferred_database=None):
        """
        Publish a given `DAAPServer` instance.

        The given instances should be fully configured, including the provider.
        By default Zeroconf only advertises the first database, but the DAAP
        protocol has support for multiple databases. Therefore, the parameter
        `preferred_database` can be set to choose which database ID will be
        served.

        If the provider is not fully configured (in other words, if the
        preferred database cannot be found), this method will not publish this
        server. In this case, simply call this method again when the provider
        is ready.

        If the server was already published, it will be unpublished first.

        :param DAAPServer daap_server: DAAP Server instance to publish.
        :param int preferred_database: ID of the database to advertise.
        """

        if daap_server in self.daap_servers:
            self.unpublish(daap_server)

        # Zeroconf can advertise the information for one database only. Since
        # the protocol supports multiple database, let the user decide which
        # database to advertise. If none is specified, take the first one.
        provider = daap_server.provider

        try:
            if preferred_database is not None:
                database = provider.server.databases[preferred_database]
            else:
                database = provider.server.databases.values()[0]
        except LookupError:
            # The server may not have any databases (yet).
            return

        # The IP 0.0.0.0 tells this server to bind to all interfaces. However,
        # Bonjour advertises itself to others, so others need an actual IP.
        # There is definately a better way, but it works.
        if daap_server.ip == "0.0.0.0":
            addresses = []

            for address in zeroconf.get_all_addresses(socket.AF_INET):
                if not address == "127.0.0.1":
                    addresses.append(socket.inet_aton(address))
        else:
            addresses = [socket.inet_aton(daap_server.ip)]

        # Determine machine ID and database ID, depending on the provider. If
        # the provider has no support for persistent IDs, generate a random
        # ID.
        if provider.supports_persistent_id:
            machine_id = hex(provider.server.persistent_id)
            database_id = hex(database.persistent_id)
        else:
            machine_id = hex(generate_persistent_id())
            database_id = hex(generate_persistent_id())

        # iTunes 11+ uses more properties, but this seems to be sufficient.
        description = {
            "txtvers": "1",
            "Password": str(int(bool(daap_server.password))),
            "Machine Name": provider.server.name,
            "Machine ID": machine_id.upper(),
            "Database ID": database_id.upper()
        }

        # Test is zeroconf supports multiple addresses or not. For
        # compatibility with zeroconf 0.17.3 or less.
        if not hasattr(zeroconf.ServiceInfo("", ""), "addresses"):
            addresses = addresses[0]

        self.daap_servers[daap_server] = zeroconf.ServiceInfo(
            type="_daap._tcp.local.",
            name=provider.server.name + "._daap._tcp.local.",
            address=addresses,
            port=daap_server.port,
            properties=description)
        self.zeroconf.register_service(self.daap_servers[daap_server])

    def unpublish(self, daap_server):
        """
        Unpublish a given server.

        If the server was not published, this method will not do anything.

        :param DAAPServer daap_server: DAAP Server instance to publish.
        """

        if daap_server not in self.daap_servers:
            return

        self.zeroconf.unregister_service(self.daap_servers[daap_server])

        del self.daap_servers[daap_server]

    def close(self):
        """
        Close the Zeroconf instance.
        """

        self.zeroconf.close()
