#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import os
import quantities as pq
import csv
from io import StringIO
from uuid import uuid1
from abc import abstractmethod
import pandas as pd
from scipy import interpolate
from copy import deepcopy
import numpy as np

from .tag import Tag, RequiredTag
from .tagUtilities import nlx2ks



statisticList  = ["raw", "mean", "median", "mode", "sem", "sd",  "var",
                  "CI_01", "CI_02.5", "CI_5", "CI_10", "CI_90", "CI_95",
                  "CI_97.5", "CI_99", "N", "min", "max", "other",
                  "deviation", "average"]


def unitIsValid(unit):
    try:
        pq.Quantity(1, unit)
    except:
        return False
    return True



class ParameterTypeTree:

    def __init__(self, value):
        if not isinstance(value, ParameterType):
            raise TypeError

        self.children = []
        self.value      = value

    def addChild(self, child):
        if not isinstance(child, ParameterTypeTree):
            raise TypeError

        self.children.append(child)


    def asList(self):
        paramTypeList = [value]
        for child in self.children:
            paramTypeList.extend(child.asList())
        return paramTypeList



    def isInTree(self, ID):
        if ID == self.value.ID:
            return True
        for child in self.children:
            if child.isInTree(ID):
                return True
        return False


    def getSubTree(self, ID):
        if ID == self.value.ID:
            return self
        for child in self.children:
            subTree = child.getSubTree(ID)
            if not subTree is None :
                return subTree
        return Noneprint("Start annotation imports...")



    def printTree(self, level = 0):
        print("="*level + " " + self.value.name)
        for child in self.children:
            child.printTree(level+1)


    @staticmethod
    def load(fileName = None, root = "BBP-000000"):

        def addChildren(tree, df):
            children = df[df["parentId"] == tree.value.ID]
            for index, row in children.iterrows():
                child = ParameterTypeTree(ParameterType(row["id"], row["parentId"],
                         row["name"], row["description"], eval(row["requiredTags"])))
                child = addChildren(child, df)
                tree.addChild(child)

            return tree

        df = ParameterTypeTree.getParamTypeDF(fileName)

        row = df[df["id"] == root]

        tree = ParameterTypeTree(ParameterType(row["id"][0], row["parentId"][0],
                                 row["name"][0], row["description"][0], eval(row["requiredTags"][0])))

        return addChildren(tree, df)


    @staticmethod
    def getParamTypeDF(fileName = None):

        if fileName is None:
            fileName = os.path.join(os.path.dirname(__file__), "modelingDictionary.csv")

        df = pd.read_csv(fileName, skip_blank_lines=True, comment="#",
                         delimiter=";", quotechar='"',
                         names=["id", "parentId", "name", "description", "requiredTags"])

        return df




def getParameterTypes(fileName = None):

    if fileName is None:
        fileName = os.path.join(os.path.dirname(__file__), "modelingDictionary.csv")

    with open(fileName, 'r') as f:
        lines = f.readlines()
    return [ParameterType.readIn(line) for line in lines if line.strip() != "" and line[0] != "#"]


def getParameterTypeNameFromID(ID, parameterTypes = None):
    if parameterTypes is None:
        parameterTypes = getParameterTypes()

    for param in parameterTypes:
        if param.ID == ID:
            return param.name

    return None


def getParameterTypeIDFromName(name, parameterTypes = None):
    if parameterTypes is None:
        parameterTypes = getParameterTypes()

    for param in parameterTypes:
        if param.name == name:
            return param.ID

    return None


def getParameterTypeFromID(ID, parameterTypes = None):
    if parameterTypes is None:
        parameterTypes = getParameterTypes()

    for param in parameterTypes:
        if param.ID == ID:
            return param

    return None


def getParameterTypeFromName(name, parameterTypes = None):
    if parameterTypes is None:
        parameterTypes = getParameterTypes()

    for param in parameterTypes:
        if param.name == name:
            return param

    return None





