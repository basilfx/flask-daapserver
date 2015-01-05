from setuptools import setup

import sys

# Make Cython optional
try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = lambda x: None
    sys.stderr.write(
        "Warning: Cython not installed. Slower Python-only alternatives will "
        "be used instead.\n")

# Detect Pypy
try:
    import __pypy__
    dependency_links = [
        "pip install cython git+git://github.com/surfly/gevent.git#egg=gevent"]
except ImportError:
    __pypy__ = None
    dependency_links = []


# Setup definitions
setup(
    name="flask-daapserver",
    version="2.2.0",
    description="DAAP server framework implemented with Flask",
    long_description=open("README.rst").read(),
    author="Bas Stottelaar",
    author_email="basstottelaar@gmail.com",
    packages=["daapserver"],
    package_dir={"daapserver": "daapserver"},
    dependency_links=dependency_links,
    setup_requires=["nose"],
    install_requires=["flask", "zeroconf", "gevent"],
    platforms=["any"],
    license="MIT",
    url="https://github.com/basilfx/flask-daapserver",
    keywords="daap flask daapserver itunes home sharing",
    zip_safe=False,
    ext_modules=cythonize([
        "daapserver/daap.py",
        "daapserver/daap_data.py",
        "daapserver/responses.py",
        "daapserver/revision.py",
        "daapserver/models.py",
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
