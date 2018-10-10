[Getting Started](#getting-started) |
[Releases](#releases) |
[Examples of use](#examples-of-use) |
[Status](#status)

# NeuroAnnotation Toolbox - Analytics (nat-analytics)

Python module to use the annotations created with
[NeuroCurator](https://github.com/BlueBrain/neurocurator), for example in a
[Jupyter](https://jupyter.org/) notebook. Whereas NAT contains the core 
functionalities required for this annotation framework, nat-analytics 
contains more high-level features useful for data analysis. 

This framework has been described in details in the following open-access
paper: https://doi.org/10.3389/fninf.2017.00027.

---

## Getting Started

**Requirements:**

Python side:

- [NumPy](http://www.numpy.org)
- [quantities](https://python-quantities.readthedocs.io)
- [matplotlib](https://matplotlib.org/)
- [nat](https://github.com/BlueBrain/nat)

**Installation:**

```bash
pip install https://github.com/BlueBrain/nat.git@nat-analytics
```

## Examples of use

A series of Jupyter notebooks has been prepared to demonstrate some use-cases for analysis of corpora of annotations using nat-core and nat-analytics. Here are some notebooks demonstrating how to interact with an annotation corpus:
- [Showing some raw information about a corpus](https://github.com/BlueBrain/nat/blob/nat-analytics/notebooks/Status_thalamus_corpus.ipynb) (nat-core)
- [Basic formatting and homogenization of a corpus of annotated parameters](https://github.com/BlueBrain/nat/blob/nat-analytics/notebooks/ThalamusStereology.ipynb) (nat-core)
- [Example with ion current conductances](https://github.com/BlueBrain/nat/blob/nat-analytics/notebooks/Example_ionic_currents.ipynb) (nat-core)
- [Statistical analysis of curated parameter values](https://github.com/BlueBrain/nat/blob/nat-analytics/notebooks/Analysis_conductances.ipynb) (nat-core)
- [Aggregating data from an annotation corpus](https://github.com/BlueBrain/nat/blob/nat-analytics/notebooks/brain_cell_densities_aggregation.ipynb) (nat-analytics, nat-core)
- [Example of how annotated values can be integrated in Notebook documentation](https://github.com/BlueBrain/nat/blob/nat-analytics/notebooks/integrationOfAnnotationsInMarkdown.ipynb) (nat-core)

Some other notebooks for specific functionalities:
- [Displaying the tree of modeling parameter types](https://github.com/BlueBrain/nat/blob/nat-analytics/notebooks/parameterTree.ipynb) (nat-core)
- [Computed similarity index between versus within documents](https://github.com/BlueBrain/nat/blob/nat-analytics/notebooks/Check_text_pdf_similarity.ipynb) (nat-core)

## Releases [TO BE REVISED]

Versions and their notable changes are listed in the
[releases section](https://github.com/BlueBrain/nat/releases/).

Releases are synchronized with the ones of NeuroCurator.

## Status

Created during 2016.

NAT-analytics is currently coded as branch from NAT, but will be forked as a separate repository down the line.