class Relationship:

    def __init__(self, type_, entity1, entity2):
        if not isinstance(type_, str):
            raise TypeError
        if not type_ in ["point", "directed", "undirected"]:
            raise ValueError
        if not isinstance(entity1, Tag):
            raise TypeError
        if type_ == "point":
            if not entity2 is None:
                raise ValueError
        elif not isinstance(entity2, Tag):
            raise TypeError

        self.type         = type_   # A value in : ["point", "directed", "undirected"]

        self.entity1    = entity1 # for directed relationship, it is the "from" entity

        self.entity2    = entity2 # for directed relationship, it is the "to" entity
                                  # for the point, it should keep a None value

    def __repr__(self):
        return str(self.toJSON())

    def __str__(self):
        return str(self.toJSON())

    def toJSON(self):
        if self.entity2 is None:
            return {"type":self.type, "entity1": self.entity1.toJSON(), "entity2":"None"}
        else:
            return {"type":self.type, "entity1": self.entity1.toJSON(), "entity2":self.entity2.toJSON()}

    @staticmethod
    def fromJSON(jsonString):
        return Relationship(jsonString["type"], Tag.fromJSON(jsonString["entity1"]),
                            None if jsonString["entity2"] == "None" else Tag.fromJSON(jsonString["entity2"]))




class ParameterType:

    def __init__(self, ID = None, parent = None, name = None, description = None, requiredTags = None):
        self.ID             = ID
        self.parent         = parent
        self.name           = name
        self.description    = description
        self.requiredTags   = requiredTags

        self.parseStr   = '"{}";"{}";"{}";"{}";{}'
        # ID;PARENT;NAME;DESCRIPTION;REQUIRED_TAGS



    @staticmethod
    def readIn(paramStr):
        parameter = ParameterType()
        reader = csv.reader(StringIO(paramStr) , delimiter=';')
        try:
            parameter.ID, parameter.parent, parameter.name, parameter.description, requiredTags = [item.strip() for item in list(reader)[0]]

            parameter.requiredTags = []
            for rootId, value in eval(requiredTags).items():
                if "||" in rootId:
                    _, id = rootId.split("||")
                else:
                    id = rootId
                parameter.requiredTags.append(RequiredTag(id, value, rootId))
        except ValueError:
            print("Problematic recording: ", paramStr)
            raise

        return parameter

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.parseStr.format(self.ID, self.parent, self.name, self.description, self.requiredTags)




class Values:

    @staticmethod
    def fromJSON(jsonString):
        if jsonString["type"] == "simple":
            return ValuesSimple.fromJSON(jsonString)
        elif jsonString["type"] == "compounded" or jsonString["type"] == "compound":
            return ValuesCompound.fromJSON(jsonString)
        else:
            raise ValueError

    @abstractmethod
    def toJSON(self):
        raise NotImplementedError


    @abstractmethod
    def __matOperator__(self, other, operatorFct):
        raise NotImplementedError

    @abstractmethod
    def rescale(unit):
        raise NotImplementedError


    def __mul__(self, other):
        return self.__matOperator__(other, "__mul__")

    def __truediv__(self, other):
        return self.__matOperator__(other, "__truediv__")

    def __add__(self, other):
        return self.__matOperator__(other, "__add__")

    def __sub__(self, other):
        return self.__matOperator__(other, "__sub__")





