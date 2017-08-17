# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 16:29:38 2017

@author: oreilly
"""

from abc import abstractmethod
import warnings

from .modelingParameter import getParameterTypeIDFromName, getParameterTypeNameFromID
from .variable import NumericalVariable, Variable
from .values import ValuesSimple, ValuesCompound

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
        
        
    def applyTransform(self, key, valueFrom, valueTo, rule):

        if key == "Parameter name":
            key = "Parameter type ID"   
            valueFrom = getParameterTypeIDFromName(valueFrom)
            valueTo   = getParameterTypeIDFromName(valueTo)

        if key == "Parameter type ID":
            self.depVar.transformTypeId(valueFrom, valueTo, rule)
        else:
            raise ValueError("The key '"+ key +"' is not supported by ParameterInstance.applyTransform().")
        
        
        


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

    def centralTendancy(self):
        if isinstance(self.depVar, NumericalVariable):
            valuesObject = self.description.depVar.values
            return valuesObject.centralTendancy()
        elif isinstance(self.depVar, Variable):
            return None
        else:
            raise TypeError("Only NumericalVariable and Variable are valid types.")  


    def indepCentralTendancies(self):
        centralTendancies = []
        for indepVar in self.indepVars:
            if isinstance(indepVar, NumericalVariable):
                centralTendancies.append([indepVar.values.centralTendancy()])
            elif isinstance(indepVar, Variable):
                centralTendancies.append(None)
            else:
                raise TypeError("Only NumericalVariable and Variable are valid types.")             
        return centralTendancies




class InvalidEquation(Warning, ValueError):
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
            errorMsg = "Invalid equation expression : '" + self.equation + \
                       "'.\nConcern parameter ID:" + \
                       str(self.parameterRefs.instanceId) + \
                       "\n Original exception raised: " + str(e)
            warnings.warn(errorMsg)


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

    def centralTendancy(self):   
        raise NotImplemented("centralTendancy() is not implemented for the class ParamDescFunction.")

    def indepCentralTendancies(self):   
        raise NotImplemented("indepCentralTendancies() is not implemented for the class ParamDescFunction.")



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

        
    def centralTendancy(self):   
        """
        Compute a measure of central tendency for the parameter. In case of
        variables composed of ValuesSimple, the averaging operation is computed
        accross the list of values regardless of the statistic property. In case
        of compound variables, it is computed accross the list stored in each 
        item of the valueLst attribute.
        """            
        if isinstance(self.depVar, NumericalVariable):
            if isinstance(self.depVar.values, ValuesSimple):
                # In this case, we DO NOT call centralTendancy
                # because every point will be associated with 
                # a different value of independant variable 
                # and we don't want to average ACCROSS the
                # different values of the x-axis. We want to
                # take the central tendancy WITHIN each 
                # value of the x-axis. Doing so can only be done
                # when using ValuesCompound.
                return self.depVar.values.values
                
            elif isinstance(self.depVar.values, ValuesCompound):
                return [self.depVar.values.centralTendancy()]
                
            else:
                raise TypeError("Only ValuesSimple and ValuesCompound are valid types.")                  
        elif isinstance(self.depVar, Variable):
            return None
        else:
            raise TypeError("Only NumericalVariable and Variable are valid types.")          


    def indepCentralTendancies(self):
        centralTendancies = []
        for indepVar in self.indepVars:
            if isinstance(indepVar, NumericalVariable):
                if isinstance(indepVar.values, ValuesSimple):
                    # In this case, we DO NOT call centralTendancy
                    # because every point will be associated with 
                    # a different value of independant variable 
                    # and we don't want to average ACCROSS the
                    # different values of the x-axis. We want to
                    # take the central tendancy WITHIN each 
                    # value of the x-axis. Doing so can only be done
                    # when using ValuesCompound.
                    centralTendancies.append(indepVar.values.values)
                    
                elif isinstance(indepVar.values, ValuesCompound):
                    centralTendancies.append([indepVar.values.centralTendancy()])
                    
                else:
                    raise TypeError("Only ValuesSimple and ValuesCompound are valid types.")  
                    
            elif isinstance(indepVar, Variable):
                centralTendancies.append(None)
            else:
                raise TypeError("Only NumericalVariable and Variable are valid types.")             
        return centralTendancies


