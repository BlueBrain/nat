[Getting started](#getting-started) |
[Releases](#releases) |
[Status](#status)

# NeuroAnnotation Toolbox (NAT)

Python package to use the annotations created with [NeuroCurator](https://github.com/BlueBrain/neurocurator), for example in a [Jupyter](https://jupyter.org/) notebook.

This framework has been described in details in the following open-access paper: https://doi.org/10.3389/fninf.2017.00027.

NAT provides the necessary functions and utilities to reliably annotate the neuroscientific literature, curate published values for modeling parameters, and save them in reusable corpora.

---

## Getting started

Install the latest version with:
```
pip install git+https://github.com/BlueBrain/nat
```

Install a specific version with:
```
pip install git+https://github.com/BlueBrain/nat.git@<tag>
```
(ex. '@v0.4.0')

NB: You don't need to install NAT to use a packaged executable of NeuroCurator.

## Releases

In the [dedicated section](https://github.com/BlueBrain/nat/releases/), you can find:
- the latest version,
- the notable changes of each version.

Releases are synchronized with the ones of NeuroCurator.

## Status

Created during 2016.

Ongoing reengineering in the branch _refactor-architecture_.

The branch _refactor-architecture_ is **not** intended to be used by end-users.

New features, bug fixes and improvements are done on the reengineered code sections.

When a reengineered code section is stable, it's merged into the branch _master_ and a release is published.
