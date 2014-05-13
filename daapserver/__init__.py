from daapserver.daap import do
from daapserver import daap

from flask import Flask, Response, request, send_file
from werkzeug.contrib.cache import SimpleCache

from functools import wraps

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

def create_daap_server(provider, server_name, password=None, cache=True):
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
    app.debug = True

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
        arguments. Since the query string keys are defined, values will be converted
        to their approriate format. An exception will be thrown in case a requested
        argument is not available, or if the value could not be converted.
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
        """

        @wraps(func)
        def _inner(*args, **kwargs):
            # Quick-and-dirty request hash, but it works. It's faster than
            # string joining of parameters, outweighing the risk on collisions.
            hash_value = 0

            for k,v in request.args.iteritems():
                if k not in QS_IGNORE_CACHE:
                    hash_value ^= hash(v)

            # Hit the cache
            key = hash(func.__name__), hash(request.path), hash_value
            value = cache.get(key)

            if value is None:
                value = func(*args, **kwargs)
                cache.set(key, value, timeout=1800)
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
        data = do("dmap.serverinforesponse", [
            do("dmap.status", 200),
            do("dmap.protocolversion", "2.0.0"),
            do("daap.protocolversion", "3.0.0"),
            do("dmap.itemname", server_name),
            do("dmap.timeoutinterval", 1800),
            do("dmap.supportsautologout", 1),
            do("dmap.loginrequired", 1 if password else 0),
            do("dmap.authenticationmethod", 2 if password else 0),
            do("dmap.supportsextensions", 1),
            do("dmap.supportsindex", 1),
            do("dmap.supportsbrowse", 1),
            do("dmap.supportsquery", 1),
            do("dmap.supportspersistentids", 1),
            do("dmap.databasescount", 1),
            do("dmap.supportsupdate", 1),
            do("dmap.supportsresolve", 1)
        ])

        return ObjectResponse(data)

    @app.route("/content-codes", methods=["GET"])
    @daap_cache_response
    def content_codes():
        children = [ do("dmap.status", 200) ]
        data = do("dmap.contentcodesresponse", children)

        for code in daap.dmapCodeTypes.keys():
            name, dtype = daap.dmapCodeTypes[code]

            children.append(
                do("dmap.dictionary", [
                    do("dmap.contentcodesnumber", code),
                    do("dmap.contentcodesname", name),
                    do("dmap.contentcodestype", daap.dmapReverseDataTypes[dtype])
                ])
            )

        return ObjectResponse(data)

    @app.route("/login", methods=["GET"])
    @daap_authenticate
    def login():
        session_id = provider.create_session()

        data = do("dmap.loginresponse",[
            do("dmap.status", 200),
            do("dmap.sessionid", session_id)
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
        return Response(None, status=204)

    @app.route("/update", methods=["GET"])
    @daap_authenticate
    @daap_unpack_args
    def update(session_id, revision, delta):
        revision = provider.get_revision(session_id, revision, delta)

        data = do("dmap.updateresponse", [
            do("dmap.status", 200),
            do("dmap.serverrevision", revision),
        ])

        return ObjectResponse(data)

    @app.route("/fp-setup", methods=["POST"])
    @daap_authenticate
    def fp_setup():
        """
        Fairplay validation, as sent by iTunes 11+.
        """

        raise NotImplemented

    @app.route("/databases", methods=["GET"])
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def databases(session_id, revision, delta):
        data = provider.get_databases(session_id, revision, delta)

        return ObjectResponse(data)

    @app.route("/databases/<int:database_id>/items/<int:item_id>/extra_data/artwork", methods=["GET"])
    @daap_unpack_args
    def database_item_artwork(database_id, item_id, session_id, revision, delta):
        # Return JPEG
        pass

    @app.route("/databases/<int:database_id>/groups/<int:group_id>/extra_data/artwork", methods=["GET"])
    @daap_unpack_args
    def database_group_artwork(database_id, group_id, session_id, revision, delta):
        raise NotImplemented

    @app.route("/databases/<int:database_id>/items/<int:item_id>.<suffix>", methods=["GET"])
    @daap_unpack_args
    def database_item(database_id, item_id, suffix, session_id, revision, delta):
        range_header = request.headers.get("Range", None)

        if not range_header:
            # No partial header
            data, mimetype, size, content_length = provider.get_item(session_id, database_id, item_id)

            response = send_file(data, mimetype=mimetype)
            response.headers["Content-Length"] = content_length
        else:
            # Server wants partial file, extract range
            values = re.search(r"(\d+)-(\d*)", range_header)
            begin, end = [ int(value) if value else None for value in values.groups() ]

            data, mimetype, size, content_length = provider.get_item(session_id, database_id, item_id, begin=begin, end=end)

            response = Response(data, 206, mimetype=mimetype, direct_passthrough=True)
            response.headers["Content-Range"] = "bytes %d-%d/%d" % (begin, begin - content_length - 1, size)

        return response

    @app.route("/databases/<int:database_id>/items", methods=["GET"])
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_items(database_id, session_id, revision, delta, type):
        data = provider.get_items(session_id, database_id, revision, delta)

        return ObjectResponse(data)

    @app.route("/databases/<int:database_id>/containers", methods=["GET"])
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_containers(database_id, session_id, revision, delta):
        data = provider.get_containers(session_id, database_id, revision, delta)

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
        data = provider.get_container_items(session_id, database_id, container_id, revision, delta)

        return ObjectResponse(data)

    # Return the app
    return app