from Cython.Build import cythonize

from distutils.core import setup

# Setup definitions
setup(
    name="flask_daapserver",
    version="2.0",
    description="DAAP server framework implemented with Flask",
    author="Bas Stottelaar",
    author_email="basstottelaar@gmail.com",
    packages=["daapserver"] ,
    package_dir={"daapserver": "daapserver"} ,
    install_requires=["flask", "pybonjour"],
    license = "MIT",
    keywords = "daap flask daapserver",
    ext_modules = cythonize([
        "daapserver/daap.py",
        "daapserver/structures.py",
        "daapserver/responses.py",
        "daapserver/utils.py"
    ]),
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: System :: Networking",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
    ],
)