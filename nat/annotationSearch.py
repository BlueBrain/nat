#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'


import os
from glob import glob
import pandas as pd
import numpy as np
import os.path
import pickle

from .annotation import Annotation
from .modelingParameter import getParameterTypeNameFromID
from .variable import NumericalVariable, Variable
from .treeData import flatten_list
from .ontoManager import OntoManager
from .tagUtilities import nlx2ks    
from .condition import Condition, ConditionAtom
from .equivalenceFinder import EquivalenceFinder

annotationKeys         = ["Annotation type", "Annotation ID", "Publication ID", "Has parameter", "Tag name", "Author"]
annotationResultFields = ["Annotation type", "Publication ID", "Nb. parameters", "Tag name", "Comment", "Authors", "Localizer"]

parameterKeys          = ["Parameter name", "Result type", "Parameter instance ID", 
                          "Unit", "Required tag name", "Annotation ID", 
                          "Publication ID", "Tag name"]
parameterResultFields  = ["Required tag names", "Result type", "Values", "Parameter name", 
                          "Parameter type ID", "Parameter instance ID", "Unit", 
                          "Text", "Context", "Species", "AgeCategories"] 



class CompiledCorpus:
    
    def __init__(self, binPath="annotations.bin"):
               
        if os.path.isabs(binPath):
            self.binPath = binPath
        else:
            self.binPath = os.path.join(os.path.dirname(__file__), binPath)  
        
        try:
            if os.path.isfile(self.binPath):
                self.loadBin()
        except:
            print("Warning: Failed to load the compiled corpus.")
            self.annotations = []
        
    def loadBin(self):
        with open(self.binPath, "rb") as binFile:
            self.annotations = pickle.load(binFile)        
        
    def compileCorpus(self, pathDB=".", outPath=None):
        if outPath is None:
            outPath = self.binPath

        self.annotations = []
        for fileName in glob(pathDB + "/*.pcr"):
            self.annotations.extend(Annotation.readIn(open(fileName, "r", encoding="utf-8", errors='ignore')))
    
        with open(outPath, "wb") as binFile:
            pickle.dump(self.annotations, binFile)
    
    def getAllAnnotations(self):
        return self.annotations


class Search:
    
    def __init__(self, pathDB=None, compiledCorpus=None):
        if pathDB is None:
            pathDB = os.path.join(os.path.dirname(__file__), 'curator_DB')

        self.compiledCorpus = compiledCorpus
        ontoMng = OntoManager()
        self.treeData                  = ontoMng.trees 
        self.dicData                   = ontoMng.dics
        
        self.conditions = Condition()    

        
        self.pathDB     = pathDB 
        self.getAllAnnotations()
        self.selectedItems = None
        self.findEquivalences = True

    def searchAnnotations(self):
        pass

    def searchParameters(self):
        pass

    
    def setSearchConditions(self, conditions):
        if not isinstance(conditions, Condition):
            raise TypeError            
        self.conditions = conditions

    
    def setResultFields(self, resultFields):
        self.resultFields = resultFields
    


    def getAllAnnotations(self):
        if not self.compiledCorpus is None:
            self.annotations = self.compiledCorpus.getAllAnnotations()
            return
 
        self.annotations = []
        for fileName in glob(self.pathDB + "/*.pcr"):
            self.annotations.extend(Annotation.readIn(open(fileName, "r", encoding="utf-8", errors='ignore')))



class AnnotationGetter(Search):
    
    def __init__(self, pathDB=None, compiledCorpus=None):
        super(AnnotationGetter, self).__init__(pathDB, compiledCorpus)

    def getAnnot(self, annotId):
        self.setSearchConditions(ConditionAtom("Annotation ID", annotId))
        self.selectedItem = self.conditions.apply_annot(self.annotations)
        if len(self.selectedItem) == 1 :
            return self.selectedItem[0]
            
        if len(self.selectedItem) == 0 :            
            raise ValueError("No corresponding annotations where found.")
        
        raise ValueError("More than one annotation have been found for this ID.")





class ParameterGetter(Search):
    
    def __init__(self, pathDB=None, compiledCorpus=None):
        super(ParameterGetter, self).__init__(pathDB, compiledCorpus)
        self.parameters = flatten_list([[(param, annot) for param in annot.parameters] for annot in self.annotations])
        self.parameters = {param:annot for param, annot in self.parameters}
                

    def getParam(self, instanceId, returnAnnotation=False):
        self.setSearchConditions(ConditionAtom("Parameter instance ID", instanceId))
        self.selectedItem = self.conditions.apply_param(self.parameters)
        if len(self.selectedItem) == 1 :
            if returnAnnotation:
                return list(self.selectedItem.keys())[0], list(self.selectedItem.values())[0]
            else:
                return list(self.selectedItem.keys())[0]
            
        if len(self.selectedItem) == 0 :            
            raise ValueError("No corresponding parameter instance where found.")
        
        raise ValueError("More than one parameter instance have been found for this ID.")


