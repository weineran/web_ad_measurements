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

doScatterPlots = False
useCategories = False

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
    "Final-numBlockedExplicitly": {"attr": "numBlockedExplicitly","x-label": "\nNumber of objects directly blocked", "file_flag": True, "event": "Final"},
    "DOM-numBlockedExplicitly": {"attr": "numBlockedExplicitly","x-label": "\nNumber of objects directly blocked", "file_flag": True, "event": "DOM"},
    "Load-numBlockedExplicitly": {"attr": "numBlockedExplicitly","x-label": "\nNumber of objects directly blocked", "file_flag": True, "event": "Load"},
    "Final-numObjsRequested": {"attr": "numObjsRequested","x-label": "\nNumber of extra objects requested", "file_flag": "Diff", "event": "Final"},
    "DOM-numObjsRequested": {"attr": "numObjsRequested","x-label": "\nNumber of extra objects requested", "file_flag": "Diff", "event": "DOM"},
    "Load-numObjsRequested": {"attr": "numObjsRequested","x-label": "\nNumber of extra objects requested", "file_flag": "Diff", "event": "Load"},
    "Final-responseReceivedCount": {"attr": "responseReceivedCount","x-label": "\nNumber of extra objects loaded", "file_flag": "Diff", "event": "Final"},
    "DOM-responseReceivedCount": {"attr": "responseReceivedCount","x-label": "\nNumber of extra objects loaded", "file_flag": "Diff", "event": "DOM"},
    "Load-responseReceivedCount": {"attr": "responseReceivedCount","x-label": "\nNumber of extra objects loaded", "file_flag": "Diff", "event": "Load"},
    "Final-time_DOMContent": {"attr": "time_DOMContent","x-label": "\nNumber of extra seconds to reach\nDOMContentLoaded event", "file_flag": "Diff", "event": "Final"},
    "Final-time_onLoad": {"attr": "time_onLoad","x-label": "\nNumber of extra seconds to reach\npage Load event", "file_flag": "Diff", "event": "Final"},
    "Final-time_finishLoad": {"attr": "time_finishLoad","x-label": "\nNumber of extra seconds to finish", "file_flag": "Diff", "event": "Final"},
    "DOM-cumulativeDataLength": {"attr": "cumulativeDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "DOM"},
    "Load-cumulativeDataLength": {"attr": "cumulativeDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Load"},
    "Final-cumulativeDataLength": {"attr": "cumulativeDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Final"},
    "DOM-cumulativeEncodedDataLength_LF": {"attr": "cumulativeEncodedDataLength_LF","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "DOM"},
    "Load-cumulativeEncodedDataLength_LF": {"attr": "cumulativeEncodedDataLength_LF","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Load"},
    "Final-cumulativeEncodedDataLength_LF": {"attr": "cumulativeEncodedDataLength_LF","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Final"},
    "DOM-cumulativeEncodedDataLength": {"attr": "cumulativeEncodedDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "DOM"},
    "Load-cumulativeEncodedDataLength": {"attr": "cumulativeEncodedDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Load"},
    "Final-cumulativeEncodedDataLength": {"attr": "cumulativeEncodedDataLength","x-label": "\nAdditional data transferred (KB)", "file_flag": "Diff", "event": "Final"}
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


def parse_args():
    parser = argparse.ArgumentParser(
            description='analyze data')
    parser.add_argument('data_dir', type=str,
                    help="The directory containing the data files to analyze.  Should contain subdirectories\n"+
                        "called 'raw', 'summaries', and 'log'.  Plots will be saved to a subdirectory called 'figs'")
    parser.add_argument('rank_cutoff', type=int,
                    help="All websites ranked higher than rank_cutoff in a given category will be included in the figure.  Websites ranked "+
                        "lower will be excluded.")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    start_time = time.clock()
    args = parse_args()
    data_dir = args.data_dir
    rank_cutoff = args.rank_cutoff

    # prep directories
    raw_data_dir = os.path.join(data_dir, "raw")
    summaries_dir = os.path.join(data_dir, "summaries")
    fig_dir = os.path.join(data_dir, "figs-category-5-5")
    csv_dir = os.path.join(data_dir, "CSVs-category-5-5")
    raw_data_file_list = os.listdir(raw_data_dir)
    summaries_file_list = os.listdir(summaries_dir)
    if not os.path.isdir(fig_dir):
        os.mkdir(fig_dir)
    if not os.path.isdir(csv_dir):
        os.mkdir(csv_dir)

    aa = AdAnalysis(summaries_file_list)

    # create list of cdfs
    resolution = 0.1
    data_dict = {}
    for baseName in MASTER_DICT:
        if baseName in DICT_ORIG_CDFS:
            data_dict[baseName] = {}
            # make a list of cdfs
            attr = baseName.split('-',1)[1]
            DICT_ORIG_CDFS[baseName]["cdf"] = keyedCdf(baseName=baseName, xlabel=aa.getXLabel(DICT_ORIG_CDFS, baseName), resolution=resolution)

    # create dict of scatter plots
    for y_label in DICT_Y_VS_EXPLICITLY_BLOCKED:
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["scatter_plot_fig"] = plt.figure(figsize=(8,13))
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["x_vals"] = {}    # {series_label1: [], series_label2: []}
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["y_vals"] = {}    # {series_label1: [], series_label2: []}

    # create dict of range CDFs
    for range_cdf in DICT_RANGE_CDFS:
        DICT_RANGE_CDFS[range_cdf]["range_cdf_fig"] = plt.figure(figsize=(8,6))
        DICT_RANGE_CDFS[range_cdf]["raw_data"] = {} # <cdf_key, (fname, raw_data)[]>

    ad_compare_dict = {}
    chron_compare_dict = {}
    ad_chron_dict = {}      # {summary_file: list_of_pairs}

    phone_measured_dict = {}
    computer_measured_dict= {}

    # loop through summary files and build dicts
    for summary_file in summaries_file_list:

        if aa.isBlocking(summary_file):
            # map summary files with ad-blocker to summary files without ad-blocker
            ad_file_match = aa.getAdFileMatch(summary_file, summaries_file_list)
            ad_compare_dict[summary_file] = ad_file_match
            if aa.isFirstSample(summary_file):
                # map first blocking summary file to chronological list of all pairs of (blocking, nonblocking)
                list_of_pairs = aa.getListOfPairs(summary_file, summaries_file_list)
                ad_chron_dict[summary_file] = list_of_pairs
        if aa.isFirstSample(summary_file):
            # map first summary file to list of all matching summary files
            chron_list = aa.getChronFileList(summary_file, summaries_file_list)
            chron_compare_dict[summary_file] = chron_list
    print(len(ad_chron_dict))
    #a = input("enter a num to continue")

    page_stats = {}

    pageloadData = []

    resp_list = None
    #for blocking_summary_file in ad_compare_dict:
    #    nonblocking_summary_file = ad_compare_dict[blocking_summary_file]
    print("num key_files: "+str(len(ad_chron_dict)))
    for key_file in ad_chron_dict:
        cdf_key = aa.getCDFKey(key_file)
        list_of_dicts = []

        # open a list of pairs of summary dictionaries
        for file_pair in ad_chron_dict[key_file]:
            blocking_summary_file = file_pair[0]
            nonblocking_summary_file = file_pair[1]

            if nonblocking_summary_file == None or blocking_summary_file == None:
                continue

            # open the pair of files
            full_path_blocking = os.path.join(summaries_dir, blocking_summary_file)
            f = open(full_path_blocking, 'r')
            #print("Loading "+blocking_summary_file)
            blocking_summary_dict = json.load(f)
            f.close()

            full_path_nonblocking = os.path.join(summaries_dir, nonblocking_summary_file)
            f = open(full_path_nonblocking, 'r')
            #print("Loading "+nonblocking_summary_file)
            nonblocking_summary_dict = json.load(f)
            f.close()

            list_of_dicts.append((blocking_summary_dict, nonblocking_summary_dict))

        # loop through all cdfs
        if len(list_of_dicts) > 0:
            categories_dict = list_of_dicts[0][0]['categories_and_ranks']
        else:
            continue

        for fig_key in MASTER_DICT:
            baseName = fig_key
            attr = MASTER_DICT[fig_key]["attr"]
            #file_flag = DICT_ORIG_CDFS[baseName]["file_flag"]
            #event = DICT_ORIG_CDFS[baseName]["event"]
            event = baseName.split('-',1)[0]
            datapoint_sum = 0
            datapoint_count = 0
            datapoint_blocking_sum = 0
            datapoint_blocking_count = 0
            datapoint_nonblocking_sum = 0
            datapoint_nonblocking_count = 0

            # loop through pairs in the list
            datapoint_diff_list = []         # if there are 5 samples, then there are 5 elems in list
            datapoint_blocking_list = []
            datapoint_nonblocking_list = []
            for dict_pair in list_of_dicts:
                blocking_summary_dict = dict_pair[0]
                nonblocking_summary_dict = dict_pair[1]
            
                datapoint_blocking = aa.getDatapoint(attr, nonblocking_summary_dict, blocking_summary_dict, True, event)
                datapoint_nonblocking = aa.getDatapoint(attr, nonblocking_summary_dict, blocking_summary_dict, False, event)
                try:
                    datapoint_diff = datapoint_nonblocking - datapoint_blocking
                except TypeError:
                    datapoint_diff = None

                datapoint_sum, datapoint_count = aa.appendDatapoint(datapoint_diff_list, datapoint_diff, datapoint_sum, datapoint_count, attr)
                datapoint_blocking_sum, datapoint_blocking_count = aa.appendDatapoint(datapoint_blocking_list, datapoint_blocking, datapoint_blocking_sum, datapoint_blocking_count, attr)
                datapoint_nonblocking_sum, datapoint_nonblocking_count = aa.appendDatapoint(datapoint_nonblocking_list, datapoint_nonblocking, datapoint_nonblocking_sum, datapoint_nonblocking_count, attr)

            if len(datapoint_blocking_list) > 0:
                med_blocking_datapoint = numpy.median(datapoint_blocking_list)
                min_blocking_datapoint = min(datapoint_blocking_list)
                max_blocking_datapoint = max(datapoint_blocking_list)
                avg_blocking_datapoint = numpy.average(datapoint_blocking_list)

            if len(datapoint_nonblocking_list) > 0:
                med_nonblocking_datapoint = numpy.median(datapoint_nonblocking_list)
                min_nonblocking_datapoint = min(datapoint_nonblocking_list)
                max_nonblocking_datapoint = max(datapoint_nonblocking_list)
                avg_nonblocking_datapoint = numpy.average(datapoint_nonblocking_list)

            if len(datapoint_diff_list) > 0:
                # get datapoints
                med_diff_datapoint = numpy.median(datapoint_diff_list)
                min_diff_datapoint = min(datapoint_diff_list)
                max_diff_datapoint = max(datapoint_diff_list)
                avg_diff_datapoint = numpy.average(datapoint_diff_list)

                # insert datapoints
                # cdf.insert(cdf_key+" (median)", med_diff_datapoint)
                # cdf.insert(cdf_key+" (min-dif)", min_diff_datapoint)
                # cdf.insert(cdf_key+" (max-dif)", max_diff_datapoint)
                # cdf.insert(cdf_key+" (avg)", avg_diff_datapoint)

                # add datapoints to datadict
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (med-dif)", med_diff_datapoint)
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (min-dif)", min_diff_datapoint)
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (max-dif)", max_diff_datapoint)
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (avg-dif)", avg_diff_datapoint)

            # make Range CDFs
            if fig_key in DICT_RANGE_CDFS:
                if len(datapoint_blocking_list) > 0 and len(datapoint_nonblocking_list) > 0:
                    ff = DICT_RANGE_CDFS[baseName]["file_flag"]
                    if ff == "Diff":
                        range_datapoint = max_diff_datapoint - min_diff_datapoint
                        min_datapoint = min_diff_datapoint
                    elif ff == True:
                        range_datapoint = max_blocking_datapoint - min_blocking_datapoint
                        min_datapoint = min_blocking_datapoint
                    elif ff == False:
                        range_datapoint = max_nonblocking_datapoint - min_nonblocking_datapoint
                        min_datapoint = min_nonblocking_datapoint

                    if DICT_RANGE_CDFS[fig_key]["doPercent"] == True:
                        try:
                            range_datapoint = (float(range_datapoint) / float(min_datapoint))*100
                        except (ZeroDivisionError, TypeError):
                            range_datapoint = None

                    if range_datapoint != None:
                        try:
                            DICT_RANGE_CDFS[baseName]["raw_data"][cdf_key].append((key_file, range_datapoint))
                        except KeyError:
                            DICT_RANGE_CDFS[baseName]["raw_data"][cdf_key] = [(key_file, range_datapoint)]
                            #DICT_RANGE_CDFS[range_cdf]["fnames"][cdf_key]= [key_file]
                        else:
                            #DICT_RANGE_CDFS[range_cdf]["fnames"][cdf_key].append(key_file)
                            pass

            if fig_key in DICT_ORIG_CDFS:
                cdf = DICT_ORIG_CDFS[fig_key]["cdf"]
                if len(datapoint_blocking_list) > 0 and len(datapoint_nonblocking_list) > 0:
                    diff_of_mins = min_nonblocking_datapoint - min_blocking_datapoint
                    #print(fig_key+": "+str(diff_of_mins))

                    cdf.insert(cdf_key+" (using min)", diff_of_mins)
                    aa.addDatatoDict(data_dict, baseName, cdf_key+" (using min)", diff_of_mins)

                if len(datapoint_diff_list) > 0:
                    if useCategories:
                        for category in categories_dict:
                            if categories_dict[category] <= rank_cutoff:
                                #cdf.insert(cdf_key+"-"+category+" (med)", med_diff_datapoint)
                                cdf.insert(category+" (med)", med_diff_datapoint)
                                try:
                                    #data_dict[baseName][cdf_key+"-"+category+" (med)"].append(med_diff_datapoint)
                                    data_dict[baseName][category+" (med)"].append(med_diff_datapoint)
                                except KeyError:
                                    #data_dict[baseName][cdf_key+"-"+category+" (med)"] = [med_diff_datapoint]
                                    data_dict[baseName][category+" (med)"] = [med_diff_datapoint]

        # FINISH LOOPING THROUGH CDFs

                
        # This loop is executed for each file
        # We add this file (or rather file group) to the plot data
        if doScatterPlots:
            for this_scatterPlot in DICT_Y_VS_EXPLICITLY_BLOCKED:
                event = DICT_Y_VS_EXPLICITLY_BLOCKED[this_scatterPlot]["event"]
                y_attr = DICT_Y_VS_EXPLICITLY_BLOCKED[this_scatterPlot]["attr"]
                file_flag = DICT_Y_VS_EXPLICITLY_BLOCKED[this_scatterPlot]["file_flag"]
                #cdf_key = aa.getDevice(key_file)
                cdf_key = aa.getCDFKey(key_file)
                for dict_pair in list_of_dicts:
                    blocking_summary_dict = dict_pair[0]
                    nonblocking_summary_dict = dict_pair[1]

                    x_datapoint = aa.getDatapoint("numBlockedExplicitly", nonblocking_summary_dict,
                                                blocking_summary_dict, True, event)
                    
                    y_datapoint = aa.getDatapoint(y_attr, nonblocking_summary_dict,
                                                blocking_summary_dict, file_flag, event)
                    if y_datapoint != None:
                        if "DataLength" in y_attr:
                            y_datapoint = y_datapoint/1000    # if it is data, show it in KB
                        if file_flag == "Both":
                        # getDatapoint returned a dict {"with-ads": datapoint, "no-ads": datapoint}
                            series_label = cdf_key+"-with-ads"
                            if y_datapoint["with-ads"] != None:
                                aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint["with-ads"])
                                aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)
                            series_label = cdf_key+"-no-ads"
                            if y_datapoint["no-ads"] != None:
                                aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint["no-ads"])
                                aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)
                        else:
                            series_label = cdf_key
                            aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint)
                            aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)

        # FINISH LOOPING THROUGH SCATTER PLOTS
    # FINISH LOOPING THROUGH FILES

    # plot range CDFs
    for range_cdf in DICT_RANGE_CDFS:
        i = 0
        csv_fname = os.path.join(csv_dir, "rng-"+range_cdf+".csv")
        f_csv = open(csv_fname, 'w')
        csv_writer = csv.writer(f_csv, delimiter=',')
        for cdf_key in DICT_RANGE_CDFS[range_cdf]["raw_data"]:
            # get data out of dict
            fname_and_raw_data = DICT_RANGE_CDFS[range_cdf]["raw_data"][cdf_key]
            fname_and_raw_data = sorted(fname_and_raw_data, key=lambda elem: elem[1])
            raw_data = [elem[1] for elem in fname_and_raw_data]
            fnames = [elem[0] for elem in fname_and_raw_data]
            # add data to plot cdf
            linedata = statsmodels.distributions.ECDF(raw_data)
            plt.plot(linedata.x, linedata.y, label=cdf_key, c=colors[i%len(colors)])#S marker=markers[i%len(markers)])
            # add data to csv
            csv_writer.writerow([' ']+fnames)
            csv_writer.writerow([cdf_key]+raw_data)
            i+=1
        # plot cdf
        plt.legend(loc="lower right")
        axes = plt.gca()
        axes.set_xlim([0,100])
        fname = os.path.join(fig_dir, "rng-"+range_cdf+".pdf")
        #DICT_RANGE_CDFS[range_cdf]["range_cdf_fig"].savefig(fname, bbox_inches="tight")
        plt.savefig(fname, bbox_inches="tight")
        plt.close()
        # close csv
        f_csv.close()


    for cdf_name in DICT_ORIG_CDFS:
        cdf = DICT_ORIG_CDFS[cdf_name]["cdf"]
        if useCategories:
            cdf.plot(plotdir=fig_dir, title="", legend="lower right", bbox_to_anchor=(1.05, 1), lw=1.5, numSymbols=3)#styles={'linewidth':0.5})
        else:
            cdf.plot(plotdir=fig_dir, title="", legend="lower right", lw=1.5, numSymbols=3)#styles={'linewidth':0.5}) bbox_to_anchor=(1.05, 1)
        f_csv = open(os.path.join(csv_dir, cdf.baseName+".csv"), 'w')
        f_csv.write("key,avg,0,10,25,50,75,80,90,100"+nl)
        for key in cdf._cdfs:
            #data = cdf._cdfs[key].getPdfData()[0]
            data = data_dict[cdf.baseName][key]
            f_csv.write(key+sep+str(numpy.average(data))+sep+str(percentile(data,0))+sep+str(percentile(data,10))+sep+str(percentile(data,25))+sep+str(percentile(data, 50))+sep+str(percentile(data, 75))+sep+str(percentile(data, 80))+sep+str(percentile(data,90))+sep+str(percentile(data,100))+nl)
        f_csv.close()

    if doScatterPlots:
        xlabel = "Num objs directly blocked"
        for scatterPlot in DICT_Y_VS_EXPLICITLY_BLOCKED:
            caption_x = 1.3
            caption_y = 0.5
            stats = ""
            print(scatterPlot)
            ylabel = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["y-label"]
            file_flag = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["file_flag"]
            x_vals = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["x_vals"]
            y_vals = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["y_vals"]
            # if scatterPlot == "Final-time_DOMContent":
            #     print(x_vals)
            #     print(y_vals)
            i = 0
            DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"] = {}
            for series_label in x_vals:
                DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i] = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["scatter_plot_fig"].add_subplot(len(x_vals),1,i+1)
                x = x_vals[series_label]
                y = y_vals[series_label]
                DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i].scatter(x, y, label=series_label, c=colors[i%len(colors)], marker=markers[i%len(markers)])
                DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i].legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
                try:
                    slope, intercept, rvalue, pvalue, stderr = linregress(x, y)
                except:
                    print(x)
                    print(y)
                    print(len(x))
                    print(len(y))
                stats+=(series_label+": slope="+"{0:.1f}".format(slope)+" intrcpt="+"{0:.1f}".format(intercept)+" corr="+"{0:.3f}".format(rvalue)+nl+(4*tab)+
                            " p="+"{0:.3f}".format(pvalue)+" stderr="+"{0:.3f}".format(stderr)+nl+nl)
                i+=1
            DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i-1].set_xlabel(xlabel)
            DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i-1].set_ylabel(ylabel)
            DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["scatter_plot_fig"].text(caption_x, caption_y, stats, verticalalignment="bottom")
            fname = os.path.join(fig_dir, "sct-"+scatterPlot+".pdf")
            DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["scatter_plot_fig"].savefig(fname, bbox_inches="tight")
        plt.close()


    pageloadData2 = sorted(pageloadData, key=lambda elem: elem[1])
    for elem in pageloadData2:
        print(elem)

    end_time = time.clock()
    elapsed_time = end_time - start_time
    print("Actual total time: "+str(elapsed_time))
