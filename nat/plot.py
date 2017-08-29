# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 09:29:00 2017

@author: oreilly
"""

import matplotlib.pyplot as plt
from collections import OrderedDict
import matplotlib
import collections
import numpy as np

def plotTraces(sample, x, panels=None, labels=None, nbCols=2, 
               figsize=None, useOnlyValid=True, **kwargs):
    
    # Get all the records as numerical traces so that they can all be plotted
    # using the same logic. 
    sample = sample.copy()
    sample.reformatAsNumericalTraces(x)
    if useOnlyValid:
        sampleDF = sample.validSample
    else:
        sampleDF = sample.sampleDF

    paramTraces = sampleDF["obj_parameter"].values
    if not panels is None:
        panels      = sampleDF[panels].values
    else:
        panels      = [""]*len(paramTraces)
    
    if not labels is None:
        labels = sampleDF[labels].values
    else:
        labels = [""]*len(paramTraces)

    nbColors = len(matplotlib.rcParams['axes.color_cycle'])
    colors = {label:"C" + str(np.mod(no, nbColors)) for no, label in enumerate(np.unique(labels))}

    def getFigTrace(param, title="", xlim=None, context=None, index=0, label=""):
        if context is None:
            fig, axes = plt.subplots()
        else:
            fig, axarr = context
            if isinstance(axarr, collections.Iterable):
                axes = axarr[int(index/nbCols), np.mod(index, nbCols)]
            else:
                axes = axarr

        if label == "":
            axes.plot(param.indepCentralTendancies(paramName=x, **kwargs), 
                      param.centralTendancy(), '-o')
        else:
            axes.plot(param.indepCentralTendancies(paramName=x), 
                      param.centralTendancy(), '-o', color=colors[label], label=label, **kwargs)        

        if not xlim is None:
            axes.set_xlim(xlim)
        else:
            axes.set_xlim([min(param.indepCentralTendancies(paramName=x)) - 2.5, 
                           max(param.indepCentralTendancies(paramName=x)) + 2.5])

        axes.set_ylabel(param.name + " (" + param.unit + ")")
        axes.set_xlabel(x          + " (" + param.indepUnits[param.indepNames == x] + ")")
        axes.set_title(title)

        # Avoid repeating labels in the legend
        handles, labels = axes.get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles))
        axes.legend(by_label.values(), by_label.keys())        
        
        return fig, axes    


    minX = {}
    maxX = {}

    uniquePanels = np.unique(panels).tolist()
    
    if figsize is None:
        figsize = (20, 6*int(np.ceil(len(uniquePanels)/nbCols)))
        
    if len(uniquePanels) > 1:
        context = plt.subplots(int(np.ceil(len(uniquePanels)/nbCols)), nbCols, 
                               figsize=figsize)
    else:
        context = plt.subplots(figsize=figsize)
    
    for paramTrace, panel, ref in zip(paramTraces, panels, labels):
        no = uniquePanels.index(panel)

        if panel in minX:
            minX[panel] = min(minX[panel], min(paramTrace.indepCentralTendancies(paramName=x)))
            maxX[panel] = max(maxX[panel], max(paramTrace.indepCentralTendancies(paramName=x)))        
        else:
            minX[panel] = min(paramTrace.indepCentralTendancies(paramName=x))
            maxX[panel] = max(paramTrace.indepCentralTendancies(paramName=x))

        minX[panel] -= (maxX[panel] - minX[panel])*0.03
        maxX[panel] += (maxX[panel] - minX[panel])*0.03 

        getFigTrace(paramTrace, xlim=[minX[panel], maxX[panel]], 
                          title=panel, context=context, index=no, label=ref)
                          
    return context