class ValuesSimple(Values):

    def __init__(self, values = None, unit= "dimensionless", statistic = "raw"):
        if not isinstance(unit, str):
            raise TypeError
        if not unitIsValid(unit):
            raise ValueError
        if not statistic in statisticList:
            raise ValueError("Invalid statistic '" + statistic +
                             "'. Statistics should take one of the following values: ",
                             str(statisticList))

        self.__values  = []

        if not values is None:
            self.values    = values
            
        self.unit      = unit
        self.statistic = statistic


    @property
    def values(self):
        return self.__values
       
    @values.setter
    def values(self, values):
        if not isinstance(values, (list, np.ndarray)):
            raise TypeError("Expected type for values is list, received type: " + str(type(values)))              
        self.__values = [float(val) for val in values]
        
        

    @staticmethod
    def fromJSON(jsonString):
        return ValuesSimple(jsonString["values"], jsonString["unit"], jsonString["statistic"])

    def toJSON(self):
        return {"type": "simple", "values": self.values, "unit": self.unit, "statistic":self.statistic}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())

    def text(self, withUnit=False):
        if len(self.values) == 1:
            valueTxt = str(self.values[0])
        else:
            valueTxt = str(self.values)

        if withUnit:
            return valueTxt + " " + self.textUnit()
        else:
            return valueTxt



    def textUnit(self):
        return self.unit



    def centralTendancy(self):
        if len(self.values) == 1:
            return self.values[0]
        else:
            return np.mean(self.values)


    def rescale(self, unit):
        retVal = deepcopy(self)
        if isinstance(unit, str):
            if self.unit != unit:
                quant = pq.Quantity(self.values, self.unit).rescale(unit)
                retVal.values = quant.base
                retVal.unit   = str(quant.dimensionality)
        return retVal


    def __matOperator__(self, other, operatorFct):

        if isinstance(other, (int, float)):
            values = np.array(self.values)
        elif isinstance(other, (pq.Quantity, ParameterInstance)):
            values = pq.Quantity(self.values, self.unit)
        else:
            raise TypeError

        functionList = {'__mul__': values.__mul__,
                        '__truediv__': values.__truediv__,
                        '__add__': values.__add__,
                        '__sub__': values.__sub__}

        retVal = deepcopy(self)
        if isinstance(other, (int, float)):
            retVal.values = functionList[operatorFct](other)
        elif isinstance(other, (pq.Quantity)):
            quant = functionList[operatorFct](other)
            retVal.values = quant.base
            retVal.unit   = str(quant.dimensionality)

        return retVal




class ValuesCompound(Values):

    def __init__(self, valueLst):
        if not isinstance(valueLst, list):
                raise TypeError
        for value in valueLst:
            if not isinstance(value, ValuesSimple):
                raise TypeError

        self.valueLst    = valueLst

    @staticmethod
    def fromJSON(jsonString):
        return ValuesCompound([Values.fromJSON(v) for v in jsonString["valueLst"]])

    def toJSON(self):
        return {"type": "compound", "valueLst": [v.toJSON() for v in self.valueLst]}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())



    def __matOperator__(self, other, operatorFct):

        retVal = deepcopy(self)
        for ind, value in enumerate(retVal.valueLst):
            if value.statistic != "N":
                retVal.valueLst[ind] = value.__matOperator__(other, operatorFct)
        return retVal


    def rescale(self, unit):
        retVal = deepcopy(self)
        for ind, value in enumerate(retVal.valueLst):
            if value.statistic != "N":
                retVal.valueLst[ind] = value.rescale(unit)
        return retVal


    def text(self, withUnit=False):

        stats = [value.statistic for value in self.valueLst]
        if "raw" in stats :
            return self.valueLst[stats.index("raw")].text(withUnit)

        if "sem" in stats :
            dev = "+/- " + self.valueLst[stats.index("sem")].text()
        elif "sd" in stats :
            dev = "+/- " + self.valueLst[stats.index("sd")].text()
        elif "var" in stats :
            dev = "+/- " + self.valueLst[stats.index("var")].text()
        elif "deviation" in stats :
            dev = "+/- " + self.valueLst[stats.index("deviation")].text()
        else:
            dev = ""

        if "min" in stats and "max" in stats :
            inter = "[" + self.valueLst[stats.index("min")].text() + " - " + self.valueLst[stats.index("max")].text() + "]"
        elif "CI_01" in stats and  "CI_99" in stats :
            inter = "[" + self.valueLst[stats.index("CI_01")].text() + " - " + self.valueLst[stats.index("CI_99")].text() + "]"
        elif "CI_02.5" in stats and  "CI_97.5" in stats :
            inter = "[" + self.valueLst[stats.index("CI_02.5")].text() + " - " + self.valueLst[stats.index("CI_97.5")].text() + "]"
        else:
            inter = ""

        if "N" in stats:
            sampSize = "(n=" + self.valueLst[stats.index("N")].text() +")"
        else:
            sampSize = ""

        if "mean" in stats :
            avg = self.valueLst[stats.index("mean")].text()
        elif "median" in stats :
            avg = self.valueLst[stats.index("median")].text()
        elif "mode" in stats :
            avg = self.valueLst[stats.index("mode")].text()
        elif "average" in stats :
            avg = self.valueLst[stats.index("average")].text()
        else:
            avg = ""


        if withUnit:
            return " ".join([avg, dev, inter, sampSize, self.textUnit()])
        else:
            return " ".join([avg, dev, inter, sampSize])


    def textUnit(self):

        stats = [value.statistic for value in self.valueLst]
        unit = ""
        if "raw" in stats :
            return self.valueLst[stats.index("raw")].textUnit()

        if "min" in stats and "max" in stats :
            unit = self.valueLst[stats.index("min")].unit
        elif "CI_01" in stats and  "CI_99" in stats :
            unit = self.valueLst[stats.index("CI_01")].unit
        elif "CI_02.5" in stats and  "CI_97.5" in stats :
            unit = self.valueLst[stats.index("CI_02.5")].unit

        if "mean" in stats :
            unit = self.valueLst[stats.index("mean")].unit
        elif "median" in stats :
            unit = self.valueLst[stats.index("median")].unit
        elif "mode" in stats :
            unit = self.valueLst[stats.index("mode")].unit
        elif "average" in stats :
            unit = self.valueLst[stats.index("average")].unit

        return unit








    def centralTendancy(self):

        stats = [value.statistic for value in self.valueLst]
        if "raw" in stats :
            return self.valueLst[stats.index("raw")].centralTendancy()

        for stat in ["mean", "median", "mode"]:
            if stat in stats :
                return self.valueLst[stats.index(stat)].centralTendancy()


        if "min" in stats and "max" in stats :
            return (self.valueLst[stats.index("min")].centralTendancy() +
                    self.valueLst[stats.index("max")].centralTendancy())/2.0
        if "CI_01" in stats and  "CI_99" in stats :
            return (self.valueLst[stats.index("CI_01")].centralTendancy() +
                    self.valueLst[stats.index("CI_99")].centralTendancy())/2.0
        if "CI_02.5" in stats and  "CI_97.5" in stats :
            return (self.valueLst[stats.index("CI_02.5")].centralTendancy() +
                    self.valueLst[stats.index("CI_97.5")].centralTendancy())/2.0

        return np.nan




    @property
    def unit(self):
        return self.textUnit()




