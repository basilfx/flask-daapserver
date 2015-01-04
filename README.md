# Flask-DAAPServer
DAAP server for streaming media, built around the Flask micro framework.

## Installation
Make sure Cython is installed. While not required, it can boost performance of some modules significantly.

To install, simply run `pip install git+https://github.com/basilfx/flask-daapserver`. It should install all dependencies.

## Examples
There are three examples included in the `examples/` directory.

* `Benchmark.py` &mdash; Benchmark revision tree speed and memory usage.
* `ExampleServer.py` &mdash; Most basic example of a DAAP server.
* `RevisionServer.py` &mdash; Demonstration of revisioning capabilities.

## License
See the `LICENSE` file (MIT license).

Part of this work (DAAP rendering) is based on the original work of Davyd Madeley.