from daapserver.daap import DAAPObject
from daapserver import daap

from flask import Flask, Response, request, send_file

from werkzeug.contrib.cache import SimpleCache
from werkzeug import http

from functools import wraps

import hashlib
import inspect
import re

__all__ = ["create_daap_server"]

# Mapping for query string arguments to function arguments. Used by the
# daap_unpack_args decorator.
QS_MAPPING = [
    ("session-id", "session_id", int),
    ("revision-number", "revision", int),
    ("delta", "delta", int),
    ("type", "type", str),
    ("meta", "meta", lambda x: x.split(","))
]

# Query string arguments ignored for generating a cache key. Used by the
# daap_cache
QS_IGNORE_CACHE = [
    "session-id",
]

class ObjectResponse(Response):
    """
    DAAP object response. Encodes a DAAPObject to raw bytes and sets the content
    type.
    """

    def __init__(self, data, *args, **kwargs):
        # Set DAAP content type
        kwargs["mimetype"] = "application/x-dmap-tagged"

        # Instantiate response
        super(ObjectResponse, self).__init__(data.encode(), *args, **kwargs)

def create_daap_server(provider, server_name, password=None, cache=True,
    debug=False):
    """
    Create a DAAP server, based around a Flask application. The server requires
    a content provider, server name and optionally, a password. The content
    provider should return raw object data.

    Object responses can be cached. This may dramatically speed up connections
    for multiple clients. However, this is only limited to objects, not file
    servings.

    Note: in case the server is mounted as a WSGI app, make sure the server
    passes the authorization header.
    """

    # Create Flask App
    app = Flask(__name__)
    app.debug = debug

    # Setup cache
    if cache:
        if type(cache) == bool:
            cache = SimpleCache()
        else:
            # Assume is a user-provided cache with a get-set method.
            pass
    else:
        cache = False

    #
    # Context-aware helpers and decorators
    #

    def daap_wsgi_app(func):
        """
        WSGI middleware which will modify the environment and strip 'daap://'
        from the path. This way, Flask can route the request properly.
        """

        @wraps(func)
        def _inner(environment, start_response):
            if environment["PATH_INFO"].startswith("daap://"):
                environment["PATH_INFO"] = "/" + environment["PATH_INFO"].split("/", 3)[3]
            return func(environment, start_response)
        return _inner
    app.wsgi_app = daap_wsgi_app(app.wsgi_app)

    def daap_unpack_args(func):
        """
        Strip query string arguments and add them to the method as keyword
        arguments. Since the query string keys are defined, values will be
        converted to their approriate format. An exception will be thrown in
        case a requested argument is not available, or if the value could not
        be converted.
        """

        # Create a function specific mapping, only for arguments appearing in
        # the function declaration.
        args, _, _, _ = inspect.getargspec(func)
        mappings = [ mapping for mapping in QS_MAPPING if mapping[1] in args ]

        @wraps(func)
        def _inner(*args, **kwargs):
            for key, kwarg, casting in mappings:
                kwargs[kwarg] = casting(request.args[key])
            return func(*args, **kwargs)
        return _inner

    def daap_authenticate(func):
        """
        Check authorization header, if authorization is given. Returns 401
        response if the authentication failed.
        """

        @wraps(func)
        def _inner(*args, **kwargs):
            auth = request.authorization

            if not auth or not auth.password == password:
                return Response(None, 401, {'WWW-Authenticate': 'Basic realm="%s"' % server_name})
            return func(*args, **kwargs)
        return _inner if password else func

    def daap_cache_response(func=None):
        """
        Cache object responses if the cache has been initialized. The cache key
        is based on the request path and the semi-constant request arguments.
        The response is caches for as long as possible, which should not be a
        problem if the cache is cleared if the provider has new data.
        """

        @wraps(func)
        def _inner(*args, **kwargs):
            # Create hash key via hashlib. We use MD5 since it is slightly
            # faster than SHA1. Note that we don't require cryptographically
            # strong hashes -- we just want to have a short and computationally
            # unique key.
            key = hashlib.md5()

            # Add basic info
            key.update(func.__name__)
            key.update(request.path)

            for k, v in request.args.iteritems():
                if k not in QS_IGNORE_CACHE:
                    key.update(v)

            # Hit the cache
            key = key.digest()
            value = cache.get(key)

            if value is None:
                value = func(*args, **kwargs)
                cache.set(key, value, timeout=3600 * 6)
            return value
        return _inner if cache else func

    #
    # Request handlers
    #

    @app.after_request
    def after_request(response):
        """
        Append default response headers, independent of the return type.
        """

        response.headers["DAAP-Server"] = server_name
        response.headers["Content-Language"] = "en_us"
        response.headers["Accept-Ranges"] = "bytes"

        return response

    @app.route("/server-info", methods=["GET"])
    @daap_cache_response
    def server_info():
        data = [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.protocolversion", "2.0.0"),
            DAAPObject("daap.protocolversion", "3.0.0"),
            DAAPObject("dmap.itemname", server_name),
            DAAPObject("dmap.timeoutinterval", 1800),
            DAAPObject("dmap.supportsautologout", 1),
            DAAPObject("dmap.loginrequired", 1 if password else 0),
            DAAPObject("dmap.authenticationmethod", 2 if password else 0),
            DAAPObject("dmap.supportsextensions", 1),
            DAAPObject("dmap.supportsindex", 1),
            DAAPObject("dmap.supportsbrowse", 1),
            DAAPObject("dmap.supportsquery", 1),
            DAAPObject("dmap.databasescount", 1),
            DAAPObject("dmap.supportsupdate", 1),
            DAAPObject("dmap.supportsresolve", 1)
        ]

        if provider.supports_persistent_id:
            data.append(DAAPObject("dmap.supportspersistentids", 1))

        if provider.supports_artwork:
            data.append(DAAPObject("daap.supportsextradata", 1))

        return ObjectResponse(DAAPObject("dmap.serverinforesponse", data))

    @app.route("/content-codes", methods=["GET"])
    @daap_cache_response
    def content_codes():
        children = [ DAAPObject("dmap.status", 200) ]
        data = DAAPObject("dmap.contentcodesresponse", children)

        for code in daap.dmapCodeTypes.iterkeys():
            name, dtype = daap.dmapCodeTypes[code]

            children.append(
                DAAPObject("dmap.dictionary", [
                    DAAPObject("dmap.contentcodesnumber", code),
                    DAAPObject("dmap.contentcodesname", name),
                    DAAPObject("dmap.contentcodestype", daap.dmapReverseDataTypes[dtype])
                ])
            )

        return ObjectResponse(data)

    @app.route("/login", methods=["GET"])
    @daap_authenticate
    def login():
        session_id = provider.create_session()

        data = DAAPObject("dmap.loginresponse",[
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.sessionid", session_id)
        ])

        return ObjectResponse(data)

    @app.route("/logout", methods=["GET"])
    @daap_authenticate
    @daap_unpack_args
    def logout(session_id):
        provider.destroy_session(session_id)

        return Response(None, status=204)

    @app.route("/activity", methods=["GET"])
    @daap_authenticate
    @daap_unpack_args
    def activity(session_id):
        return Response(None, status=200)

    @app.route("/update", methods=["GET"])
    @daap_authenticate
    @daap_unpack_args
    def update(session_id, revision, delta):
        revision = provider.get_revision(session_id, revision, delta)

        data = DAAPObject("dmap.updateresponse", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.serverrevision", revision),
        ])

        return ObjectResponse(data)

    @app.route("/fp-setup", methods=["POST"])
    @daap_authenticate
    def fp_setup():
        """
        Fairplay validation, as sent by iTunes 11+. It will be unlikely this
        will be ever implemented.
        """

        raise NotImplemented

    @app.route("/databases", methods=["GET"])
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def databases(session_id, revision, delta):
        new, old = provider.get_databases(session_id, revision, delta)
        added, removed, is_update = utils.diff(new, old)

        # Single database response
        def _database(database):
            data = [
                DAAPObject("dmap.itemid", database.id),
                DAAPObject("dmap.itemname", database.name),
                DAAPObject("dmap.itemcount", len(database.items)),
                DAAPObject("dmap.containercount", len(database.containers))
            ]

            if provider.supports_persistent_id and database.persistent_id is not None:
                data.append(DAAPObject("dmap.persistentid", database.persistent_id))

            return DAAPObject("dmap.listingitem", data)

        # Databases response
        data = DAAPObject("daap.serverdatabases", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", int(is_update)),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(added)),
            DAAPObject("dmap.listing",(
                _database(new[k]) for k in added
            )),
            DAAPObject("dmap.deletedidlisting", (
                DAAPObject("dmap.itemid", k) for k in removed
            ))
        ])

        return ObjectResponse(data)

    @app.route("/databases/<int:database_id>/items/<int:item_id>/extra_data/artwork", methods=["GET"])
    @daap_unpack_args
    def database_item_artwork(database_id, item_id, session_id):
        data, mimetype, total_length = provider.get_artwork(session_id, database_id, item_id)

        # Setup response
        response = Response(data, 200, mimetype=mimetype, direct_passthrough=not isinstance(data, basestring))

        if total_length:
            response.headers["Content-Length"] = total_length

        return response

    @app.route("/databases/<int:database_id>/groups/<int:group_id>/extra_data/artwork", methods=["GET"])
    @daap_unpack_args
    def database_group_artwork(database_id, group_id, session_id, revision, delta):
        raise NotImplemented("Not implemented")

    @app.route("/databases/<int:database_id>/items/<int:item_id>.<suffix>", methods=["GET"])
    @daap_unpack_args
    def database_item(database_id, item_id, suffix, session_id):
        range_header = request.headers.get("Range", None)

        if range_header:
            begin, end = http.parse_range_header(range_header).ranges[0]
            data, mimetype, total_length = provider.get_item(session_id, database_id, item_id, byte_range=(begin, end))
            begin, end = (begin or 0), (end or total_length)

            # Setup response
            response = Response(data, 206, mimetype=mimetype, direct_passthrough=not isinstance(data, basestring))
            response.headers["Content-Range"] = "bytes %d-%d/%d" % (begin, end - 1, total_length)
            response.headers["Content-Length"] = end - begin
        else:
            data, mimetype, total_length = provider.get_item(session_id, database_id, item_id)

            # Setup response
            response = Response(data, 200, mimetype=mimetype, direct_passthrough=not isinstance(data, basestring))
            response.headers["Content-Length"] = total_length

        return response

    @app.route("/databases/<int:database_id>/items", methods=["GET"])
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_items(database_id, session_id, revision, delta, type):
        new, old = provider.get_items(session_id, database_id, revision, delta)
        added, removed, is_update = utils.diff(new, old)

        # Single item response
        def _item(item):
            data = [
                DAAPObject("dmap.itemid", item.id),
                DAAPObject("dmap.itemkind", 2),
            ]

            if provider.supports_persistent_id and item.persistent_id is not None:
                data.append(DAAPObject("dmap.persistentid", item.persistent_id))
            if item.name is not None:
                data.append(DAAPObject("dmap.itemname", item.name))
            if item.track is not None:
                data.append(DAAPObject("daap.songtracknumber", item.track))
            if item.artist is not None:
                data.append(DAAPObject("daap.songartist", item.artist))
            if item.album is not None:
                data.append(DAAPObject("daap.songalbum", item.album))
            if item.year is not None:
                data.append(DAAPObject("daap.songyear", item.year))
            if item.bitrate is not None:
                data.append(DAAPObject("daap.songbitrate", item.bitrate))
            if item.duration is not None:
                data.append(DAAPObject("daap.songtime", item.duration))
            if item.file_size is not None:
                data.append(DAAPObject("daap.songsize", item.file_size))
            if item.file_suffix is not None:
                data.append(DAAPObject("daap.songformat", item.file_suffix))
            if provider.supports_artwork and item.album_art:
                data.append(DAAPObject("daap.songartworkcount", 1))
                data.append(DAAPObject("daap.songextradata", 1))

            return DAAPObject("dmap.listingitem", data)

        # Items response
        data = DAAPObject("daap.databasesongs", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", int(is_update)),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(added)),
            DAAPObject("dmap.listing", (
                _item(new[k]) for k in added
            )),
            DAAPObject("dmap.deletedidlisting", (
                DAAPObject("dmap.itemid", k) for k in removed
            ))
        ])

        return ObjectResponse(data)

    @app.route("/databases/<int:database_id>/containers", methods=["GET"])
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_containers(database_id, session_id, revision, delta):
        new, old = provider.get_containers(session_id, database_id, revision, delta)
        added, removed, is_update = utils.diff(new, old)

        # Single container response
        def _container(container):
            data = [
                DAAPObject("dmap.itemid", container.id),
                DAAPObject("dmap.itemname", container.name),
                DAAPObject("dmap.itemcount", len(container.container_items)),
                DAAPObject("dmap.parentcontainerid", container.parent.id if container.parent else 0)
            ]

            if provider.supports_persistent_id and container.persistent_id is not None:
                data.append(DAAPObject("dmap.persistentid", container.persistent_id))
            if container.is_base is not None:
                data.append(DAAPObject("daap.baseplaylist", 1))
            if container.is_smart is not None:
                data.append(DAAPObject("com.apple.itunes.smart-playlist", 1))

            return DAAPObject("dmap.listingitem", data)

        # Containers response
        data = DAAPObject("daap.databaseplaylists", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", int(is_update)),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(added)),
            DAAPObject("dmap.listing", (
                _container(new[k]) for k in added
            )),
            DAAPObject("dmap.deletedidlisting", (
                DAAPObject("dmap.itemid", k) for k in removed
            ))
        ])

        return ObjectResponse(data)

    @app.route("/databases/<int:database_id>/groups", methods=["GET"])
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_groups(database_id, session_id, revision, delta, type):
        raise NotImplemented

    @app.route("/databases/<int:database_id>/containers/<int:container_id>/items", methods=["GET"])
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_container_item(database_id, container_id, session_id, revision, delta, type):
        new, old = provider.get_container_items(session_id, database_id, container_id, revision, delta)
        added, removed, is_update = utils.diff(new, old)

        # Single container response
        def _container_item(container_item):
            item = container_item.item

            data = [
                DAAPObject("dmap.itemkind", 2),
                DAAPObject("dmap.itemid", item.id),
                DAAPObject("dmap.containeritemid", container_item.id),
            ]

            if provider.supports_persistent_id and container_item.persistent_id is not None:
                data.append(DAAPObject("dmap.persistentid", container_item.persistent_id))
            #if item.name:
            #    data.append(DAAPObject("daap.sortname", item.name))
            #if item.album:
            #    data.append(DAAPObject("daap.sortalbum", item.album))
            #if item.artist:
            #    data.append(DAAPObject("daap.sortartist", item.artist))
            #    data.append(DAAPObject("daap.sortalbumartist", item.artist))

            return DAAPObject("dmap.listingitem", data)

        # Containers response
        data = DAAPObject("daap.playlistsongs", [
            DAAPObject("dmap.status", 200),
            DAAPObject("dmap.updatetype", int(is_update)),
            DAAPObject("dmap.specifiedtotalcount", len(new)),
            DAAPObject("dmap.returnedcount", len(added)),
            DAAPObject("dmap.listing", (
                _container_item(new[k]) for k in added
            )),
            DAAPObject("dmap.deletedidlisting", (
                DAAPObject("dmap.itemid", k) for k in removed
            ))
        ])

        return ObjectResponse(data)

    # Return the app
    return app