class NumericalVariable:

    def __init__(self, typeId, values):
        if not isinstance(typeId, str):
            raise TypeError
        if not isinstance(values, Values):
            raise TypeError


        self.typeId = typeId
        self.values = values

    @staticmethod
    def fromJSON(jsonString):
        return NumericalVariable(jsonString["typeId"], Values.fromJSON(jsonString["values"]))

    def toJSON(self):
        return {"typeId": self.typeId, "values": self.values.toJSON()}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())






class Variable:

    def __init__(self, typeId, unit, statistic):
        self.typeId    = typeId
        self.unit      = unit
        self.statistic = statistic

    @staticmethod
    def fromJSON(jsonString):
        if not jsonString["statistic"] in statisticList:
            raise ValueError("Invalid statistic (" + jsonString["statistic"] + "). Statistics should take one of the following values: ", str(statisticList))

        return Variable(jsonString["typeId"], jsonString["unit"], jsonString["statistic"])

    def toJSON(self):
        return {"typeId": self.typeId, "unit": self.unit, "statistic":self.statistic}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())








class ParamDesc:
    @staticmethod
    @abstractmethod
    def fromJSON(jsonString):
        if jsonString["type"] == "function":
            return ParamDescFunction.fromJSON(jsonString)
        elif jsonString["type"] == "numericalTrace":
            return ParamDescTrace.fromJSON(jsonString)
        elif jsonString["type"] == "pointValue":
            return ParamDescPoint.fromJSON(jsonString)
        else:
            raise ValueError

    @abstractmethod
    def toJSON(self):
        raise NotImplementedError


class ParamDescPoint(ParamDesc):

    def __init__(self, depVar):
        if not isinstance(depVar, NumericalVariable):
            raise ValueError

        self.depVar          = depVar
        self.type            = "pointValue"

    @staticmethod
    def fromJSON(jsonString):
        return ParamDescPoint(NumericalVariable.fromJSON(jsonString["depVar"]))

    def toJSON(self):
        return {"type":"pointValue", "depVar": self.depVar.toJSON()}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())




class InvalidEquation(ValueError):
    def __init__(self, message="Invalid equation expression.", *args):
        self.message = message
        super(InvalidEquation, self).__init__(message, *args)




