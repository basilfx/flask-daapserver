# adopted from http://stackp.online.fr/?p=35

__all__ = ["Zeroconf"]

import sys
import select
import logging

# Load the libraries, prefer Bonjour
pybonjour = None
avahi = None

try:
    import pybonjour
except ImportError:
    try:
        import avahi
        import dbus
    except ImportError:
        pass

# Logger instance
logger = logging.getLogger(__name__)

class Zeroconf(object):
    """
    A simple class to publish a network service with zeroconf using avahi or
    pybonjour, preferring pybonjour.
    """

    class Helper(object):
        def __init__(self, name, port, **kwargs):
            self.name = name
            self.port = port
            self.stype = kwargs.get("stype", "_http._tcp")
            self.domain = kwargs.get("domain", "")
            self.host = kwargs.get("host", "")
            self.text = kwargs.get("text", "")

    class Pybonjour(Helper):
        def publish(self):
            #records as in mt-daapd
            txtRecord=pybonjour.TXTRecord()
            txtRecord["txtvers"]            = "1"
            txtRecord["iTSh Version"]       = "131073" #"196609"
            txtRecord["Machine Name"]       = self.name
            txtRecord["Password"]           = "0" # "False" ?
            #txtRecord["Database ID"]        = "" # 16 hex digits
            #txtRecord["Version"]            = "196616"
            #txtRecord["iTSh Version"]       =
            #txtRecord["Machine ID"]         = "" # 12 hex digits
            #txtRecord["Media Kinds Shared"] = "0"
            #txtRecord["OSsi"]               = "0x1F6" #?
            #txtRecord["MID"]                = "0x3AA6175DD7155BA7", = database id - 2 ?
            #txtRecord["dmv"]                = "131077"

            def register_callback(sdRef, flags, errorCode, name, regtype, domain):
                pass

            self.sdRef = pybonjour.DNSServiceRegister(name=self.name,
                                                      regtype="_daap._tcp",
                                                      port=self.port,
                                                      callBack=register_callback,
                                                      txtRecord=txtRecord)

            while True:
                ready = select.select([self.sdRef], [], [])

                if self.sdRef in ready[0]:
                    pybonjour.DNSServiceProcessResult(self.sdRef)
                    break

        def unpublish(self):
            self.sdRef.close()

    class Avahi(Helper):
        def publish(self):
            bus = dbus.SystemBus()

            server = dbus.Interface(
                bus.get_object(
                    avahi.DBUS_NAME,
                    avahi.DBUS_PATH_SERVER
                ),
                avahi.DBUS_INTERFACE_SERVER
            )

            self.group = dbus.Interface(
                bus.get_object(avahi.DBUS_NAME, server.EntryGroupNew()),
                avahi.DBUS_INTERFACE_ENTRY_GROUP
            )

            self.group.AddService(
                avahi.IF_UNSPEC, avahi.PROTO_UNSPEC,dbus.UInt32(0),
                self.name, self.stype, self.domain, self.host,
                dbus.UInt16(self.port), self.text
            )
            self.group.Commit()

        def unpublish(self):
            self.group.Reset()

    def __init__(self, *args, **kwargs):
        if pybonjour:
            helper = Zeroconf.Pybonjour
            logger.info("Selected PyBonjour for publishing")
        elif avahi:
            helper = Zeroconf.Avahi
            logger.info("Selected Avahi/DBus for publishing")
        else:
            raise ValueError("PyBonjour or Avahi not available")

        # Create helper
        self.helper = helper(*args, **kwargs)

    def publish(self):
        self.helper.publish()

        logger.info("Published service '%s'", self.helper.name)

    def unpublish(self):
        self.helper.unpublish()

        logger.info("Unpublished service '%s'", self.helper.name)