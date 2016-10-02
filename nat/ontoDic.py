# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 11:19:26 2016

@author: oreilly
"""

from .tagUtilities import nlx2ks
from .ontoServ import getLabelFromCurie
import collections


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
        if value is None:
            raise ValueError("The OntoDic class do not accept None as values.")
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

