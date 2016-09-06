#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'


from .ontoDic import OntoDic
from .treeData import appendReqTagTrees, appendAdditions, addSuppTerms

import os
import pickle



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





