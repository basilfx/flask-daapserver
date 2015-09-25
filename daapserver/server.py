from daapserver import responses, utils

from flask import Flask, Response, request
from werkzeug.contrib.cache import SimpleCache
from werkzeug import http

from functools import wraps

import hashlib
import inspect
import logging
import time

# Logger instance
logger = logging.getLogger(__name__)

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
# daap_cache. This makes sure that identical requests from different sessions
# will yield from cache.
QS_IGNORE_CACHE = [
    "session-id",
]


class ObjectResponse(Response):
    """
    DAAP object response. Encodes a DAAPObject to raw bytes and sets the
    content type.
    """

    def __init__(self, data, *args, **kwargs):
        # Set DAAP content type
        kwargs["mimetype"] = "application/x-dmap-tagged"

        # Instantiate response
        super(ObjectResponse, self).__init__(data.encode(), *args, **kwargs)


def create_server_app(provider, password=None, cache=True, cache_timeout=3600,
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
    app = Flask(__name__, static_folder=None)
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
            if environment["PATH_INFO"].startswith("daap://") or \
                    environment["PATH_INFO"].startswith("http://"):
                environment["PATH_INFO"] = "/" + \
                    environment["PATH_INFO"].split("/", 3)[3]
            return func(environment, start_response)
        return _inner
    app.wsgi_app = daap_wsgi_app(app.wsgi_app)

    def daap_trace(func):
        """
        Utility method for tracing function calls. Helps debugging malicious
        requests (e.g. protocol changes). Is only enabled when `debug` is True.
        Normally, exceptions are caught by Flask and handled as Bad Requests.
        Any debugging is therefore lost.
        """

        # Do not apply when debug is False.
        if not debug:
            return func

        @wraps(func)
        def _inner(*args, **kwargs):
            try:
                start = time.time()
                result = func(*args, **kwargs)
                logger.debug(
                    "Request handling took %.6f seconds",
                    time.time() - start)

                return result
            except:
                logger.exception(
                    "Caught exception before raising it to Flask.")
                raise

        return _inner

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
        mappings = [mapping for mapping in QS_MAPPING if mapping[1] in args]

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

        # Do not apply when no password is set
        if not password:
            return func

        @wraps(func)
        def _inner(*args, **kwargs):
            auth = request.authorization

            if not auth or not auth.password == password:
                return Response(None, 401, {
                    "WWW-Authenticate": "Basic realm=\"%s\"" %
                    provider.server.name})
            return func(*args, **kwargs)
        return _inner
    app.authenticate = daap_authenticate

    def daap_cache_response(func):
        """
        Cache object responses if the cache has been initialized. The cache key
        is based on the request path and the semi-constant request arguments.
        The response is caches for as long as possible, which should not be a
        problem if the cache is cleared if the provider has new data.
        """

        # Do not apply when cache is False.
        if not cache:
            return func

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
                cache.set(key, value, timeout=cache_timeout)
            elif debug:
                logger.debug("Loaded response from cache.")
            return value
        return _inner

    #
    # Request handlers
    #

    @app.after_request
    def after_request(response):
        """
        Append default response headers, independent of the return type.
        """

        response.headers["DAAP-Server"] = provider.server.name
        response.headers["Content-Language"] = "en_us"
        response.headers["Accept-Ranges"] = "bytes"

        return response

    @app.route("/server-info", methods=["GET"])
    @daap_trace
    @daap_cache_response
    def server_info():
        """
        """

        data = responses.server_info(provider, provider.server.name, password)

        return ObjectResponse(data)

    @app.route("/content-codes", methods=["GET"])
    @daap_trace
    @daap_cache_response
    def content_codes():
        """
        """

        data = responses.content_codes(provider)

        return ObjectResponse(data)

    @app.route("/login", methods=["GET"])
    @daap_trace
    @daap_authenticate
    def login():
        """
        """

        session_id = provider.create_session(
            user_agent=request.headers.get("User-Agent"),
            remote_address=request.remote_addr,
            client_version=request.headers.get(
                "Client-DAAP-Version"))
        data = responses.login(provider, session_id)

        return ObjectResponse(data)

    @app.route("/logout", methods=["GET"])
    @daap_trace
    @daap_authenticate
    @daap_unpack_args
    def logout(session_id):
        """
        """

        provider.destroy_session(session_id)

        return Response(None, status=204)

    @app.route("/activity", methods=["GET"])
    @daap_trace
    @daap_authenticate
    @daap_unpack_args
    def activity(session_id):
        """
        """

        return Response(None, status=200)

    @app.route("/update", methods=["GET"])
    @daap_trace
    @daap_authenticate
    @daap_unpack_args
    def update(session_id, revision, delta):
        """
        """

        revision = provider.get_next_revision(session_id, revision, delta)

        data = responses.update(provider, revision)

        return ObjectResponse(data)

    @app.route("/fp-setup", methods=["POST"])
    @daap_trace
    @daap_authenticate
    def fp_setup():
        """
        Fairplay validation, as sent by iTunes 11+. It will be unlikely this
        will be ever implemented.
        """

        raise NotImplementedError("Fairplay not supported.")

    @app.route("/databases", methods=["GET"])
    @daap_trace
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def databases(session_id, revision, delta):
        """
        """

        new, old = provider.get_databases(session_id, revision, delta)
        added, removed, is_update = utils.diff(new, old)

        data = responses.databases(
            provider, new, old, added, removed, is_update)

        return ObjectResponse(data)

    @app.route(
        "/databases/<int:database_id>/items/<int:item_id>/extra_data/artwork",
        methods=["GET"])
    @daap_trace
    @daap_unpack_args
    def database_item_artwork(database_id, item_id, session_id):
        """
        """

        data, mimetype, total_length = provider.get_artwork(
            session_id, database_id, item_id)

        # Setup response
        response = Response(
            data, 200, mimetype=mimetype,
            direct_passthrough=not isinstance(data, basestring))

        if total_length:
            response.headers["Content-Length"] = total_length

        return response

    @app.route(
        "/databases/<int:database_id>/groups/<int:group_id>/extra_data/"
        "artwork", methods=["GET"])
    @daap_trace
    @daap_unpack_args
    def database_group_artwork(database_id, group_id, session_id, revision,
                               delta):
        """
        """
        raise NotImplemented("Groups not supported.")

    @app.route(
        "/databases/<int:database_id>/items/<int:item_id>.<suffix>",
        methods=["GET"])
    @daap_trace
    @daap_unpack_args
    def database_item(database_id, item_id, suffix, session_id):
        """
        """

        range_header = request.headers.get("Range", None)

        if range_header:
            begin, end = http.parse_range_header(range_header).ranges[0]
            data, mimetype, total_length = provider.get_item(
                session_id, database_id, item_id, byte_range=(begin, end))
            begin, end = (begin or 0), (end or total_length)

            # Setup response
            response = Response(
                data, 206, mimetype=mimetype,
                direct_passthrough=not isinstance(data, basestring))

            # A streaming response with unknown content lenght, Range x-*
            # as per RFC2616 section 14.16
            if total_length <= 0:
                response.headers["Content-Range"] = "bytes %d-%d/*" % (
                    begin, end - 1)
            elif total_length > 0:
                response.headers["Content-Range"] = "bytes %d-%d/%d" % (
                    begin, end - 1, total_length)
                response.headers["Content-Length"] = end - begin
        else:
            data, mimetype, total_length = provider.get_item(
                session_id, database_id, item_id)

            # Setup response
            response = Response(
                data, 200, mimetype=mimetype,
                direct_passthrough=not isinstance(data, basestring))

            if total_length > 0:
                response.headers["Content-Length"] = total_length

        return response

    @app.route("/databases/<int:database_id>/items", methods=["GET"])
    @daap_trace
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_items(database_id, session_id, revision, delta, type):
        """
        """

        new, old = provider.get_items(session_id, database_id, revision, delta)
        added, removed, is_update = utils.diff(new, old)

        data = responses.items(provider, new, old, added, removed, is_update)

        return ObjectResponse(data)

    @app.route("/databases/<int:database_id>/containers", methods=["GET"])
    @daap_trace
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_containers(database_id, session_id, revision, delta):
        """
        """

        new, old = provider.get_containers(
            session_id, database_id, revision, delta)
        added, removed, is_update = utils.diff(new, old)

        data = responses.containers(
            provider, new, old, added, removed, is_update)

        return ObjectResponse(data)

    @app.route("/databases/<int:database_id>/groups", methods=["GET"])
    @daap_trace
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_groups(database_id, session_id, revision, delta, type):
        """
        """
        raise NotImplementedError("Groups not supported.")

    @app.route(
        "/databases/<int:database_id>/containers/<int:container_id>/items",
        methods=["GET"])
    @daap_trace
    @daap_authenticate
    @daap_cache_response
    @daap_unpack_args
    def database_container_item(database_id, container_id, session_id,
                                revision, delta):
        """
        """

        new, old = provider.get_container_items(
            session_id, database_id, container_id, revision, delta)
        added, removed, is_update = utils.diff(new, old)

        data = responses.container_items(
            provider, new, old, added, removed, is_update)

        return ObjectResponse(data)

    # Return the app
    return app
