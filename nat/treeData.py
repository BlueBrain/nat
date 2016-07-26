#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'


from .tagUtilities import nlx2ks
from .tag import RequiredTag
from .ontoServ import getLabelFromCurie
from .modelingParameter import ParameterTypeTree
from .scigraph_client import Vocabulary, Graph

import json
import os
from glob import glob
import pandas as pd
import collections
import pickle
import numpy as np


def flatten_list(l):
    return [item for sublist in l for item in sublist]



"""

def buildTreeFromRoot(root_id, maxDepth=100, root_no=0, verbose=False, fileName="onto", recompute=True):
    graph = Graph()            
    vocab = Vocabulary()

    if root_id in nlx2ks:
        root_id = nlx2ks[root_id]

    def addSubtree(root, depth=0): 
        if depth+1 < maxDepth:
            if root is None:
                return
            neighbors = graph.getNeighbors(root.id, relationshipType="subClassOf", direction="INCOMING")
            if neighbors is None:
                nodes = []
            else:
                nodes = neighbors["nodes"]
                
            ids, ids_idx = np.unique([node["id"] for node in nodes], return_index=True)
            #print(len(nodes), len(ids_idx), ids)
            for node in np.array(nodes)[ids_idx]:
                nodeLabel = node["lbl"]
                nodeId    = node["id"]
                
                if root.id == nodeId:
                    continue

                if nodeLabel is None:
                    continue
                
                child = TreeData(nodeLabel, nodeId, root)            
                termDic[nodeId] = nodeLabel
                if verbose:
                    print(" "*(depth+1) + nodeLabel, " (" + nodeId + ")")
                addSubtree(child, depth+1)
                root.children.append(child)


    termDic = {}            
    root = vocab.findById(root_id)
    if root is None:
        if verbose:
            print("Skipping", root_no, root_id)
        return None, None
    if root["labels"] is None:
        if verbose:
            print("Skipping " + str(root_no))
        return None, None
    neighbors = graph.getNeighbors(root_id, relationshipType="subClassOf", direction="INCOMING")    
    if neighbors is None:
        if verbose:
            print("Skipping " + str(root_no))
        return None, None
    if len(neighbors["nodes"]) == 1:
        if verbose:
            print("Skipping " + str(root_no))
        return None, None
    
    root_name = root["labels"][0]
    if not recompute:
        if (os.path.isfile(fileName + "_" + root_name + "_" + str(root_no) + ".tree") and
            os.path.isfile(fileName + "_" + root_name + "_" + str(root_no) + ".dic")) :
            if verbose:
                print("Skipping " + fileName + "_" + root_name + "_" + str(root_no))
            return None, None
        
    if verbose:
        print(root_name)
    root = TreeData(root_name, root_id, root_no=root_no)            
    termDic[root_id] = root_name
    addSubtree(root)
    return root, termDic



"""

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


"""

def build_request(queryHeader = "prefix xsd: <http://www.w3.org/2001/XMLSchema#> \n prefix property: <http://neurolex.org/wiki/Property-3A>",
                  querySelect = "select DISTINCT ?name ?id where",
                  where_list = []):

    return queryHeader + querySelect + '{' + ' . '.join(where_list) + '}'


def find_all_items(attempt=0, maxAttemps=10):

    where_list = ['?x property:Label ?name',
                  '?x property:Id ?id']
    try:
        sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
        sparql.setQuery(build_request(where_list=where_list))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return {result["id"]["value"]:result["name"]["value"] for result in results["results"]["bindings"]}
    except urllib.error.URLError:
        print("Raising cancelled.")
        if attempt == maxAttemps:
            raise
        else:
            return find_all_items(attempt+1)



def find_subregions(region_id, attempt=0, maxAttemps=10):

    where_list = [
        '?region property:Id "{0}"^^xsd:string'.format(region_id),
        '?subregions property:Is_part_of ?region_name',
        '?subregions property:Label ?subregions_name',
        '?region       property:Label ?region_name',
        '?subregions property:Id ?subregions_id']  
  
     #             [
    #    '?x property:Id "{0}"^^xsd:string'.format(region_id),
    #    '{?regions property:SuperCategory ?x_name} UNION { ?regions property:Is_part_of ?x }',
    #    '?regions property:Label ?name',
    #    '?x       property:Label ?x_name',
    #    '?regions property:Id ?id']
  
    try:
        sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
        sparql.setQuery(build_request(where_list=where_list))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return [result["subregions_id"]["value"] for result in results["results"]["bindings"]]
    except urllib.error.URLError:
        if attempt == maxAttemps:
            raise
        else:
            return find_subregions(region_id, attempt+1, maxAttemps)





def find_subcategories(cat_id, attempt=0, maxAttemps=10):

    where_list = [
        '?cat property:Id "{0}"^^xsd:string'.format(cat_id),
        '?subcats property:SuperCategory ?cat_name',
        '?subcats property:Label         ?subcats_name',
        '?cat     property:Label         ?cat_name',
        '?subcats property:Id            ?subcats_id']  
  
    try:
        sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
        sparql.setQuery(build_request(where_list=where_list))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return [result["subcats_id"]["value"] for result in results["results"]["bindings"]]
    except urllib.error.URLError:
        if attempt == maxAttemps:
            raise
        else:
            return find_subcategories(cat_id, attempt+1, maxAttemps)






def name_from_id(region_id, attempt=0, maxAttemps=10):

    where_list = ['?x property:Id "{0}"^^xsd:string'.format(region_id), '?x property:Label ?name',]

    try:
        sparql = SPARQLWrapper("http://rdf-stage.neuinfo.org/ds/query")
        sparql.setQuery(build_request(where_list=where_list))
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return [result["name"]["value"] for result in results["results"]["bindings"]][0]
    except urllib.error.URLError:
        if attempt == maxAttemps:
            raise
        else:
            return name_from_id(region_id, attempt+1, maxAttemps)

"""



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




