# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 17:16:54 2016

@author: oreilly
"""

import os, json

from neurocurator.scigraph_client import Vocabulary, Graph
from neurocurator.treeData import TreeData


def rebuildTreeFromKS(maxDepth=100, verbose=False, fileName="onto", recompute=True, start=0):
    vocab = Vocabulary()
    graph = Graph()            

    def addSubtree(root, depth=0): 
        if depth+1 < maxDepth:
            if root is None:
                return
            neighbors = graph.getNeighbors(root.id, relationshipType="subClassOf", direction="INCOMING")
            if neighbors is None:
                nodes = []
            else:
                nodes = neighbors["nodes"]
            for node in nodes:
                nodeLabel = node["lbl"]
                nodeId    = node["id"]
                
                if root.id == nodeId:
                    continue

                if nodeLabel is None:
                    continue
                
                child = TreeData(nodeLabel, nodeId, root)            
                termDic[nodeId] = nodeLabel
                if verbose:
                    print(" "*(depth+1) + nodeLabel)
                addSubtree(child, depth+1)
                root.children.append(child)


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
            termDic = {}            
            root = vocab.findById(root_id)
            if root is None:
                print("Skipping " + str(root_no))
                continue
            if root["labels"] is None:
                print("Skipping " + str(root_no))
                continue
            neighbors = graph.getNeighbors(root_id, relationshipType="subClassOf", direction="INCOMING")    
            if neighbors is None:
                print("Skipping " + str(root_no))
                continue
            if len(neighbors["nodes"]) == 1:
                print("Skipping " + str(root_no))
                continue
            
            root_name = root["labels"][0]
            if not recompute:
                if (os.path.isfile(fileName + "_" + root_name + "_" + str(root_no) + ".tree") and
                    os.path.isfile(fileName + "_" + root_name + "_" + str(root_no) + ".dic")) :
                    print("Skipping " + fileName + "_" + root_name + "_" + str(root_no))
                    continue
                
            if verbose:
                print(root_name)
            root = TreeData(root_name, root_id, root_no=root_no)            
            termDic[root_id] = root_name
            addSubtree(root)

            root.saveTree(fileName)
            with open(fileName + "_" + root_name + "_" + str(root_no) + ".dic", 'w') as f:
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
        

