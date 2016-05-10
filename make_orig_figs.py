import json
import os
import argparse
import time
import numpy
from numpy import percentile
from AdAnalysis import AdAnalysis
from aqualab.plot.mCdf import keyedCdf
import matplotlib.pyplot as plt
from scipy.stats import linregress
#from statsmodels.distributions.empirical_distribution import ECDF
import statsmodels.distributions
import csv

doScatterPlots = True
useCategories = True
orig_cdf_method = "diff_of_mins"

# For CDFs
colors = ['b', 'g', 'r', 'c', 'm', 'k']
markers = ['o', '^', 's', 'v', '+']
sep = ','
nl = '\n'
tab = "    "

MASTER_DICT = {
    "Final-numBlockedExplicitly": {"attr": "numBlockedExplicitly",},
    "DOM-numBlockedExplicitly": {"attr": "numBlockedExplicitly",},
    "Load-numBlockedExplicitly": {"attr": "numBlockedExplicitly",},
    "Final-numObjsRequested": {"attr": "numObjsRequested",},
    "DOM-numObjsRequested": {"attr": "numObjsRequested",},
    "Load-numObjsRequested": {"attr": "numObjsRequested",},
    "Final-responseReceivedCount": {"attr": "responseReceivedCount",},
    "DOM-responseReceivedCount": {"attr": "responseReceivedCount",},
    "Load-responseReceivedCount": {"attr": "responseReceivedCount",},
    "Final-time_DOMContent": {"attr": "time_DOMContent",},
    "Final-time_onLoad": {"attr": "time_onLoad",},
    "Final-time_finishLoad": {"attr": "time_finishLoad",},
    "DOM-cumulativeDataLength": {"attr": "cumulativeDataLength",},
    "Load-cumulativeDataLength": {"attr": "cumulativeDataLength",},
    "Final-cumulativeDataLength": {"attr": "cumulativeDataLength",},
    "DOM-cumulativeEncodedDataLength_LF": {"attr": "cumulativeEncodedDataLength_LF",},
    "Load-cumulativeEncodedDataLength_LF": {"attr": "cumulativeEncodedDataLength_LF",},
    "Final-cumulativeEncodedDataLength_LF": {"attr": "cumulativeEncodedDataLength_LF",},
    "DOM-cumulativeEncodedDataLength": {"attr": "cumulativeEncodedDataLength",},
    "Load-cumulativeEncodedDataLength": {"attr": "cumulativeEncodedDataLength",},
    "Final-cumulativeEncodedDataLength": {"attr": "cumulativeEncodedDataLength",},
    "Load-numBlockedExplicitly": {"attr": "numBlockedExplicitly",},
    "Load-responseReceivedCount": {"attr": "responseReceivedCount",},
    "Load-responseReceivedCount-False": {"attr": "responseReceivedCount",},
    "Load-numBlockedExplicitly-doPercent": {"attr": "numBlockedExplicitly",},
    "Load-responseReceivedCount-doPercent": {"attr": "responseReceivedCount",},
    "Load-responseReceivedCount-False-doPercent": {"attr": "responseReceivedCount",}
}

