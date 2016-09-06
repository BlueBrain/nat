#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'


from .tagUtilities import nlx2ks
from .tag import RequiredTag
from .modelingParameter import ParameterTypeTree
from .scigraph_client import Graph
from .ontoDic import OntoDic
import requests

import os
import pandas as pd
import numpy as np


def flatten_list(l):
    return [item for sublist in l for item in sublist]


def getChildrens(root_id, maxDepth=100, relationshipType="subClassOf"):
    #graph = Graph()            

    if root_id in nlx2ks:
        root_id = nlx2ks[root_id]

    direction="INCOMING"
    #neighbors = graph.getNeighbors(root_id, depth=maxDepth, 
    #                               relationshipType=relationshipType, 
    #                               direction=direction)
                                   
                                   

    baseKS  = "http://matrix.neuinfo.org:9000"
    response = requests.get(baseKS + "/scigraph/graph/neighbors/" + 
                            root_id + "?direction=" + direction + 
                            "&depth=" + str(maxDepth) + 
                            "&project=%2A&blankNodes=false&relationshipType=" 
                            + relationshipType)
    neighbors = response.json()

    if neighbors is None:
        return {}

    nodes = neighbors["nodes"]
    return OntoDic({node["id"]:node["lbl"] for node in np.array(nodes)})
    
    

def addSuppTerms(dic):
    
    idsToAdd = {"NIFINV:birnlex_2300"   :"Computational model", 
                "GO:0030431"            :"sleep", 
                "NIFMOL:sao1797800540"  :"Sodium Channel",
                "NIFMOL:sao1846985919"  :"Calcium Channel", 
                "NIFGA:nlx_anat_1010"   :"Afferent role", 
                "NIFCELL:nifext_156"    :"Hippocampal pyramidal cell",
                "NIFMOL:sao940366596"   :"Ion Channel"}

    dic.update(idsToAdd)
    
    # These terms were in Neurolex but have not been ported to KS.
    orphanTerms = {"nlx_78803":"Burst Firing Pattern", 
                   "nlx_52865":"Modelling",
                   "nlx_152236":"Electron microscopy immunolabeling protocol"}
    dic.update(orphanTerms)
    
    return dic
    


def appendAdditions(treeData, dicData):
    csvFileName = os.path.join(os.path.dirname(__file__), './additionsToOntologies.csv')

    df = pd.read_csv(csvFileName, skip_blank_lines=True, comment="#", 
                     delimiter=";", names=["id", "label", "definition", "superCategory", "synonyms"])
    for index, row in df.iterrows():
        if not row["id"] in dicData:
            dicData[row["id"]] = row["label"]

        if isinstance(row["superCategory"], str):         
            for rootId, childrens in treeData.items():
                if row["superCategory"] == rootId or row["superCategory"] in childrens:
                    childrens[row["id"]] = row["label"]
    return treeData, dicData


def appendReqTagTrees(treeData, dicData):
    df = ParameterTypeTree.getParamTypeDF()
    
    reqTagRoots = np.unique(np.concatenate([list(eval(reqTags).keys()) for reqTags in df["requiredTags"] if len(eval(reqTags))]))
    reqTagRoots = np.unique([RequiredTag.processTagRoot(rootId)[0] for rootId in reqTagRoots])

    for root_id in reqTagRoots:
        childrenDic = getChildrens(root_id)    
        dicData.update(childrenDic)
        treeData[root_id] = childrenDic

    return treeData, dicData



