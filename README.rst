Flask-DAAPServer
================

DAAP server for streaming media, built around the Flask micro framework.
Supports iTunes, artwork and revisioning.

|Build Status|

Introduction.
-------------

The Digital Audio Access Protocol (DAAP) is a protocol designed by Apple
to share media over the network, using HTTP as transport layer. It
advertises servers via Bonjour/Zeroconf over the network.

This Python module implements the full stack, by providing a HTTP server
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

The data model entities are implemented by classes. Objects don't have
references to children, but they have access to their IDs (e.g.
``parent.child_id`` versus ``parent.child``).

Installation
------------

Make sure Cython is installed. While not required, it can boost
performance of some modules significantly.

To install, simply run
``pip install git+https://github.com/basilfx/flask-daapserver``. It
should install all dependencies.

Usage
-----

Take a look at the examples, or to the projects using Flask-DAAPServer:

-  `SubDaap <https://github.com/basilfx/SubDaap>`__ — Bridge between
   SubSonic and iTunes.

Examples
--------

There are three examples included in the ``examples/`` directory. You
can run them with ``python <filename>``.

-  ``Benchmark.py`` — Benchmark revision tree speed and memory usage.
-  ``ExampleServer.py`` — Most basic example of a DAAP server.
-  ``RevisionServer.py`` — Demonstration of revisioning capabilities.

License
-------

See the ``LICENSE`` file (MIT license).

Part of this work (DAAP rendering) is based on the original work of
Davyd Madeley.

.. |Build Status| image:: https://travis-ci.org/basilfx/flask-daapserver.svg?branch=master
   :target: https://travis-ci.org/basilfx/flask-daapserver
