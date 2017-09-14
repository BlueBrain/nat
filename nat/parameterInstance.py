# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 16:31:44 2017

@author: oreilly
"""
from uuid import uuid1
from scipy import interpolate
from copy import deepcopy
import json

from .tag import RequiredTag
from .tagUtilities import nlx2ks
from .ontoServ import getCuriesFromLabel
from .relationship import Relationship
from .paramDesc import ParamDesc, ParamDescPoint
from .variable import Variable, NumericalVariable
from .values import ValuesSimple, ValuesCompound
from .modelingParameter import getParameterTypeNameFromID, getParameterTypeFromID



class ParameterInstance:
    # This class represent a parameter instance. It can be used to
    # represent 1) a parameter that is specified in a
    # modeling file (e.g. .mm_py, .mm_hoc, .mm_mod) with the #|...|#
    # formalism or 2) a parameter specified by a given annotation.
    # The objects encode the type of parameter, its numerical value,
    # the units in which it is specified, and the annotation and publication
    # ID it refers to.
    def __init__(self, id, description, requiredTags,
                  relationship=None, isExperimentProperty=False):
        super(ParameterInstance, self).__init__()


        if not isinstance(relationship, Relationship) and not relationship is None:
            print(relationship, type(relationship))
            raise TypeError
        if not isinstance(description, ParamDesc):
            raise TypeError
        if not isinstance(requiredTags, list):
            raise TypeError
        for reqTag in requiredTags:
            if not isinstance(reqTag, RequiredTag):
                raise TypeError
        if not isinstance(isExperimentProperty, bool):
            raise TypeError

        if id is None:
            self.id = str(uuid1())
        else:
            self.id    = id

        self.requiredTags           = requiredTags
        self.description            = description
        self.relationship           = relationship
        self.isExperimentProperty   = isExperimentProperty

        #self.checkRequiredTag()


    def duplicate(self):
        param = ParameterInstance(None, self.description, self.requiredTags,
                                  self.relationship, self.isExperimentProperty)  
        return param
        


    def checkRequiredTag(self):
        from .ontoManager import OntoManager
        ## TODO: remove this line once tag ids have been corrected in all annotatiuons
        ontoMng  = OntoManager()
        dicData  = ontoMng.dics

        invDicData = {val:(nlx2ks[key] if key in nlx2ks else key) for key, val in dicData.items()}
        invDicData['Thalamus geniculate nucleus (lateral) principal neuron'] = 'NIFCELL:nlx_cell_20081203'
        invDicData["Young rat"] = "nlx_organ_109041"
        invDicData["Thalamus geniculate nucleus (lateral) interneuron"] = "NIFCELL:nifext_46"
        invDicData["Temperature"] = "PATO:0000146"
        invDicData["Sleep"] = "GO:0030431"
        invDicData['Burst firing pattern'] = "nlx_78803"
        invDicData['Cat'] = 'NIFORG:birnlex_113'
        invDicData['Thalamus reticular nucleus cell'] = 'NIFCELL:nifext_45'
        invDicData['Afferent'] = "NIFGA:nlx_anat_1010"
        invDicData['Morphology'] = 'PATO:0000051'

        for reqTag in self.requiredTags:

            #id = nlx2ks[id] if id in nlx2ks else id

            ## TODO: remove this line once tag ids have been corrected in all annotations
            if not dicData[reqTag.id] == reqTag.name:
                try:
                    if not reqTag.name in invDicData:
                        curies = getCuriesFromLabel(reqTag.name)
                        invDicData[reqTag.name] = curies[0]

                    print("Incompatibility between in " + str(reqTag.id) + ":" + str(reqTag.name) + ". Correcting to " +
                          str(invDicData[reqTag.name]) + ":" + str(dicData[invDicData[reqTag.name]]))
                    reqTag.id = invDicData[reqTag.name]
                    reqTag.name = dicData[reqTag.id]
                except:
                    raise
            ######



    def toJSON(self):
        json = {"id":self.id,
                "description":self.description.toJSON(),
                "requiredTags": [reqTag.toJSON() for reqTag in self.requiredTags],
                "isExperimentProperty":self.isExperimentProperty}

        if not self.relationship is None:
            json["relationship"] = self.relationship.toJSON()

        return json





    def applyTransform(self, key, valueFrom, valueTo, rule):
        param = self.duplicate()
        param.description.applyTransform(key, valueFrom, valueTo, rule)
        return param



    @property
    def unit(self):
        if isinstance(self.description.depVar, Variable):
            return self.description.depVar.unit
        elif isinstance(self.description.depVar, NumericalVariable):
            return self.description.depVar.values.unit
        else:
            raise TypeError


    @property
    def values(self):
        if isinstance(self.description.depVar, NumericalVariable):
            valuesObject = self.description.depVar.values
            if isinstance(valuesObject, ValuesSimple):
                return valuesObject.values
            elif isinstance(valuesObject, ValuesCompound):
                return [val.values for val in valuesObject.valueLst]
            else:
                raise TypeError
        elif isinstance(self.description.depVar, Variable):
            return None
        else:
            raise TypeError



    def centralTendancy(self, returnStat=False):  
        return self.description.centralTendancy(returnStat)

    def size(self, returnStat=False):
        return self.description.size(returnStat)

    def deviation(self, returnStat=False):        
        return self.description.deviation(returnStat)
        
        


    def indepCentralTendancies(self, paramName=None, paramId=None):
        
        if not paramId is None:
            paramName = getParameterTypeNameFromID(paramId)

        if not paramName is None:
            if not paramName in self.indepNames:
                return None
        
        centralTendancies = self.description.indepCentralTendancies()
            
        if paramName is None:
            return centralTendancies            
        
        return centralTendancies[self.indepNames == paramName]
        
        

    @property
    def means(self):
        if isinstance(self.description.depVar, NumericalVariable):
            valuesObject = self.description.depVar.values
            if isinstance(valuesObject, ValuesSimple):
                if valuesObject.statistic == "mean":
                    return valuesObject.values
                else:
                    return None
            elif isinstance(valuesObject, ValuesCompound):
                for val in valuesObject.valueLst:
                    if val.statistic == "mean":
                        return val.values
                return None
            else:
                raise TypeError
        elif isinstance(self.description.depVar, Variable):
            return None
        else:
            raise TypeError



    def valuesText(self, withUnit=False):
        if isinstance(self.description.depVar, NumericalVariable):
            return self.description.depVar.values.text(withUnit)
        elif isinstance(self.description.depVar, Variable):
            return None
        else:
            raise TypeError



    @property
    def indepUnits(self):
        if not hasattr(self.description, "indepVars"):
            return None
        indepVarUnits = []
        for indepVar in self.description.indepVars:
            if isinstance(indepVar, Variable):
                indepVarUnits.append(indepVar.unit)
            elif isinstance(indepVar, NumericalVariable):
                indepVarUnits.append(indepVar.values.unit)
        return indepVarUnits


    @property
    def indepValues(self):
        if not hasattr(self.description, "indepVars"):
            return None
        indepVarValues = []
        for indepVar in self.description.indepVars:
            if isinstance(indepVar, NumericalVariable):
                valuesObject = indepVar.values
                if isinstance(valuesObject, ValuesSimple):
                    indepVarValues.append(valuesObject.values)
                elif isinstance(valuesObject, ValuesCompound):
                    indepVarValues.append([val.values for val in valuesObject.valueLst])
                else:
                    raise TypeError
        return indepVarValues


    def getInterp1dValues(self, indepValues, indepName, kind='linear', statsToReturn=None):

        if isinstance(self.description.depVar, NumericalVariable):
            valuesObject = self.description.depVar.values
            
            if not indepName in self.indepNames:
                # No independant variables correspond to the one 
                # proposed for interpolating. We return the values
                # with no interpolation
                return self.values            
            
            if isinstance(valuesObject, ValuesSimple):
                y = self.values
                x = self.indepValues[self.indepNames.index(indepName)]
                f = interpolate.interp1d(x, y, kind=kind)
                return f(indepValues)


            elif isinstance(valuesObject, ValuesCompound):
                interVals = []
                for val in valuesObject.valueLst:
                    if statsToReturn is None or val.statistic in statsToReturn:
                        y = val.values
                        x = self.indepValues[self.indepNames.index(indepName)]
                        f = interpolate.interp1d(x, y, kind=kind)
                        interVals.append(f(indepValues))
                return interVals

    @property
    def indepTypeIds(self):
        if not hasattr(self.description, "indepVars"):
            return None
        indepVarTypes = []
        for indepVar in self.description.indepVars:
            if isinstance(indepVar, NumericalVariable):
                indepVarTypes.append(indepVar.typeId)
        return indepVarTypes



    @property
    def indepNames(self):
        if self.indepTypeIds is None:
            return None
        return [getParameterTypeNameFromID(typeId) for typeId in self.indepTypeIds]



    @property
    def typeId(self):
        return self.description.depVar.typeId

    @property
    def typeDesc(self):
        return self.description.type


    @staticmethod
    def fromJSON(jsonParams):
        params = []
        for jsonParam in jsonParams:

            if not "requiredTags" in jsonParam:
                # To convert older format annotations
                values = ValuesSimple([jsonParam["value"]], jsonParam["unit"])
                if jsonParam["id"] in ["BBP-01104", "BBP-00008"]:
                    typeId = "BBP-011001"
                    requiredTags    = [RequiredTag("nifext_8055", "Sodium current", "nifext_8054"), RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                elif jsonParam["id"] in ["BBP-01103", "BBP-00007"]:
                    typeId = "BBP-011001"
                    requiredTags = [RequiredTag("nifext_8056", "Potassium current", "nifext_8054"), RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                elif jsonParam["id"] in ["BBP-03003", "BBP-00003"]:
                    typeId = "BBP-121003"
                    requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                elif jsonParam["id"] in ["BBP-03004", "BBP-00005"]:
                    typeId = "BBP-121004"
                    requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                elif jsonParam["id"] in ["BBP-01001", "BBP-00004"]:
                    typeId = "BBP-040001"
                    requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                elif jsonParam["id"] in ["BBP-01300", "BBP-00006"]:
                    typeId = "BBP-022000"
                    requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                elif jsonParam["id"] in ["BBP-01402", "BBP-00009"] :
                    typeId = "BBP-030001"
                    requiredTags = [RequiredTag("BBP_nlx_0001", "Leak ionic current", "nifext_8054"), RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                elif jsonParam["id"] == "BBP-00043" :
                    typeId = "BBP-990004"
                    requiredTags = []
                elif jsonParam["id"] == "BBP-00041" :
                    typeId = "BBP-990304"
                    requiredTags = []
                elif jsonParam["id"] == "BBP-00042" :
                    typeId = "BBP-990003"
                    requiredTags = []
                elif jsonParam["id"] == "BBP-00012" :
                    typeId = "BBP-030003"
                    requiredTags = [RequiredTag("nifext_8054", "Transmembrane ionic current", "nifext_8054"), RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                elif jsonParam["id"] == "BBP-00068" :
                    typeId = "BBP-080004"
                    requiredTags = [RequiredTag("sao1813327414", "Cell", "sao1813327414")]
                else:
                    print(jsonParam["id"])
                    print(jsonParam)
                    print(getParameterTypeFromID(jsonParam["id"]))
                    raise ValueError
                param = ParameterInstance(None, ParamDescPoint(NumericalVariable(typeId, values)),
                                          requiredTags)
            else:
                if "relationship" in jsonParam:
                    relationship = Relationship.fromJSON(jsonParam["relationship"])
                else:
                    relationship = None

                if "isExperimentProperty" in jsonParam:
                    isExpProp = bool(jsonParam["isExperimentProperty"])
                else:
                    isExpProp = False

                param = ParameterInstance(jsonParam["id"],
                                          ParamDesc.fromJSON(jsonParam["description"]),
                                          [RequiredTag.fromJSON(s) for s in jsonParam["requiredTags"]],
                                          relationship, isExpProp)
            params.append(param)

        return params



    def __repr__(self):
        return str(self.__str__())

    def __str__(self):
        return str(self.toJSON())
        #return self.parseStr.format(self.typeID, self.unit, self.value, self.__annotID, self.__pubID, self.requirements)


    def __mul__(self, other):
        retPar = deepcopy(self)
        if isinstance(self.description.depVar, NumericalVariable):
            retPar.description.depVar.values = self.description.depVar.values*other
        else:
            raise TypeError
        return retPar

    __rmul__ = __mul__


    def __truediv__(self, other):
        retPar = deepcopy(self)
        if isinstance(self.description.depVar, NumericalVariable):
            retPar.description.depVar.values = self.description.depVar.values/other
        else:
            raise TypeError
        return retPar


    def __add__(self, other):
        retPar = deepcopy(self)
        if isinstance(self.description.depVar, NumericalVariable):
            retPar.description.depVar.values = self.description.depVar.values + other
        else:
            raise TypeError
        return retPar


    def __sub__(self, other):
        retPar = deepcopy(self)
        if isinstance(self.description.depVar, NumericalVariable):
            retPar.description.depVar.values = self.description.depVar.values - other
        else:
            raise TypeError
        return retPar


    def rescale(self, unit):
        retPar = deepcopy(self)
        if isinstance(self.description.depVar, NumericalVariable):
            retPar.description.depVar.values = self.description.depVar.values.rescale(unit)
        else:
            raise TypeError
        return retPar


    @property
    def name(self):
        return getParameterTypeNameFromID(self.typeId)


    @staticmethod
    def readIn(fileObject):
        try:
            return ParameterInstance.fromJSON(json.load(fileObject))
        except ValueError:
            if fileObject.read() == "":
                return []
            else:
                print("File content: ", fileObject.read())
                raise






