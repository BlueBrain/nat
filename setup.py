__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

import os

from setuptools import setup

VERSION = "0.4.4"

HERE = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file.
with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="nat-server",
    version=VERSION,
    # FIXME
    description="Module to pawn the NAT REST server.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="neuroscience annotation curation literature modeling parameters",
    url="https://github.com/BlueBrain/nat/tree/nat-server",
    author="Christian O'Reilly, Pierre-Alexandre Fonta",
    author_email="christian.oreilly@epfl.ch, pierre-alexandre.fonta@epfl.ch",
    # NB: 'If maintainer is provided, distutils lists it as the author in PKG-INFO'.
    # https://docs.python.org/3/distutils/setupscript.html#meta-data
    # maintainer="Pierre-Alexandre Fonta",
    # maintainer_email="pierre-alexandre@epfl.ch",
    license="GPLv3",
    packages=["nat-server"],
    # FIXME
    python_requires=">=3.4",
    # FIXME
    install_requires=[
        "nat",
        "flask",
        "PyPDF2"
    ],
    data_files=[("", ["LICENSE.txt"])],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: Free for non-commercial use",
        # FIXME
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: English"
    ]
)