class AnnotationSearch(Search):
    
    def __init__(self, pathDB=None, compiledCorpus=None):
        super(AnnotationSearch, self).__init__(pathDB, compiledCorpus)
        self.resultFields = annotationResultFields

    def search(self):
        if self.findEquivalences:
            self.conditions = EquivalenceFinder(self.conditions).run()
        self.selectedItems = self.conditions.apply_annot(self.annotations)
        resultDF           = self.formatOutput(self.selectedItems)
        return resultDF


    def formatOutput(self, annotations):

        results = {"obj_annotation":annotations} 
        for field in self.resultFields:
            
            if field == "Annotation type":
                results[field] = [annot.type for annot in annotations]                

            elif field == "Publication ID":
                results[field] = [annot.pubId for annot in annotations]                    
                                 
            elif field == "Nb. parameters":
                results[field] = [len(annot.parameters) for annot in annotations]          
                                 
            elif field == "Comment":
                results[field] = [annot.comment for annot in annotations]  
                
            elif field == "Authors":
                results[field] = [annot.authors for annot in annotations]          

            elif field == "Localizer":
                results[field] = [annot.text for annot in annotations]          

            elif field == "Tag name":
                try:
                    results[field] = [[tag.name for tag in annot.tags] for annot in annotations]         
                except AttributeError:
                    for annot in annotations:
                        print(annot.tags)
                    raise
             
            else :
                raise ValueError

        return pd.DataFrame(results)



class ParameterSearch(Search):
    
    def __init__(self, pathDB=None, compiledCorpus=None):
        super(ParameterSearch, self).__init__(pathDB, compiledCorpus)
        self.resultFields = parameterResultFields
        self.getAllParameters()
        self.expandRequiredTags = False
        self.onlyCentralTendancy = False   
        self.contextLength       = 100


    def search(self):
        if self.findEquivalences:
            self.conditions = EquivalenceFinder(self.conditions).run()
        self.selectedItems = self.conditions.apply_param(self.parameters)
        resultDF           = self.formatOutput(self.selectedItems)
        return resultDF


    def formatOutput(self, parameters):

        results = {"obj_parameter":list(parameters.keys()), "obj_annotation":list(parameters.values())}
        annotations = list(parameters.values())
        
        
        for field in self.resultFields:
            
            if field == "Parameter name":
                results[field] = [getParameterTypeNameFromID(param.description.depVar.typeId) for param in parameters]                
            
            elif field == "Text":
                results[field] = [annot.text for annot in annotations]                
            
            elif field == "Context":
                results[field] = [annot.getContext(self.contextLength, dbPath=self.pathDB) for annot in annotations]

            elif field == "Result type":
                results[field] = [param.description.type for param in parameters]               
                        
            elif field == "Required tag names":
                if self.expandRequiredTags:
                    # Get all root_ids the required tags of the parameters
                    tagCats = np.unique(flatten_list([[tag.rootId for tag in param.requiredTags] 
                                                                  if len(param.requiredTags) 
                                                                  else "" 
                                                                  for param in parameters]))
                                                                      
                    # Remove duplicates and normalize IDs                              
                    tagCats = np.unique([nlx2ks[id] if id in nlx2ks else id for id in tagCats])                                                                  

                    for tagCatId in tagCats:
                        tagNames = []
                        for param in parameters:
                            tagName = ""
                            for tag in param.requiredTags:
                                tagRoot = nlx2ks[tag.rootId] if tag.rootId in nlx2ks else tag.rootId                                     
                                if tagRoot == tagCatId:
                                    tagName = tag.name
                                    break
                            tagNames.append(tagName)
                                
                        results[self.dicData[tagCatId]] = tagNames
                        
                else:
                     results[field] = [[tag.name for tag in param.requiredTags] 
                                                 if len(param.requiredTags) 
                                                 else "" 
                                                 for param in parameters]

       
            elif field == "Parameter type ID":
                results[field] = [param.description.depVar.typeId for param in parameters]            
             
            elif field == "Parameter instance ID":
                results[field] = [param.id for param in parameters]            


            elif field == "Unit":
                units = []
                for param in parameters:
                    if isinstance(param.description.depVar, Variable):
                        units.append(param.description.depVar.unit)
                    elif isinstance(param.description.depVar, NumericalVariable):
                        units.append(param.description.depVar.values.textUnit())
                    else:
                        raise TypeError
                results[field] = units

        
            elif field == "Species":
                results[field] = [annot.getSpecies() for annot in annotations]  
                
            elif field == "AgeCategories":
                results[field] = [annot.getAgeCategories() for annot in annotations]     

            elif field == "Values":
                if self.onlyCentralTendancy:
                    results[field] =  [param.centralTendancy() 
                                        if isinstance(param.description.depVar, NumericalVariable)
                                        else np.nan 
                                        for param in parameters]                                            
                else:
                    results[field] =  [param.valuesText() 
                                        if isinstance(param.description.depVar, NumericalVariable)
                                        else np.nan 
                                        for param in parameters]            
            else :
                raise ValueError

        return pd.DataFrame(results)



    def getAllParameters(self):
        self.parameters = flatten_list([[(param, annot) for param in annot.parameters] for annot in self.annotations])
        self.parameters = {param:annot for param, annot in self.parameters}
        




if __name__ == "__main__":

    searcher = ParameterSearch()
    searcher.setSearchConditions(ConditionAtom("Parameter name", "conductance_ion_curr_max"))
    searcher.expandRequiredTags = True

    result = searcher.search()
    print(result)
