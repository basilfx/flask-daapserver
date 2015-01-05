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

# Detect PyPy and fix dependencies
try:
    import __pypy__ # noqa
    dependency_links = ["git+git://github.com/surfly/gevent.git#egg=gevent"]
    install_requires = ["flask", "zeroconf"]
except ImportError:
    dependency_links = []
    install_requires = ["flask", "zeroconf", "gevent"]


# Setup definitions
setup(
    name="flask-daapserver",
    version="2.2.1",
    description="DAAP server framework implemented with Flask",
    long_description=open("README.rst").read(),
    author="Bas Stottelaar",
    author_email="basstottelaar@gmail.com",
    packages=["daapserver"],
    package_dir={"daapserver": "daapserver"},
    setup_requires=["nose"],
    dependency_links=dependency_links,
    install_requires=install_requires,
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
