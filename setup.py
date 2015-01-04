from Cython.Build import cythonize

from distutils.core import setup

# Setup definitions
setup(
    name="flask_daapserver",
    version="2.2.0",
    description="DAAP server framework implemented with Flask",
    author="Bas Stottelaar",
    author_email="basstottelaar@gmail.com",
    packages=["daapserver"] ,
    package_dir={"daapserver": "daapserver"} ,
    install_requires=["cython", "flask", "zeroconf"],
    license = "MIT",
    keywords = "daap flask daapserver itunes home sharing",
    ext_modules = cythonize([
        "daapserver/daap.py",
        "daapserver/daap_data.py",
        "daapserver/responses.py",
        "daapserver/revision.py",
        "daapserver/models.py",
    ]),
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: System :: Networking",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
    ],
)