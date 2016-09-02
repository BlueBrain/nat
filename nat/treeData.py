#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'


from .tagUtilities import nlx2ks
from .tag import RequiredTag
from .ontoServ import getLabelFromCurie
from .modelingParameter import ParameterTypeTree
from .scigraph_client import Graph

import os
import pandas as pd
import collections
import pickle
import numpy as np


def flatten_list(l):
    return [item for sublist in l for item in sublist]


def getChildrens(root_id, maxDepth=100, relationshipType="subClassOf"):
    graph = Graph()            

    if root_id in nlx2ks:
        root_id = nlx2ks[root_id]

    neighbors = graph.getNeighbors(root_id, depth=maxDepth, 
                                   relationshipType=relationshipType, 
                                   direction="INCOMING")
    if neighbors is None:
        return {}

    nodes = neighbors["nodes"]
    return OntoDic({node["id"]:node["lbl"] for node in np.array(nodes)})
    
    

# From http://stackoverflow.com/a/3387975/1825043
class TransformedDict(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key        
        
    def __str__(self):
        return "{" + ", ".join([str(key) + ":" + str(val) for key, val in self.items()]) +  "}"



class OntoDic(TransformedDict):

    # We reimplement __setitem__ and __contains__ because we don't want to 
    # check ontology services when adding new item to the dict.
    def __setitem__(self, key, value):
        if key in nlx2ks:
            key = nlx2ks[key]        
        self.store[key] = value

    def __contains__(self, key):
        if key in nlx2ks:
            key = nlx2ks[key]             
        return key in self.store
        

    def __keytransform__(self, id):
        if id in nlx2ks:
            id = nlx2ks[id]
        if not id in self.store:                
            label = getLabelFromCurie(id)
            if label is None:
                raise KeyError("The id '" + id + "' is not known locally and is not available in the registered ontology services.")    
            
            self.store[id] = label
            #print("Adding label " + label + " for the id " + id + " to the local tag id dict.")    
        return id
    
    
    def __str__(self):
        return super(OntoDic, self).__str__()


class OntoManager:

    __ontoTrees__ = {}
    __ontoDics__  = {}
    
    try:
        with open('ontoDics.pickle', 'rb') as f:
            __ontoDics__ = pickle.load(f)
        with open('ontoTrees.pickle', 'rb') as f:
            __ontoTrees__ = pickle.load(f)
    except:
        pass


    def __init__(self, fileNamePattern=None):

        if fileNamePattern is None:
            self.fileNamePattern = os.path.join(os.path.dirname(__file__), "onto/onto*")            
        else:
            self.fileNamePattern = fileNamePattern
        
        if not self.fileNamePattern in OntoManager.__ontoTrees__:
            OntoManager.__ontoTrees__[self.fileNamePattern] = OntoDic()
            OntoManager.__ontoDics__[self.fileNamePattern]  = OntoDic()   
    
            OntoManager.__ontoTrees__[self.fileNamePattern], \
            OntoManager.__ontoDics__[self.fileNamePattern] = appendReqTagTrees(OntoManager.__ontoTrees__[self.fileNamePattern], 
                                                                               OntoManager.__ontoDics__[self.fileNamePattern])                        
            
            OntoManager.__ontoTrees__[self.fileNamePattern], \
            OntoManager.__ontoDics__[self.fileNamePattern] = appendAdditions(OntoManager.__ontoTrees__[self.fileNamePattern], 
                                                                             OntoManager.__ontoDics__[self.fileNamePattern])
                                                            
            OntoManager.__ontoDics__[self.fileNamePattern] = addSuppTerms(OntoManager.__ontoDics__[self.fileNamePattern])
                
            #print(self.dics, self.trees)            
                
            self.savePickle()

            
        #if not self.fileNamePattern in __ontoTrees__: 
        #    __ontoTrees__[self.fileNamePattern], \
        #    __ontoDics__[self.fileNamePattern] = __loadTreeData__(self.fileNamePattern)
        
    @property
    def dics(self):
        return OntoManager.__ontoDics__[self.fileNamePattern]
        
    @property
    def trees(self):
        return OntoManager.__ontoTrees__[self.fileNamePattern]

    def savePickle(self):
        with open('ontoDics.pickle', 'wb') as f:
            pickle.dump(OntoManager.__ontoDics__, f, pickle.HIGHEST_PROTOCOL)
        with open('ontoTrees.pickle', 'wb') as f:
            pickle.dump(OntoManager.__ontoTrees__, f, pickle.HIGHEST_PROTOCOL)





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



