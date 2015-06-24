from setuptools import setup

import sys

# Make Cython optional
try:
    from Cython.Build import cythonize
except ImportError:
    sys.stderr.write(
        "Error: Cython is not installed. Please install Cython first with"
        "`pip install Cython`.")
    sys.exit(1)

# Detect PyPy and fix dependencies
try:
    import __pypy__ # noqa
    dependency_links = [
        "http://github.com/surfly/gevent/tarball/master#egg=gevent"]
except ImportError:
    dependency_links = []

# Setup definitions
setup(
    name="flask-daapserver",
    version="3.0.0",
    description="DAAP server framework implemented with Flask",
    long_description=open("README.rst").read(),
    author="Bas Stottelaar",
    author_email="basstottelaar@gmail.com",
    packages=["daapserver"],
    package_dir={"daapserver": "daapserver"},
    setup_requires=["nose"],
    dependency_links=dependency_links,
    install_requires=["flask", "zeroconf", "gevent", "enum"],
    platforms=["any"],
    license="MIT",
    url="https://github.com/basilfx/flask-daapserver",
    keywords="daap flask daapserver itunes home sharing streaming",
    zip_safe=False,
    ext_modules=cythonize([
        "daapserver/collection.pyx",
        "daapserver/daap.pyx",
        "daapserver/models.pyx",
        "daapserver/responses.py",
        "daapserver/revision.pyx",
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
