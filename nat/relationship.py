# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 16:32:25 2017

@author: oreilly
"""

from .tag import Tag

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

