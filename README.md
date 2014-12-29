# Flask-DAAPServer
DAAP server for streaming media, built around the Flask micro framework.

## Installation
First install dependencies:
* `pip install git+https://github.com/basilfx/pybonjour-python3`
* `pip install gevent` (for Pypy: `pip install git+https://github.com/surfly/gevent`)
* `pip install flask`

Then Flask-DAAPServer:
* `pip install git+https://github.com/basilfx/flask-daapserver`

## Examples
There are three examples included in the `examples/` directory.

* `Benchmark.py` &mdash; Benchmark revision tree speed and memory usage
* `ExampleServer.py` &mdash; Most basic example of a DAAP server
* `RevisionServer.py` &mdash; Demonstration of revisioning capabilities

## License
See the `LICENSE` file (MIT license).

Part of this work (DAAP rendering) is based on the original work of Davyd Madeley.