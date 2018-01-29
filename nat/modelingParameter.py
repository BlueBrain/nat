#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import csv
from io import StringIO

import pandas as pd

from nat.utils import data_path
from .tag import RequiredTag


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
        paramTypeList = [self.value]
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
        return None



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
            fileName = data_path("modelingDictionary.csv")

        df = pd.read_csv(fileName, skip_blank_lines=True, comment="#",
                         delimiter=";", quotechar='"',
                         names=["id", "parentId", "name", "description", "requiredTags"])

        return df




def getParameterTypes(fileName = None):

    if fileName is None:
        fileName = data_path("modelingDictionary.csv")

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