"""
 Better not to define as a TreeData static method because it cause problem
 when loading from pickle since pickle need to know the definition of the 
 class, which can be not loaded yet.
"""
"""
def __loadTreeData__(fileNamePattern):
    
    raise ValueError()
    
    if fileNamePattern is None:
        fileNamePattern = os.path.join(os.path.dirname(__file__), "onto/onto*")    

    class TranslatingDict(TransformedDict):
    
        def __keytransform__(self, id):
            return nlx2ks[id] if id in nlx2ks else id
    
    trees = []       
    for fileName in glob(fileNamePattern + ".tree"):
        trees.append(TreeData.loadTree(fileName))
            
    dic = TranslatingDict()
    for fileName in glob(fileNamePattern + ".dic"):
        with open(fileName, 'r') as f:
            dic.update(json.load(f))


    trees, dic = appendAdditions(trees, dic)
    dic = addSuppTerms(dic)
    return trees, dic

"""



"""
def addSuppTerms(dic):
    
    
    # Previously, we were doing something like...
    #    
    #idsToAdd = [...]
    #vocab = Vocabulary()
    #for id in idsToAdd:
    #    term = vocab.findById(id)      
    #    dic[id] = term["labels"][0] 
    #
    # ...but this calls the SciGraph interface which queries for the information
    # online. This fails when working offline. Thus, for now, we just specify
    # the terms name by hand.
    
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
        if row["id"] in dicData:
            continue

        dicData[row["id"]] = row["label"]
        if isinstance(row["superCategory"], str): 
            
            # Check that superCategory is a str because when no superCategory
            # has been specified, the pd.read_csv put a nan value which is 
            # a float type. In this case, we don't want to try to attach the
            # term to a tree.
            subTree = None
            for tree in treeData:
                subTree = tree.getSubTree(row["superCategory"])    
                if not subTree is None:
                    break
            if not subTree is None:
                child = TreeData(row["label"], row["id"], parent=subTree.id)
                subTree.children.append(child)
            else:
                # Define as a new tree
                treeData.append(TreeData(row["label"], row["id"]))
        else:
            # Define as a new tree
            treeData.append(TreeData(row["label"], row["id"]))

    print(treeData)
    return treeData, dicData


def appendReqTagTrees(treeData, dicData):
    df = ParameterTypeTree.getParamTypeDF()
    
    reqTagRoots = np.unique(np.concatenate([list(eval(reqTags).keys()) for reqTags in df["requiredTags"] if len(eval(reqTags))]))
    reqTagRoots = np.unique([RequiredTag.processTagRoot(rootId)[0] for rootId in reqTagRoots if not "NOLOAD" in RequiredTag.processTagRoot(rootId)[1]])

    for root_id in reqTagRoots:
        if not root_id in dicData:
            #print("####", root_id)
            root, termDic = buildTreeFromRoot(root_id, verbose=True)
        
            if not root is None:
                dicData.update(termDic)
                treeData.append(root)

    return treeData, dicData
"""




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








"""


class TreeData:
    def __init__(self, txt, id, parent=None, root_no=None):

        self.txt = txt
        self.id  = id
        self.parent = parent
        self.children = []
        self.root_no = root_no


    def __str__(self):
        return "TreeData[" + self.id + ":" + self.txt + "]"


    def __repr__(self):
        return "TreeData[" + self.id + ":" + self.txt + "]"


    def toJSON(self):
        return {"txt":self.txt, "id": self.id, "parent":"", 
                "root_no":self.root_no, 
                "children":[child.toJSON() for child in self.children]}

    @staticmethod
    def fromJSON(jsonString, parent=None):
        tree = TreeData(jsonString["txt"], jsonString["id"], parent,  
                        jsonString["root_no"])

        tree.children = [TreeData.fromJSON(v, tree) for v in jsonString["children"]]
        return tree



    def position(self):
        if self.parent is not None:
            for count, child in enumerate(self.parent.children):
                if child == self:
                    return count
        else:
            return self.root_no


    def isInTree(self, id):
        if id == self.id:
            return True
        elif id in nlx2ks:
            if nlx2ks[id] == self.id:
                return True
            
        for child in self.children:
            if child.isInTree(id):
                return True
        return False


    def getSubTree(self, id):
        if id == self.id:
            return self
        elif id in nlx2ks:
            if nlx2ks[id] == self.id:
                return self
            
        for child in self.children:
            subTree = child.getSubTree(id)
            if not subTree is None :
                return subTree
        return None


    def asList(self):
        idList   = [self.id]
        nameList = [self.txt]
        for child in self.children:
            ids, names = child.asList()
            idList.extend(ids)
            nameList.extend(names)
        return idList, nameList




    def printTree(self, level = 0, printID=False):
        if printID:
            print("="*level + " " + self.id + ":" + self.txt)
        else:
            print("="*level + " " + self.txt)
            
        for child in self.children:
            child.printTree(level+1, printID=printID)



    def saveTree(self, fileName):
        with open(fileName + "_" + self.txt + "_" + str(self.root_no) + ".tree", 'w') as fileObj:
            json.dump(self.toJSON(), fileObj, sort_keys=True, indent=4, separators=(',', ': '))
            
    @staticmethod
    def loadTree(fileName):
        with open(fileName, 'r') as fileObj:
            jsonAnnots = json.load(fileObj)
        return TreeData.fromJSON(jsonAnnots)

"""