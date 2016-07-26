# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 17:16:54 2016

@author: oreilly
"""


import json

from neurocurator.scigraph_client import Vocabulary
from neurocurator.treeData import buildTreeFromRoot


def rebuildTreeFromKS(maxDepth=100, verbose=False, fileName="onto", recompute=True, start=0):
    vocab = Vocabulary()

    categories = vocab.getCategories()
    
    root_ids = []
    for cat in categories:
        catTerms = vocab.findByTerm(cat)
        if catTerms is None:
            continue
        for catTerm in catTerms :
            if catTerm["curie"] is None:
                continue
            root_ids.append(catTerm["curie"])

    # Supplementary tree roots not included in categories
    root_ids.extend(["NIFMOL:nifext_8054", "BFO:0000023", "BIRNOBI:birnlex_11009", "NIFMOL:birnlex_15"])
    sorted(root_ids, key=str.lower)

    for root_no, root_id in enumerate(root_ids):
        
        if root_no >= start:
            tree, termDic = buildTreeFromRoot(root_id, maxDepth, root_no, verbose, fileName, recompute)
            if not tree is None:
                tree.saveTree(fileName)
                with open(fileName + "_" + tree.txt + "_" + str(root_no) + ".dic", 'w') as f:
                    json.dump(termDic, f, sort_keys=True, indent=4, separators=(',', ': '))



import sys
if __name__ == "__main__":
    import codecs
    sys.stdout = codecs.getwriter('utf8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf8')(sys.stderr.detach())
    if len(sys.argv) == 1:
        rebuildTreeFromKS(maxDepth=100, verbose=True, fileName="onto/onto", recompute=False)
    elif len(sys.argv) == 2:
        rebuildTreeFromKS(maxDepth=100, verbose=True, fileName="onto/onto", recompute=False, start=float(sys.argv[1]))
        