DICT_ORIG_CDFS = {
    "Final-numBlockedExplicitly": {
        "attr": "numBlockedExplicitly","x-label": "\nNumber of objects directly blocked", "file_flag": True, "event": "Final"},
    "DOM-numBlockedExplicitly": {
        "attr": "numBlockedExplicitly","x-label": "\nNumber of objects directly blocked", "file_flag": True, "event": "DOM"},
    "Load-numBlockedExplicitly": {
        "attr": "numBlockedExplicitly","x-label": "\nNumber of objects directly blocked", "file_flag": True, "event": "Load"},
    "Final-numObjsRequested": {
        "attr": "numObjsRequested","x-label": "\nNumber of extra objects requested", "file_flag": "Diff", "event": "Final"},
    "DOM-numObjsRequested": {
        "attr": "numObjsRequested","x-label": "\nNumber of extra objects requested", "file_flag": "Diff", "event": "DOM"},
    "Load-numObjsRequested": {
        "attr": "numObjsRequested","x-label": "\nNumber of extra objects requested", "file_flag": "Diff", "event": "Load"},
    "Final-responseReceivedCount": {
        "attr": "responseReceivedCount","x-label": "\nNumber of extra objects loaded", "file_flag": "Diff", "event": "Final"},
    "DOM-responseReceivedCount": {
        "attr": "responseReceivedCount","x-label": "\nNumber of extra objects loaded", "file_flag": "Diff", "event": "DOM"},
    "Load-responseReceivedCount": {
        "attr": "responseReceivedCount","x-label": "\nNumber of extra objects loaded", "file_flag": "Diff", "event": "Load"},
    "Final-time_DOMContent": {
        "attr": "time_DOMContent","x-label": "\nNumber of extra seconds to reach\nDOMContentLoaded event", "file_flag": "Diff", "event": "Final"},
    "Final-time_onLoad": {
        "attr": "time_onLoad","x-label": "\nNumber of extra seconds to reach\npage Load event", "file_flag": "Diff", "event": "Final"},
    "Final-time_finishLoad": {
        "attr": "time_finishLoad","x-label": "\nNumber of extra seconds to finish", "file_flag": "Diff", "event": "Final"},
    "DOM-cumulativeDataLength": {
        "attr": "cumulativeDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "DOM"},
    "Load-cumulativeDataLength": {
        "attr": "cumulativeDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Load"},
    "Final-cumulativeDataLength": {
        "attr": "cumulativeDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Final"},
    "DOM-cumulativeEncodedDataLength_LF": {
        "attr": "cumulativeEncodedDataLength_LF","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "DOM"},
    "Load-cumulativeEncodedDataLength_LF": {
        "attr": "cumulativeEncodedDataLength_LF","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Load"},
    "Final-cumulativeEncodedDataLength_LF": {
        "attr": "cumulativeEncodedDataLength_LF","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Final"},
    "DOM-cumulativeEncodedDataLength": {
        "attr": "cumulativeEncodedDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "DOM"},
    "Load-cumulativeEncodedDataLength": {
        "attr": "cumulativeEncodedDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Load"},
    "Final-cumulativeEncodedDataLength": {
        "attr": "cumulativeEncodedDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Final"}
}


DICT_RANGE_CDFS = {
    "Load-numBlockedExplicitly": {
        "attr": "numBlockedExplicitly", "y-label": "CDF of block count range",
        "file_flag": True, "doPercent": False},
    "Load-responseReceivedCount": {
        "attr": "responseReceivedCount", "y-label": "CDF of 'block' count range",
        "file_flag": "Diff", "doPercent": False},
    "Load-responseReceivedCount-False": {
        "attr": "responseReceivedCount", "y-label": "CDF of obj count range",
        "file_flag": False, "doPercent": False},
    "Load-numBlockedExplicitly-doPercent": {
        "attr": "numBlockedExplicitly", "y-label": "CDF of block count range",
        "file_flag": True, "doPercent": True},
    "Load-responseReceivedCount-doPercent": {
        "attr": "responseReceivedCount", "y-label": "CDF of 'block' count range",
        "file_flag": "Diff", "doPercent": True},
    "Load-responseReceivedCount-False-doPercent": {
        "attr": "responseReceivedCount", "y-label": "CDF of obj count range",
        "file_flag": False, "doPercent": True}
}

DICT_Y_VS_EXPLICITLY_BLOCKED = {
    "DOM-numObjsRequested": {
        "attr": "numObjsRequested", "y-label": "Num extra objs requested",
        "event": "DOM", "file_flag": "Diff"},
    "DOM-responseReceivedCount": {
        "attr": "responseReceivedCount", "y-label": "Num extra objs loaded",
        "event": "DOM", "file_flag": "Diff"},
    "DOM-cumulativeEncodedDataLength_LF": {
        "attr": "cumulativeEncodedDataLength_LF", "y-label": "Additional data transferred (KB)",
        "event": "DOM", "file_flag": "Diff"},
    "Final-time_DOMContent": {
        "attr": "time_DOMContent", "y-label": "Num extra seconds",
        "event": "Final", "file_flag": "Diff"},
    "Final-time_DOMContent_Both": {
        "attr": "time_DOMContent", "y-label": "Num seconds",
        "event": "Final", "file_flag": "Both"},

    "Load-numObjsRequested": {
        "attr": "numObjsRequested", "y-label": "Num extra objs requested",
        "event": "Load", "file_flag": "Diff"},
    "Load-responseReceivedCount": {
        "attr": "responseReceivedCount", "y-label": "Num extra objs loaded",
        "event": "Load", "file_flag": "Diff"},
    "Load-cumulativeEncodedDataLength_LF": {
        "attr": "cumulativeEncodedDataLength_LF", "y-label": "Additional data transferred (KB)",
        "event": "Load", "file_flag": "Diff"},
    "Final-time_onLoad": {
        "attr": "time_onLoad", "y-label": "Num extra seconds",
        "event": "Final", "file_flag": "Diff"},
    "Final-time_onLoad_Both": {
        "attr": "time_onLoad", "y-label": "Num seconds",
        "event": "Final", "file_flag": "Both"},

    "Final-numObjsRequested": {
        "attr": "numObjsRequested", "y-label": "Num extra objs requested",
        "event": "Final", "file_flag": "Diff"},
    "Final-responseReceivedCount": {
        "attr": "responseReceivedCount", "y-label": "Num extra objs loaded",
        "event": "Final", "file_flag": "Diff"},
    "Final-cumulativeEncodedDataLength_LF": {
        "attr": "cumulativeEncodedDataLength_LF", "y-label": "Additional data transferred (KB)",
        "event": "Final", "file_flag": "Diff"},
    "Final-time_finishLoad": {
        "attr": "time_finishLoad", "y-label": "Num extra seconds",
        "event": "Final", "file_flag": "Diff"},
    "Final-time_finishLoad_Both": {
        "attr": "time_finishLoad", "y-label": "Num seconds",
        "event": "Final", "file_flag": "Both"}
}

def shouldExclude(target_key, fig_key, datapoint, denominator):
    if target_key == fig_key:
        if datapoint >= 20 or denominator == 0:
            return True
    return False

def parse_args():
    parser = argparse.ArgumentParser(
            description='analyze data')
    parser.add_argument('data_dir', type=str,
                    help="The directory containing the data files to analyze.  Should contain subdirectories\n"+
                        "called 'raw', 'summaries', and 'log'.  Plots will be saved to a subdirectory called 'figs'")
    parser.add_argument('rank_cutoff', type=int,
                    help="All websites ranked higher than rank_cutoff in a given category will be included in the figure.  Websites ranked "+
                        "lower will be excluded.")
    parser.add_argument('--exclude_list_mobile', type=str,
                    help="A .json file containing mobile hostnames to exclude.  This is useful if, for example, "+
                    "you want to filter out certain websites that are known to be special cases or outliers.")
    parser.add_argument('--exclude_list_desktop', type=str,
                    help="A .json file containing desktop hostnames to exclude.  This is useful if, for example, "+
                    "you want to filter out certain websites that are known to be special cases or outliers.")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    start_time = time.clock()
    args = parse_args()
    data_dir = args.data_dir
    rank_cutoff = args.rank_cutoff
    exclude_list_mobile = args.exclude_list_mobile
    exclude_list_desktop = args.exclude_list_desktop

    # prep directories
    # fig_dir = os.path.join(data_dir, "figs-test-exclude-volatile/orig")
    # csv_dir = os.path.join(data_dir, "CSVs-test-exclude-volatile/orig")
    fig_dir = os.path.join(data_dir, "figs-test/orig")
    csv_dir = os.path.join(data_dir, "CSVs-test/orig")
    summaries_dir = os.path.join(data_dir, "summaries")
    summaries_file_list = os.listdir(summaries_dir)

    if not os.path.isdir(fig_dir):

        os.mkdir(fig_dir)

    aa = AdAnalysis(summaries_file_list)
    csv_files = os.listdir(csv_dir)

    for csv_file in csv_files:
        if csv_file[0] == '.':
            continue
        f_csv = open(os.path.join(csv_dir, csv_file), 'r')
        csv_reader = csv.reader(f_csv, delimiter=',')
        bar_plot = plt.figure(1, figsize=(8,3))
        cdf_plot = plt.figure(2, figsize=(4,3))
        i = 0
        means = []
        yerrs = []
        labels = []
        for row in csv_reader:
            if i%2 == 0:
                hostnames = row[1:]
            elif i%2 == 1:
                datapoints = row
                label = datapoints[0].split(' ')[0]
                datapoints = [float(y) for y in datapoints[1:]]
                avg = numpy.average(datapoints)
                means.append(avg)
                stdev = numpy.std(datapoints)
                yerrs.append(stdev)
                labels.append(label)

                linedata = statsmodels.distributions.ECDF(datapoints)
                #cdf_plot.plot(linedata.x, linedata.y, label=label, c=colors[i%len(colors)])#S marker=markers[i%len(markers)])
            i+=1
        f_csv.close()

        plt.figure(1)   # switch to bar plot
        fig, ax = plt.subplots()
        bar_locs = numpy.arange(len(means))
        width = 0.35
        bars = ax.bar(bar_locs, means, width, color='r', yerr=yerrs)
        ax.set_xticks(bar_locs + width)
        ax.set_xticklabels(labels, rotation="vertical")
        bar_fname = csv_file[:-4]+"-bar.pdf"
        bar_path = os.path.join(fig_dir, bar_fname)
        plt.savefig(bar_path, bbox_inches="tight")

        plt.figure(2)
        cdf_fname = csv_file[:-4]+"-cdf.pdf"
        cdf_path = os.path.join(fig_dir, cdf_fname)
        cdf_plot.savefig(cdf_path, bbox_inches="tight")
        plt.close()

    end_time = time.clock()
    elapsed_time = end_time - start_time
    print("Actual total time: "+str(elapsed_time))
