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


class Trace:
    
    def __init__(self, x=None, y=None, marker="o", linestyle="solid"):
        
        if x is None:
            self.x = []
        else:
            self.x  = x
        
        if y is None: 
            self.y = []
        else:
            self.y = y
            
        self.marker = marker
        self.linestyle = linestyle


marker_desc_lst = ["o", "s", "*", "."]


def plotTraces(sample, x, panels=None, labels=None, nbCols=2, 
               figsize=None, useOnlyValid=True, markers_lbl=None,
               text_lbl=None, text_y_offset_lbl=None, **kwargs):
    
    # Get all the records as numerical traces so that they can all be plotted
    # using the same logic. 
    sample = sample.copy()
    sample.reformatAsNumericalTraces(x)
    if useOnlyValid:
        sampleDF = sample.validSample
    else:
        sampleDF = sample.sampleDF

    paramTraces = sampleDF["obj_parameter"].values
    if panels is not None:
        panels      = sampleDF[panels].values
    else:
        panels      = [""]*len(paramTraces)

    if labels is not None:
        labels = sampleDF[labels].values
    else:
        labels = [""] * len(paramTraces)

    if text_lbl is not None:
        texts = sampleDF[text_lbl].values
    else:
        texts = [""] * len(paramTraces)

    if text_y_offset_lbl is not None:
        text_y_offests = sampleDF[text_y_offset_lbl].values
    else:
        text_y_offests = [0] * len(paramTraces)

    if markers_lbl is not None:
        markers_values = sampleDF[markers_lbl].values
        marker_dict = {val: marker_desc_lst[np.unique(markers_values).tolist().index(val)] for val in
                       np.unique(markers_values)}
        markers = [marker_dict[val] for val in markers_values]
    else:
        marker_dict = {}
        markers = [marker_desc_lst[0]] * len(paramTraces)

    nbColors = len(matplotlib.rcParams['axes.color_cycle'])
    colors = {label:"C" + str(np.mod(no, nbColors)) for no, label in enumerate(np.unique(labels))}

    def getFigTrace(param, x, marker='o', linestyle="solid"):
        trace = Trace(x=param.indepCentralTendancies(paramName=x), 
                      y=param.centralTendancy(), 
                      marker=marker,
                      linestyle=linestyle)
        return trace
 

    def update_legend(axes):
        # Avoid repeating labels in the legend
        handles, labels = axes.get_legend_handles_labels()
        by_label = OrderedDict(zip(labels, handles))
        legend_handles = []
        legend_labels = list(by_label.keys())
        for legend_label, legend_handle in by_label.items():
            legend_handles.append(matplotlib.lines.Line2D([0, 1], [0, 1],
                                                         label=legend_label,
                                                         color=legend_handle.get_color()))

        for marker_label, marker_desc in marker_dict.items():
            line_test = matplotlib.lines.Line2D([0, 1], [0, 1],
                                                label=marker_label, color="k", marker=marker_desc, linewidth=0)
            legend_handles.append(line_test)
            legend_labels.append(marker_label)

        axes.legend(legend_handles, legend_labels)


    def plotTrace(trace, param, title="", xlim=None, context=None, text="",
                  text_y_offset=0, index=0, label=""):
        if context is None:
            fig, axes = plt.subplots()
        else:
            fig, axarr = context
            if isinstance(axarr, collections.Iterable):
                axes = axarr[int(index/nbCols), np.mod(index, nbCols)]
            else:
                axes = axarr

        if label == "":
            axes.plot(trace.x, trace.y, marker=trace.marker, linestyle=trace.linestyle, **kwargs)
        else:
            axes.plot(trace.x, trace.y, marker=trace.marker, linestyle=trace.linestyle,
                      color=colors[label], label=label, **kwargs)        

        if not xlim is None:
            axes.set_xlim(xlim)
        else:
            axes.set_xlim([min(trace.x) - 2.5, 
                           max(trace.x) + 2.5])

        axes.set_ylabel(param.name + " (" + param.unit + ")")
        axes.set_xlabel(x          + " (" + param.indepUnits[param.indepNames == x] + ")")
        axes.set_title(title)

        if text != "":
            axes.text(trace.x[-1]+3, trace.y[-1]+text_y_offset, text, color=colors[label])

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

    for paramTrace, panel, ref, marker, text, text_y_offset in \
            zip(paramTraces, panels, labels, markers, texts, text_y_offests):
        no = uniquePanels.index(panel)

        if panel in minX:
            minX[panel] = min(minX[panel], min(paramTrace.indepCentralTendancies(paramName=x)))
            maxX[panel] = max(maxX[panel], max(paramTrace.indepCentralTendancies(paramName=x)))        
        else:
            minX[panel] = min(paramTrace.indepCentralTendancies(paramName=x))
            maxX[panel] = max(paramTrace.indepCentralTendancies(paramName=x))

        minX[panel] -= (maxX[panel] - minX[panel])*0.03
        maxX[panel] += (maxX[panel] - minX[panel])*0.03 

        trace = getFigTrace(paramTrace, x, marker=marker)

        fig, axes = plotTrace(trace, paramTrace, xlim=[minX[panel], maxX[panel]],
                              title=panel, context=context, index=no, label=ref, text=text,
                              text_y_offset=text_y_offset)

        update_legend(axes)

    return context
