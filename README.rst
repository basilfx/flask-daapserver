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

The DAAP data model consists of the following entities:

-  Server
-  Databases
-  Containers
-  Items
-  Container Items

There are a few more, but the above ones have been implemented.

A server contains databases, a database contains containers and items, a
container contains container items and a container item is a one-to-many
mapping between items and containers. While the DAAP client
implementation of iTunes only supports one database per server (this is
the one that shows up in iTunes), the models does not impose any
restrictions. Therefore, this implementation does not keep you from
adding multiple databases to a server.

The DAAP protocol efficiently updates the entities. Only deltas are send
to the client. For this to work, the server has to add revision
(version) numbers to the entities, and map entities to revisions.
Because several clients can be on different revisions, it is necessary
to keep track of all revisions. When all clients are up to date, the
older revisions can be cleaned.

The DAAP protocol assumes that string are encoded as UTF-8. Therefore,
you are encouraged to use unicode objects where possible.

Mutable versus immutable
~~~~~~~~~~~~~~~~~~~~~~~~

Python is a language that does not implement access modifiers
(private/protected/public). Therefore, an instance variable can be
changed, no matter from where. This makes it harder to implement
immutable types. Cython (which converts Python to C), allows you to add
these modifiers, in some sense.

Support for immutable types was planned, but dropped for the following
reasons:

-  Creating (copy of) objects is expensive, and there are many objects.
-  Cython objects (`Extension
   Types <http://docs.cython.org/src/userguide/extension_types.html>`__)
   should be subclassable in Python, which poses problems with
   modifiers.
-  The DAAP protocol does not care about the object contents. For
   instance, if ``obj_in_v3 is obj_in_v4``, and you change
   ``obj_in_v4.name``, any client that still has to update to revision 3
   will receive the change made in revision 4. This isn't a problem if
   you want to update clients to the latest version.

Do note that this module does not merge objects with the same ID of
different revisions. For instance, the following will fail:

.. code:: python

    db_rev1 = Database(id=1, name="My DB")
    server.databases.add(db_rev1)
    server.databases[1] is db_rev1  # Is True

    db_rev1.items.add(Item(id=1, name="Song 1"))
    db_rev1.items.add(Item(id=2, name="Song 2"))
    db_rev1.items.add(Item(id=3, name="Song 3"))

    db_rev2 = Database(id=2, name="My Updated DB")
    server.databases.add(db_rev2)
    server.databases[1] is db_rev2  # Is True

    len(db_rev1.items) is not len(db_rev2.items)  # Reference to items lost because
                                                  # db_rev1.items was overwritten.

If you want immutability, a correct way is the following:

.. code:: python

    db_rev2 = copy.copy(server.databases[1])
    db_rev2.name = "My DB, version 2"

    db_rev1.items is db_rev2.items  # Is True

The copy can even be skipped if you don't care about actual immutability
and don't mind that intermediate revision will all be the same:

.. code:: python

    db_rev3 = server.databases[1]
    db_rev3.name = "My DB, version 3"

    db_rev1.items is db_rev2.items is db_rev3.items  # Is True
    db_rev2.name == db_rev3.name  # Is True because db_rev3 is not a copy. However,
                                  # the revisioning store will detect this as
                                  # another update.

Installation
------------

Make sure Cython is installed. It is required to boost performance of
some modules significantly.

To install, simply run ``pip install flask-daapserver``. It should
install all dependencies and compile the Cython-based modules. If you
want the latest version, type
``pip install git+https://github.com/basilfx/flask-daapserver``.

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
   'workaround', and now expects the first revision to be committed
   first, e.g. setting up the initial structure first. See the examples
   for more information.
-  Auto-commit of changed has been removed. The user should commit
   manually. The ``daapserver.models.BaseServer`` has a ``commit``
   method that will propagate the commit to all attached databases,
   containers and so forth.
-  The ``added()`` and ``edited()`` methods on
   ``daapserver.models.Collection`` have been replaced by ``updated()``.
   The DAAP protocol does not differ between both.

To give an idea of the performance impact, the ``utils/benchmark.py``
script yielded an improvement of 108MB vs 196MB in memory usage and
0.8375s vs 4.3017s in time (100,000 items, Python 2.7.9, OS X 10.10, 64
Bits).

Running tests
-------------

There are several unit tests included to test core components. The test
suite can be invoked using ``python setup.py nosetests``.

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

-  ``ExampleServer.py`` — Most basic example of a DAAP server.
-  ``RevisionServer.py`` — Demonstration of revisioning capabilities.
-  ``SoundcloudServer.py`` — Soundcloud server that streams all tracks
   of a certain users. Requires a Client ID and the Soundcloud Python
   module.

Contributing
------------

Feel free to submit a pull request. All pull requests must be made
against the ``development`` branch. Python code should follow the PEP-8
conventions and tested (if applicable).

License
-------

See the ``LICENSE`` file (MIT license).

Part of this work (DAAP object encoding) is based on the original work
of Davyd Madeley.

.. |Build Status| image:: https://travis-ci.org/basilfx/flask-daapserver.svg?branch=master
   :target: https://travis-ci.org/basilfx/flask-daapserver
.. |Latest Version| image:: https://pypip.in/version/flask-daapserver/badge.svg
   :target: https://pypi.python.org/pypi/flask-daapserver/
