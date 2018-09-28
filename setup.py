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
    name="nat",
    version=VERSION,
    description="Module to use the annotations created with NeuroCurator.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="neuroscience annotation curation literature modeling parameters",
    url="https://github.com/BlueBrain/nat",
    author="Christian O'Reilly, Pierre-Alexandre Fonta",
    author_email="christian.oreilly@epfl.ch, pierre-alexandre.fonta@epfl.ch",
    # NB: 'If maintainer is provided, distutils lists it as the author in PKG-INFO'.
    # https://docs.python.org/3/distutils/setupscript.html#meta-data
    # maintainer="Pierre-Alexandre Fonta",
    # maintainer_email="pierre-alexandre@epfl.ch",
    license="GPLv3",
    packages=["nat"],
    python_requires=">=3.5",  # Package pandas requires Python 3.5+.
    install_requires=[
        "beautifulsoup4",  # Imported as 'bs4'.
        "gitpython",  # Imported as 'git'.
        "lxml",  # Used with BeautifulSoup4.
        "numpy",
        "pandas",
        "parse",
        "python-dateutil",
        "pyzotero",
        "quantities",
        "requests",
        "scipy",
    ],
    extras_require={
        "test": ["pytest", "pytest-cov", "pytest-lazy-fixture", "pytest-mock"],
    },
    package_data={
        "nat": ["data/*.csv"],
    },
    data_files=[("", ["LICENSE.txt"])],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: Free for non-commercial use",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5'",
        "Programming Language :: Python :: 3.6'",
        "Programming Language :: Python :: 3.7'",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: English",
    ]
)
