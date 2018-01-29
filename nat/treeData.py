#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

import os
import pickle

import numpy as np
import pandas as pd
import requests

from nat.utils import data_path
from .modelingParameter import ParameterTypeTree
# from .scigraph_client import Graph
from .ontoDic import OntoDic
from .tag import RequiredTag
from .tagUtilities import nlx2ks

rootIDs = {}

# "Eumetazoa" includes almost all animals. 
rootIDs["species"] = "NIFORG:birnlex_569"

# "maturity" includes many qualifier for age categories.
rootIDs["ageCategories"] = "PATO:0000261"



def flatten_list(l):
    return [item for sublist in l for item in sublist]



def getBBPChildren(root_id, df=None, childrenDic=None):
    if df is None:
        csvFileName = data_path("additionsToOntologies.csv")
    
        df = pd.read_csv(csvFileName, skip_blank_lines=True, comment="#", 
                         delimiter=";", names=["id", "label", "definition", "superCategory", "synonyms"])    

        childrenDic = OntoDic()
    
        selected = df[df["superCategory"] == root_id]
    
    for key in selected["id"]:
        childrenDic = getBBPChildren(key, df, childrenDic)
        
    childrenDic.update({key:value for key, value in zip(selected["id"], selected["label"])})
    return childrenDic


def getChildren(root_id, maxDepth=100, relationshipType="subClassOf", 
                 alwaysFetch=False):
    """
     Accessing web-based ontology service is too long, so we cache the 
     information in a pickle file and query the services only if the info
     has not already been cached. 
    """
    childrenDic = {}
    fileName = os.path.join(os.path.dirname(__file__), "children.bin") 

    #### CHECK FOR CASE OF BBP TAGS
    if root_id[:4] == "BBP_":

        if not alwaysFetch:
            try:
                with open(fileName, "rb") as childrenFile:
                    childrenDic = pickle.load(childrenFile)
                    
                if root_id in childrenDic:
                    return childrenDic[root_id]                
            except:
                pass        

        childrenDic[root_id] = getBBPChildren(root_id)        
        
        if not alwaysFetch:
            try:
                with open(fileName, "wb") as childrenFile:
                    pickle.dump(childrenDic, childrenFile)
            except:
                pass      
            
        return childrenDic[root_id]

    ## TODO: should also check for BBP children of online onto terms

    if root_id in nlx2ks:
        root_id = nlx2ks[root_id]

    if not alwaysFetch:
        try:
            with open(fileName, "rb") as childrenFile:
                childrenDic = pickle.load(childrenFile)
                
            if root_id in childrenDic:
                return childrenDic[root_id]                
        except:
            pass

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

    if not response.ok:
        return {}
        
    neighbors = response.json()

    if neighbors is None:
        return {}

    nodes = neighbors["nodes"]
    #for node in np.array(nodes):
    #    node["lbl"] = node["lbl"].encode('utf-8').decode('utf-8')
        
    #try:
    #    assert(np.all([not node["lbl"] is None for node in np.array(nodes)]))
    #except AssertionError: 
    #    for node in np.array(nodes):
    #        if node["lbl"] is None:
    #            print(node["id"])
    #    raise        
    
    # TODO: replace by the commented line below. This patch is only to 
    #       accomodate for a current issue with the knowledge-space endpoint.          
    #childrenDic[root_id]  = OntoDic({node["id"]:node["lbl"] for node in np.array(nodes)})        
    childrenDic[root_id]  = OntoDic({node["id"]:node["lbl"] for node in np.array(nodes) if not node["lbl"] is None})
    
    if not alwaysFetch:    
        try:
            with open(fileName, "wb") as childrenFile:
                pickle.dump(childrenDic, childrenFile)
        except:
            pass        

    return childrenDic[root_id] 
    
    

#http://matrix.neuinfo.org:9000/scigraph/graph/neighbors/UBERON:0000955?blankNodes=False&depth=1&direction=INCOMING&project=*&relationshipType=subClassOf
    
    

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
    csvFileName = data_path("additionsToOntologies.csv")

    df = pd.read_csv(csvFileName, skip_blank_lines=True, comment="#", 
                     delimiter=";", names=["id", "label", "definition", "superCategory", "synonyms"])
    for index, row in df.iterrows():
        if not row["id"] in dicData:
            dicData[row["id"]] = row["label"]

        if isinstance(row["superCategory"], str):         
            for rootId, children in treeData.items():
                if row["superCategory"] == rootId or row["superCategory"] in children:
                    children[row["id"]] = row["label"]
    return treeData, dicData


def appendReqTagTrees(treeData, dicData, alwaysFetch=False):
    df = ParameterTypeTree.getParamTypeDF()
    
    reqTagRoots = np.unique(np.concatenate([list(eval(reqTags).keys()) for reqTags in df["requiredTags"] if len(eval(reqTags))]))
    reqTagRoots = np.unique([RequiredTag.processTagRoot(rootId)[0] for rootId in reqTagRoots])
    
    # Adding supplementary category roots that are not required tags but that  
    # are useful to define project-wide properties.
    reqTagRoots = np.concatenate((list(rootIDs.values()), reqTagRoots))        
    
    for root_id in reqTagRoots:
        print("Building ontological tree for ", root_id, "... ")
        childrenDic = getChildren(root_id, alwaysFetch=alwaysFetch)    
        dicData.update(childrenDic)
        treeData[root_id] = childrenDic
    return treeData, dicData



