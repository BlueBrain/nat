#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

from PySide import QtGui, QtCore
import os
from glob import glob
import pandas as pd
import collections
import json

from .tagUtilities import nlx2ks
from .treeData import TreeData

"""
def flatten_list(l):
    return [item for sublist in l for item in sublist]
"""


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








"""
 Better not to define as a TreeData static method because it cause problem
 when loading from pickle since pickle need to know the definition of the 
 class, which can be not loaded yet.
"""
"""
def loadTreeData(fileNamePattern=None):

    if fileNamePattern is None:
        fileNamePattern = os.path.join(os.path.dirname(__file__), "onto/onto*")    
    
    # From http://stackoverflow.com/a/3387975/1825043
    class TransformedDict(collections.MutableMapping):
        # A dictionary that applies an arbitrary key-altering
        # function before accessing the keys
    
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
            if subTree is None:
                #raise ValueError
                pass
            else:
                child = TreeData(row["label"], row["id"], parent=subTree.id)
                subTree.children.append(child)

    return treeData, dicData

"""




class TreeModel(QtCore.QAbstractItemModel):

    def __init__(self, tree):
        super(TreeModel, self).__init__()
        self.__tree = tree
        self.__current = tree[0]


    def flags(self, index):
        flag = QtCore.Qt.ItemIsEnabled
        if index.isValid():
            flag |= QtCore.Qt.ItemIsSelectable
        return flag


    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid():
            node = parent.internalPointer().children[row]
        else:
            node = self.__tree[row]
        return self.__createIndex(row, column, node)


    def parent(self, index):
        node = QtCore.QModelIndex()
        if index.isValid():
            nodeS = index.internalPointer()
            parent = nodeS.parent
            if parent is not None:
                node = self.__createIndex(parent.position(), 0, parent)
        return node


    def rowCount(self, index=QtCore.QModelIndex()):
        count = len(self.__tree)
        node = index.internalPointer()
        if node is not None:
            count = len(node.children)
        return count


    def columnCount(self, index=QtCore.QModelIndex()):
        return 1


    def data(self, index, role=QtCore.Qt.DisplayRole):
        data = None
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            node = index.internalPointer()
            data = node.txt

        if role == QtCore.Qt.UserRole:
            node = index.internalPointer()
            data = node.id

        return data


    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        result = True
        if role == QtCore.Qt.EditRole and value != "":
            node = index.internalPointer()
            node.text = value
            result = True
        return result


    def __createIndex(self, row, column, node):
        if node.index == None:
            index = self.createIndex(row, column, node)
            node.index = index
        return node.index

    def headerData(self, section, orientation, role):
        return None





class TreeView(QtGui.QTreeView):

    def __init__(self, model, parent=None):
        super(TreeView, self).__init__(parent)
        self.__model = model
        self.setModel(model)

        self.header().hide() 


        self.setCurrentIndex(self.__model.index(0, 0))
        return

