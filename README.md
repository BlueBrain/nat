[Getting Started](#getting-started) |
[Upgrade](#upgrade) |
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

### Installation

After having **installed the [requirements](#requirements)**:

```bash
pip3 install nat
```

**Before**, you might want to create a dedicated environment with `conda`:

```bash
conda create --name nat_env python=3.7
conda activate nat_env
```

#### Requirements

- [Python 3.5+](https://www.python.org/downloads/)
- [Git 1.7.0+](https://git-scm.com/downloads) (GitPython)
- [Miniconda](https://conda.io/miniconda.html) (optional)

#### Python dependencies

- [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)
- [GitPython](https://gitpython.readthedocs.io)
- [lxml](http://lxml.de)
- [NumPy](http://www.numpy.org)
- [pandas](https://pandas.pydata.org)
- [parse](https://pypi.python.org/pypi/parse)
- [dateutils](https://dateutil.readthedocs.io)
- [Pyzotero](https://pyzotero.readthedocs.io)
- [quantities](https://python-quantities.readthedocs.io)
- [requests](http://docs.python-requests.org)
- [SciPy](https://www.scipy.org/scipylib/)

## Upgrade

```bash
pip3 install --upgrade nat
```

If you have used `conda`, activate the environment before:

```bash
conda activate nat_env
```

## Releases

Versions and their notable changes are listed in the [releases section](
https://github.com/BlueBrain/nat/releases/).

## Status

Created during 2016.

Ongoing stabilization and reengineering in the branch _refactor-architecture_.

The branch _refactor-architecture_ is **not** intended to be used by end-users.

New features, bug fixes and improvements are done on the reengineered code sections.

When a reengineered code section is stable, it's merged into the branch
_master_ and a release is published.
