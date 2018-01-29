[Getting Started](#getting-started) |
[Releases](#releases) |
[Status](#status)

# NeuroAnnotation Toolbox (NAT)

Python module to use the annotations created with
[NeuroCurator](https://github.com/BlueBrain/neurocurator), for example in a
[Jupyter](https://jupyter.org/) notebook.

This framework has been described in details in the following open-access
paper: https://doi.org/10.3389/fninf.2017.00027.

NAT provides the necessary functions and utilities to:
- reliably annotate the neuroscientific literature,
- curate published values for modeling parameters,
- save them in reusable corpora.

---

## Getting Started

**Requirements:**

System side:

- [Git 1.7.0+](https://git-scm.com/downloads)
- [ImageMagick 6](http://docs.wand-py.org/en/latest/guide/install.html)

Python side:

- [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)
- [GitPython](https://gitpython.readthedocs.io)
- [lxml](http://lxml.de)
- [NumPy](http://www.numpy.org)
- [pandas](https://pandas.pydata.org)
- [parse](https://pypi.python.org/pypi/parse)
- [Pyzotero](https://pyzotero.readthedocs.io)
- [quantities](https://python-quantities.readthedocs.io)
- [SciPy](https://www.scipy.org/scipylib/index.html)
- [Wand](http://docs.wand-py.org)

**Installation:**

```bash
pip install nat
```

## Releases

Versions and their notable changes are listed in the
[releases section](https://github.com/BlueBrain/nat/releases/).

Releases are synchronized with the ones of NeuroCurator.

## Status

Created during 2016.

Ongoing stabilization and reengineering in the branch _refactor-architecture_.

The branch _refactor-architecture_ is **not** intended to be used by end-users.

New features, bug fixes and improvements are done on the reengineered code sections.

When a reengineered code section is stable, it's merged into the branch
_master_ and a release is published.
