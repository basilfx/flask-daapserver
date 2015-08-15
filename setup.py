from setuptools import setup

import sys

# Check for Cython
try:
    from Cython.Build import cythonize
except ImportError:
    sys.stderr.write(
        "Error: Cython is required, but not installed. Please install Cython "
        "first with `pip install Cython`.")
    sys.exit(1)


# Add code transformer to Cython
from Cython.Compiler import Pipeline, Visitor, ExprNodes, StringEncoding
from daapserver.daap_data import dmap_names, dmap_code_types


class DAAPObjectTransformer(Visitor.CythonTransform):
    """
    Convert all DAAPObject(x, y) into SpeedyDAAPObject(code[x], type[x], y).
    """

    def visit_CallNode(self, node):
        if isinstance(node.function, ExprNodes.NameNode) and \
                node.function.name == u"DAAPObject":

            # Make sure we only convert DAAPObject(x, y) calls, nothing more.
            if len(node.args) == 2:
                code = dmap_names[node.args[0].value]
                itype = dmap_code_types[code][1]

                node.function.name = self.context.intern_ustring(
                    u"SpeedyDAAPObject")
                node.args[0] = ExprNodes.StringNode(
                    node.pos, value=StringEncoding.BytesLiteral(code))
                node.args.insert(1, ExprNodes.IntNode(
                    node.pos, value=str(itype)))

        # Visit method body.
        self.visitchildren(node)

        return node


def new_create_pipeline(context, *args, **kwargs):
    result = old_create_pipeline(context, *args, **kwargs)
    result.insert(1, DAAPObjectTransformer(context))

    return result

old_create_pipeline = Pipeline.create_pipeline
Pipeline.create_pipeline = new_create_pipeline

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
    install_requires=["flask", "zeroconf", "gevent", "enum"],
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
