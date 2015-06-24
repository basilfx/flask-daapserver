Flask-DAAPServer
================

DAAP server for streaming media, built around the Flask micro framework.
Supports iTunes, artwork and revisioning.

|Build Status| |Latest Version|

Introduction.
-------------

The Digital Audio Access Protocol (DAAP) is a protocol designed by Apple
to share media over the network, using HTTP as transport layer. It
advertises itself via Bonjour/Zeroconf.

This Python module implements the full stack, providing a HTTP server
(built around Flask), a high-level application layer and
Bonjour/Zeroconf advertising.

Data model
----------

DAAP uses an easy data model. The basic model consists of the following
entities.

-  Server
-  Databases
-  Containers
-  Items
-  Container Items

A server contains databases, a database contains containers and items, a
container contains container items and a container item is a one-to-many
mapping between items and containers. While the DAAP client
implementation of iTunes only supports one database per server, the
protocol does not have any limitations. Therefore, this implementation
does not limit you to add multiple databases.

If applicable to the client, data can be revisioned. Only changes are
shared between server and client, happening in real time. Because
several clients can be on different revisions, it's neccessary to keep
track of all changes to the data model. This is done by a so-called tree
revision storage. When all clients are up to date, the older revisions
can be removed.

The data model entities are implemented by classes. Parents do not share
any reference to their children, but they can access to their hildren by
IDs (e.g. ``parent.child_id`` versus ``parent.child``).

Installation
------------

Make sure Cython is installed. It is required to boost performance of
some modules significantly.

To install, simply run ``pip install flask-daapser``. It should install
all dependencies and compile the Cython-based modules. If you want the
latest version, type
``pip install git+https://github.com/basilfx/flask-daapserver``.

PyPy 2.4 or later is supported. While all tests pass and examples work,
it should be considered experimental.

Upgrade notice
~~~~~~~~~~~~~~

The revisioning storage API has changed between version v2.3.0 and
v3.0.0. Due to the large overhead of revisioning, it was decided that
there should be less memory usage and faster access. While the API has
remained similar, a few changes have been made:

-  Cython is required now.
-  The global object store has been removed. Every container now has its
   own store for its children. Therefore, it is very important to add
   objects in the right order. For instance, do not add a item to a
   database before adding the database to the server (the models do not
   offer advanced ORM functionality).
-  The previous version fixed compatibility with iTunes 12.1. For some
   reason, iTunes expected the first revision to be two. The fix simply
   included to start revisions from 2. This version removed this
   'workaround', and now expects the first revision to be commited
   first, e.g. setting up the initial structure first. See the examples
   for more information.
-  Auto-commit has been removed. The user should commit manually. The
   ``daapserver.models.BaseServer`` has a ``commit`` method that will
   propagate the commit to all attached databases, containers and so
   forth.
-  The ``added()`` and ``edited()`` methods on
   ``daapserver.models.Collection`` have been replaced by ``updated()``.
   The DAAP protocol does not differ between both.

To give an idea of the performance impact, the ``Benchmark.py`` script
yielded an improvement of 108MB vs 196MB in memory usage and 0.8375s vs
4.3017s in time (100,000 items, Python 2.7.9, OS X 10.10, 64 Bits).

Experimental
~~~~~~~~~~~~

The script ``utils/transform.py`` can rewrite Python source code to make
it more efficient at the expense of readability. It rewrites the
following functions:

-  ``DAAPObject(x, y)`` into ``SpeedyDAAPObject(code[x], type[x], y)``.
   Saves two dictionary lookups and simplifies instantiation. However,
   it bypasses (type) checking.

To run this script, run
``python utils/transform.py <input_file> <output_file>``, e.g.
``python utils/transform.py daapserver/response.py daapserver/response_out.py``.

Usage
-----

Take a look at the examples, or to the projects using Flask-DAAPServer:

-  `SubDaap <https://github.com/basilfx/SubDaap>`__ — Bridge between
   SubSonic and iTunes.

Examples
--------

There are four examples included in the ``examples/`` directory. You can
run them with ``python examples/<filename>``. Check the source for more
information and the details.

-  ``Benchmark.py`` — Benchmark revision tree speed and memory usage.
-  ``ExampleServer.py`` — Most basic example of a DAAP server.
-  ``RevisionServer.py`` — Demonstration of revisioning capabilities.
-  ``SoundcloudServer.py`` — Soundcloud server that streams all tracks
   of a certain users. Requires a Client ID and the Soundcloud Python
   module.

License
-------

See the ``LICENSE`` file (MIT license).

Part of this work (DAAP object encoding) is based on the original work
of Davyd Madeley.

.. |Build Status| image:: https://travis-ci.org/basilfx/flask-daapserver.svg?branch=master
   :target: https://travis-ci.org/basilfx/flask-daapserver
.. |Latest Version| image:: https://pypip.in/version/flask-daapserver/badge.svg
   :target: https://pypi.python.org/pypi/flask-daapserver/
