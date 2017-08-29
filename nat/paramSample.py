# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 17:14:30 2017

@author: oreilly
"""

from quantities import Quantity
import numpy as np
from copy import copy

from .variable import NumericalVariable
from .values import ValuesSimple, ValuesCompound
from .paramDesc import ParamDescTrace
from .modelingParameter import getParameterTypeIDFromName, getParameterTypeNameFromID
from .annotationSearch import ParameterGetter
from .zoteroWrap import ZoteroWrap
from .ageResolver import AgeResolver
from .treeData import getChildren


class ParamSample:
    
    def __init__(self, searcher, libraryId=None, libraryType=None, apiKey=None):
        
        self.searcher = searcher
        self.sampleDF = searcher.search()
        if not libraryId is None and not libraryType is None and not apiKey is None:
            self.zotWrap = ZoteroWrap()
            self.zotWrap.loadCachedDB(libraryId, libraryType, apiKey)
        else:
            self.zotWrap = None
            
        self.ageUnit = "day"
        
        # For the conversion of age categories (e.g., adult) to 
        # numerical values. "min" species the lower bound of the interval.
        # For example, rats are adult from 5 months up to their dead (around 2-3.5 years)
        # setting this parametes to min, 5 months will be attributed as numerical
        # value for the age "adult" in rats.
        self.ageTypeValue = "min"
        
        self.sampleDF["isValid"] = None
        self.sampleDF["statusStr"] = ""
        self.__report = "Search string: " + str(self.searcher.conditions) + "\n"
        if self.searcher.onlyCentralTendancy:
            self.__report = "Search : Using central tendencies for single annotations containing multiple values.\n"
        self.__aggregators = {}
            


    def copy(self):
        copiedSample = copy(self)            
        copiedSample.sampleDF = self.sampleDF.copy()
        return copiedSample
            
    def setZoteroLib(self, libraryId, libraryType, apiKey):
        self.zotWrap = ZoteroWrap()
        self.zotWrap.loadCachedDB(libraryId, libraryType, apiKey)    



    def rescaleUnit(self, unit, rescaleStereo=True):
        
        def rescale2DStereo(paramID, thicknessValue, thicknessUnit, desiredUnit):
            density = paramGetter.getParam(paramID)
            thickness = Quantity(thicknessValue, thicknessUnit)
            return (density/thickness).rescale(desiredUnit)        
        

        self.__report += "Rescaling the units to '" + str(unit) + "'.\n"   
        if rescaleStereo:
            self.__report += "Rescaling densities from 2D densities to 3D.\n"              
        
        paramGetter = ParameterGetter(pathDB=self.searcher.pathDB)
        for param, annot, (index, row) in zip(self.sampleDF["obj_parameter"], 
                                              self.sampleDF["obj_annotation"], 
                                              self.sampleDF.iterrows()):
                                                  
            if param.unit == unit:
                continue
                                                  
            try:
                param = param.rescale(unit)
            except ValueError:
            
                if rescaleStereo:
                    thicknessInstanceId = [param.instanceId for param in annot.experimentProperties 
                                            if getParameterTypeNameFromID(param.paramTypeId) == "slice_thickness"]
         
                    if len(thicknessInstanceId) == 1:
                        thicknessParameter = paramGetter.getParam(thicknessInstanceId[0])
                        if len(thicknessParameter.values) == 1:
                            param = rescale2DStereo(param.id, thicknessValue=thicknessParameter.values[0], 
                                                    thicknessUnit=thicknessParameter.unit, 
                                                    desiredUnit=unit)
                            self.sampleDF.loc[index, "obj_parameter"] = param   
                            self.sampleDF.loc[index, "Values"]        = param.valuesText()   
                            self.sampleDF.loc[index, "Unit"]          = param.unit                   
                            continue
                
                statusStr = "Cannot be rescaled to unit " + str(unit) + "\n"
                self.sampleDF.loc[index, "isValid"]   = False
                self.sampleDF.loc[index, "statusStr"] += statusStr
                continue                

            if Quantity(1, param.unit) != Quantity(1, unit):
                statusStr = "Cannot be rescaled to unit " + str(unit) + "\n"
                self.sampleDF.loc[index, "isValid"]   = False
                self.sampleDF.loc[index, "statusStr"] += statusStr
                continue                            
                
            self.sampleDF.loc[index, "obj_parameter"] = param   
            self.sampleDF.loc[index, "Values"]        = param.valuesText()   
            self.sampleDF.loc[index, "Unit"]          = param.unit   





    def reformatAsNumericalTraces(self, indepVarName = None, indepVarId = None):
        if not indepVarName is None:
            if not indepVarId is None:
                if getParameterTypeNameFromID(indepVarId) != indepVarName:
                    raise ValueError("Parameters indepVarName and indepVarId "
                                    + "passed to ParamSample.reformatAsNumericalTraces() are incompatible.")
            else:
                indepVarId = getParameterTypeIDFromName(indepVarName)
                
            self.__report += "Reformating as numerical traces with independant variable '" \
                             + indepVarName + "'.\n"                      
                
        else:
            if indepVarId is None:
                raise ValueError("At least one of the attribute indepVarName and indepVarId "
                                    + "passed to ParamSample.reformatAsNumericalTraces() most not be None.")
            indepVarName = getParameterTypeNameFromID(indepVarId)
                
            self.__report += "Reformating as numerical traces with independant variable ID '" \
                             + indepVarId + "'.\n"                        

                
        for index, row in self.sampleDF.iterrows():
        
            if row["Result type"] == "pointValue":
                indepVar = row[indepVarName]
                if indepVar is None:
                    statusStr = "Cannot be transformed to a numerical trace: no values for the independant variable.\n"
                    self.sampleDF.loc[index, "isValid"]   = False
                    self.sampleDF.loc[index, "statusStr"] += statusStr
                    continue                   
                                
                # Building the independant variables   
                if isinstance(indepVar.magnitude.tolist(), list):
                    indepValueLst = indepVar.magnitude.tolist()
                else:
                    indepValueLst = [float(indepVar)]
                
                indepValues = ValuesSimple(indepValueLst, unit=str(indepVar.dimensionality))

                indepVar = NumericalVariable(typeId = indepVarId, 
                                             values = indepValues)

                # Building the dependant variable 
                depVar   = row["obj_parameter"].description.depVar   
                if len(depVar.values) != len(indepValueLst): 
                    if len(indepValueLst) == 1:
                        centralTendancy, statCT = row["obj_parameter"].centralTendancy(returnStat=True)  
                        deviation, statDev      = row["obj_parameter"].deviation(returnStat=True)  
                        size                    = row["obj_parameter"].size()  
                        depUnit  = row["obj_parameter"].unit                        
                        
                        depValueLst = [ValuesSimple([centralTendancy],
                                                     unit=depUnit, 
                                                     statistic=statCT),
                                       ValuesSimple([deviation],
                                                     unit=depUnit, 
                                                     statistic=statDev),
                                       ValuesSimple([size],
                                                     unit="dimensionless", 
                                                     statistic="N")]

                        depVar = NumericalVariable(typeId = depVar.typeId, 
                                                   values = ValuesCompound(depValueLst))
                        
                    else:
                        raise ValueError("Ambiguous attemps to transform a parameter into a numerical trace.")
                        
                # Building the numerical trace parameter
                row["obj_parameter"].description = ParamDescTrace(depVar, [indepVar])
                row["Result type"] = "numericalTrace"


        
    def preprocess(self, steps):
        for step in steps:
            getattr(self, "preprocess_" + step)()
        
    
    def preprocess_species(self):
        speciesId = []
        species   = []
        for index, row in self.sampleDF.iterrows():
            tags =row["Species"]
            if len(tags) > 1 :                
                statusStr = "Species ambiguous. More than one species associated to the annotation.\n"
                self.sampleDF.loc[index, "isValid"]   = False
                self.sampleDF.loc[index, "statusStr"] += statusStr                
                continue
                
            speciesId.append(tags[0].id)
            species.append(tags[0].name)
            
        self.sampleDF["SpeciesId"] = speciesId
        self.sampleDF["Species"]   = species
        
        self.__report += "Extracting species from annotations.\n"                  


    def preprocess_age(self):    
        if not "SpeciesId" in self.sampleDF:
            self.preprocess_species()
            
        ageCategoryIds = []
        ageCategories  = []
        numericalAges  = []
        for index, row in self.sampleDF.iterrows():
            
            # First check if an experimental property with age as been attributed to the record            
            ageExpProp = [expProp.instanceId for expProp in row["obj_annotation"].experimentProperties if expProp.paramTypeId == 'BBP-002001']
            if len(ageExpProp) > 1 :
                statusStr = "Age is ambiguous. More than one age experimentation property is associated with the annotation.\n"
                self.sampleDF.loc[index, "isValid"]   = False
                self.sampleDF.loc[index, "statusStr"] += statusStr                
                continue   
            
            if len(ageExpProp) == 1 :
                getter = ParameterGetter(pathDB=self.searcher.pathDB)
                
                ageParam = getter.getParam(ageExpProp[0])
                
                ageCategoryIds.append(None)
                ageCategories.append(None)        
                numericalAges.append(Quantity(ageParam.centralTendancy(), ageParam.unit).rescale(self.ageUnit))

            # No experimental property attributed. Check to use a age category if one has been attributed.
            else:
                tags = row["AgeCategories"]
                if len(tags) > 1 :
                    statusStr = "Age is ambiguous. More than one age category is associated with the annotation.\n"
                    self.sampleDF.loc[index, "isValid"]   = False
                    self.sampleDF.loc[index, "statusStr"] += statusStr                               
                    
                if len(tags) == 0:
                    ageCategoryIds.append(None)
                    ageCategories.append(None)
                    numericalAges.append(None)
                    continue
                
                ageCategoryIds.append(tags[0].id)
                ageCategories.append(tags[0].name)
                age = AgeResolver.resolve_fromIDs(row["SpeciesId"], tags[0].id, unit=self.ageUnit, 
                                                  typeValue=self.ageTypeValue) 
                numericalAges.append(age)

        self.sampleDF["AgeCategoryId"] = ageCategoryIds
        self.sampleDF["AgeCategory"]   = ageCategories
        self.sampleDF["age"]           = numericalAges

        
        self.__report += "Preprocessing age information.\n"                  



    
    def preprocess_ref(self):    
        if self.zotWrap is None:
            raise ValueError("To add references to the sample, you need first to set " +
                             "the Zotero library by calling LitSample.setZoteroLib()")

        self.sampleDF["ref"] = [self.zotWrap.getInTextCitationFromID(annot.pubId) 
                                           for annot in self.sampleDF["obj_annotation"]]
    
        self.__report += "Preprocessing associated references.\n"            
    
        
    def filter_species(self, speciesTermId):
        self.rootSpeciesId = speciesTermId
        childrenDict = getChildren(speciesTermId)

        if not "SpeciesId" in self.sampleDF:
            self.preprocess_species()
            
        for index, row in self.sampleDF.iterrows():

            if not row["SpeciesId"] in childrenDict:
                statusStr = "Species filtered out. Not a children of " + speciesTermId + ".\n"
                row["isValid"]   = False
                row["statusStr"] += statusStr                

        self.__report += "Filter species using the species ID '" + speciesTermId + "'.\n"            


        
    def validateUndefined(self):
        self.sampleDF.loc[np.equal(self.sampleDF["isValid"], None), "isValid"] = True

        self.__report += "Validated parameters with undefined status.\n"     


    def addAggregator(self, aggregator):
        self.__aggregators[aggregator.paramName] = aggregator
        self.__report += "Adding an aggregator for parameter '" + aggregator.paramName + \
                         "':" + str(aggregator) + ".\n"            
        
    def getParamValues(self, paramName=None, paramId=None, useOnlyValids=True):
        """
        Return the rows of sampleDF that are associated to the parameter
        specified in paramName.
        """
        
        if not paramName is None:
            if not paramId is None:
                if getParameterTypeNameFromID(paramId) != paramName:
                    raise ValueError("Parameters paramId and paramName "
                                    + "passed to ParamSample.getParamValues() are incompatible.")
        else:
            if paramId is None:
                raise ValueError("At least one of the attribute paramName and paramId "
                                    + "passed to ParamSample.getParamValues() most not be None.")
            paramName = getParameterTypeNameFromID(paramId)
        
        df = self.sampleDF
        if useOnlyValids:
            df = df[df["isValid"] == True]

        df.loc[:, "paramNames"] = [getParameterTypeNameFromID(param.typeId) for param in df["obj_parameter"]]

        return df[df["paramNames"] == paramName]            
        




    def interpolate(self, interpValues):
        """
        interpValues should be a dictionnary where the keys are the parameter names
        for the independant variable for which interpolation should be run and
        the values are the value to which the parameter should be interpolated.
        """        
        
        df = self.sampleDF
        self.interpValues = interpValues
        for interParamName, value  in interpValues.items():
            self.__report += "Interpolation of the parameters for independent variables '" \
                             + interParamName + "' at value " + str(value) + ".\n"   
            finalValues = np.zeros((len(df["Result type"])))
            for ind, (paramTrace, resType) in enumerate(zip(df["obj_parameter"], df["Result type"])):
                if resType == "numericalTrace" and interParamName in paramTrace.indepNames:
                    val = paramTrace.getInterp1dValues(value, interParamName, statsToReturn=["mean"])
                    if isinstance(val, list):
                        if len(val) == 1:
                            val = val[0]
                        else:
                            raise ValueError("This case has not been implemented yet.")
                    df.loc[ind, "Values"] = float(val)   

                    

    




    def getModelingValues(self, paramName):
        """
        Return the values to use in modeling for the parameterId, by the 
        aggregation method specified by the associated aggregator.
        """        
        
        return self.__aggregators[paramName].values(self)

    @property 
    def validSample(self):
        return self.sampleDF.loc[self.sampleDF["isValid"]]
        
    @property 
    def invalidSample(self):
        return self.sampleDF.loc[np.logical_not(self.sampleDF["isValid"])]

    @property 
    def report(self):
        return self.__report

    #def get