from pkg_resources import parse_version
from setuptools import setup

import sys
import imp
import os

# Check for Cython
try:
    from Cython.Build import cythonize

    if parse_version(__import__("cython").__version__) < \
            parse_version("0.23.0"):
        sys.stderr.write(
            "Error: Cython version 0.23.0 or later is required. Upgrade "
            "Cython via `pip install Cython -U`.\n")
        sys.exit(1)
except ImportError:
    sys.stderr.write(
        "Error: Cython is required, but not installed. Please install Cython "
        "first with `pip install Cython`.\n")
    sys.exit(1)

# Install pre-compiler stage. Cannot use normal import because the precompiler
# is a single file that is not in the same directory.
precompiler = imp.load_source("precompiler", os.path.join(
    os.path.dirname(__file__), "utils/transformer.py"))
precompiler.install_new_pipeline()

# Setup definitions
setup(
    name="flask-daapserver",
    version="3.0.2",
    description="DAAP server framework implemented with Flask",
    long_description=open("README.rst").read(),
    author="Bas Stottelaar",
    author_email="basstottelaar@gmail.com",
    packages=["daapserver"],
    package_dir={"daapserver": "daapserver"},
    setup_requires=["nose"],
    install_requires=["flask>=0.10.0", "gevent>=1.1b1", "zeroconf", "enum34"],
    platforms=["any"],
    license="MIT",
    url="https://github.com/basilfx/flask-daapserver",
    keywords="daap flask daapserver itunes home sharing streaming",
    zip_safe=False,
    ext_modules=cythonize([
        "daapserver/daap.pyx",
        "daapserver/revision.pyx",
        "daapserver/collection.pyx",
        "daapserver/models.pyx",
        "daapserver/responses.pyx",
    ]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: System :: Networking",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Cython"
    ]
)