class ParamRef:

    def __init__(self, instanceId, paramTypeId):
        if not isinstance(instanceId, str):
            raise TypeError
        if not isinstance(paramTypeId, str):
            raise TypeError

        self.instanceId  = instanceId
        self.paramTypeId = paramTypeId

    @staticmethod
    def fromJSON(jsonString):
        return ParamRef(jsonString["instanceId"], jsonString["paramTypeId"])

    def toJSON(self):
        return {"instanceId" : self.instanceId, "paramTypeId": self.paramTypeId}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())








from numpy import *  # To make sure that the exec call in checkEquation() has access to all numpy functions
class ParamDescFunction(ParamDesc):

    def __init__(self, depVar, indepVars, parameterRefs, equation):
        if not isinstance(depVar, Variable):
            raise TypeError
        if not isinstance(indepVars, list):
            raise TypeError
        for item in indepVars:
            if not isinstance(item, Variable):
                raise TypeError
        if not isinstance(parameterRefs, list):
            raise TypeError
        for par in parameterRefs:
            if not isinstance(par, ParamRef):
                raise TypeError
        if not isinstance(equation, str):
            raise TypeError

        self.depVar        = depVar
        self.indepVars     = indepVars
        self.parameterRefs = parameterRefs
        self.equation      = equation
        self.type          = "function"

        self.checkEquation()


    def checkEquation(self):
        try:
            for var in self.indepVars:
                locals()[getParameterTypeNameFromID(var.typeId)] = 1.0
            for ref in self.parameterRefs:
                locals()[getParameterTypeNameFromID(ref.paramTypeId)] = 1.0

            exec(self.equation, globals(), locals())
            return

        except Exception as e:
            errorMsg = "Invalid equation expression : '" + self.equation + "'. Original exception raised: " + str(e)

        raise InvalidEquation(errorMsg)


    @staticmethod
    def fromJSON(jsonString):
        return ParamDescFunction(Variable.fromJSON(jsonString["depVar"]),
                                [Variable.fromJSON(s) for s in jsonString["indepVars"]],
                                [ParamRef.fromJSON(s) for s in jsonString["parameterRefs"]],
                                jsonString["equation"])

    def toJSON(self):
        return {"type":"function", "depVar": self.depVar.toJSON(),
                "indepVars"    : [var.toJSON() for var in self.indepVars],
                "parameterRefs": [par.toJSON() for par in self.parameterRefs],
                "equation":self.equation}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())






class ParamDescTrace(ParamDesc):

    def __init__(self, depVar, indepVars):
        if not isinstance(depVar, NumericalVariable):
            raise TypeError
        if not isinstance(indepVars, list):
            raise TypeError
        for item in indepVars:
            if not isinstance(item, NumericalVariable):
                raise TypeError

        self.depVar          = depVar
        self.indepVars       = indepVars
        self.type            = "numericalTrace"

    @staticmethod
    def fromJSON(jsonString):
        return ParamDescTrace(NumericalVariable.fromJSON(jsonString["depVar"]),
                             [NumericalVariable.fromJSON(s) for s in jsonString["indepVars"]])

    def toJSON(self):
        return {"type":"numericalTrace", "depVar": self.depVar.toJSON(),
                "indepVars": [var.toJSON() for var in self.indepVars]}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())





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



    def centralTendancy(self):
        if isinstance(self.description.depVar, NumericalVariable):
            valuesObject = self.description.depVar.values
            return valuesObject.centralTendancy()
        elif isinstance(self.description.depVar, Variable):
            return None
        else:
            raise TypeError



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


    def getInterp1dValues(self, indepValues, kind='linear', statsToReturn=None):

        if isinstance(self.description.depVar, NumericalVariable):
            valuesObject = self.description.depVar.values
            if isinstance(valuesObject, ValuesSimple):
                y = self.values
                x = self.indepValues[0]
                f = interpolate.interp1d(x, y, kind=kind)
                return f(indepValues)

            elif isinstance(valuesObject, ValuesCompound):
                interVals = []
                for val in valuesObject.valueLst:
                    if statsToReturn is None or val.statistic in statsToReturn:
                        y = val.values
                        x = self.indepValues[0]
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
            return fromJSON(json.load(fileObject))
        except ValueError:
            if fileObject.read() == "":
                return []
            else:
                print("File content: ", fileObject.read())
                raise






