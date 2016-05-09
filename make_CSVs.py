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
    list_out_dir = os.path.join(data_dir, "measured_lists")
    raw_data_dir = os.path.join(data_dir, "raw")
    summaries_dir = os.path.join(data_dir, "summaries")
    fig_dir = os.path.join(data_dir, "figs-test")
    csv_dir = os.path.join(data_dir, "CSVs-test")
    raw_data_file_list = os.listdir(raw_data_dir)
    summaries_file_list = os.listdir(summaries_dir)
    if not os.path.isdir(fig_dir):
        os.mkdir(fig_dir)
    if not os.path.isdir(csv_dir):
        os.mkdir(csv_dir)
    if not os.path.isdir(list_out_dir):
        os.mkdir(list_out_dir)

    aa = AdAnalysis(summaries_file_list)

    # create list of cdfs
    resolution = 0.1
    data_dict = {}
    for baseName in MASTER_DICT:
        if baseName in DICT_ORIG_CDFS:
            data_dict[baseName] = {}
            # make a list of cdfs
            attr = baseName.split('-',1)[1]
            DICT_ORIG_CDFS[baseName]["raw_data"] = {} # <cdf_key, (fname, raw_data)[]>

    # create dict of scatter plots
    for y_label in DICT_Y_VS_EXPLICITLY_BLOCKED:
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["x_vals"] = {}    # {phone_4g: [], computer-wifi: [], etc}
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["y_vals"] = {}    # {phone_4g: [], computer-wifi: [], etc}
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["hostnames"] = {}    # {phone_4g: [], computer-wifi: [], etc}

    # create dict of range CDFs
    for range_cdf in DICT_RANGE_CDFS:
        DICT_RANGE_CDFS[range_cdf]["raw_data"] = {} # <cdf_key, (fname, raw_data)[]>

    ad_compare_dict = {}
    chron_compare_dict = {}
    ad_chron_dict = {}      # {summary_file: list_of_pairs}
    new_exclude_dict_mobile = {}   # we are building in this script
    new_exclude_dict_desktop = {}   # we are building in this script

    if exclude_list_mobile != None:
        with open(exclude_list_mobile, 'r') as x_file:
            exclude_dict_mobile = json.load(x_file)
    else:
        exclude_dict_mobile = {}

    if exclude_list_desktop != None:
        with open(exclude_list_desktop, 'r') as x_file:
            exclude_dict_desktop = json.load(x_file)
    else:
        exclude_dict_desktop = {}

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

        # skip hostnames designated for exclusion
        hostname = aa.getHostname(key_file)
        device_type = aa.getDeviceTypeFromSummary(list_of_dicts[0][0])
        if device_type == "phone" and hostname in exclude_dict_mobile:
            print("phone "+hostname)
            continue
        if device_type == "computer" and hostname in exclude_dict_desktop:
            print("computer "+hostname)
            continue

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

            hostname = aa.getHostname(key_file)
            sample_num = aa.getSampleNum(key_file)

            # make Range CDFs
            if fig_key in DICT_RANGE_CDFS:
                if len(datapoint_blocking_list) > 0 and len(datapoint_nonblocking_list) > 0:
                    ff = DICT_RANGE_CDFS[baseName]["file_flag"]
                    if ff == "Diff":
                        range_datapoint = max_diff_datapoint - min_diff_datapoint
                        denominator = min_diff_datapoint
                    elif ff == True:
                        range_datapoint = max_blocking_datapoint - min_blocking_datapoint
                        denominator = min_blocking_datapoint
                    elif ff == False:
                        range_datapoint = max_nonblocking_datapoint - min_nonblocking_datapoint
                        denominator = min_nonblocking_datapoint

                    if DICT_RANGE_CDFS[fig_key]["doPercent"] == True:
                        try:
                            range_datapoint = (float(range_datapoint) / float(denominator))*100
                        except (ZeroDivisionError, TypeError):
                            range_datapoint = None

                    if shouldExclude("Load-responseReceivedCount-False-doPercent", fig_key, range_datapoint, denominator):
                        if device_type == "phone":
                            new_exclude_dict_mobile[hostname] = True
                        elif device_type == "computer":
                            new_exclude_dict_desktop[hostname] = True

                    label = str(ff)+'-'+hostname
                    if range_datapoint != None:
                        try:
                            DICT_RANGE_CDFS[baseName]["raw_data"][cdf_key].append((label, range_datapoint))
                        except KeyError:
                            DICT_RANGE_CDFS[baseName]["raw_data"][cdf_key] = [(label, range_datapoint)]
                        else:
                            pass

            if fig_key in DICT_ORIG_CDFS:
                label = hostname
                if len(datapoint_blocking_list) > 0 and len(datapoint_nonblocking_list) > 0:
                    key_suffix = " ("+orig_cdf_method+')'
                    if orig_cdf_method == "diff_of_mins":
                        datapoint = min_nonblocking_datapoint - min_blocking_datapoint
                    elif orig_cdf_method == "max_diff":
                        datapoint = max_diff_datapoint
                    elif orig_cdf_method == "median_diff":
                        datapoing = med_diff_datapoint

                    if useCategories:
                        for category in categories_dict:
                            if categories_dict[category] <= rank_cutoff:
                                try:
                                    DICT_ORIG_CDFS[fig_key]["raw_data"][category+key_suffix].append((label, datapoint))
                                except KeyError:
                                    DICT_ORIG_CDFS[fig_key]["raw_data"][category+key_suffix] = [(label, datapoint)]
                    else:
                        try:
                            DICT_ORIG_CDFS[fig_key]["raw_data"][cdf_key].append((label, datapoint))
                        except KeyError:
                            DICT_ORIG_CDFS[fig_key]["raw_data"][cdf_key] = [(label, datapoint)]

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

                    this_hostname = str(file_flag)+'-'+aa.getSampleNum(blocking_summary_dict["rawDataFile"])+blocking_summary_dict["hostname"]
                    if y_datapoint != None:
                        if "DataLength" in y_attr:
                            y_datapoint = y_datapoint/1000    # if it is data, show it in KB
                        if file_flag == "Both":
                        # getDatapoint returned a dict {"with-ads": datapoint, "no-ads": datapoint}
                            series_label = cdf_key+"-with-ads"
                            if y_datapoint["with-ads"] != None:
                                aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint["with-ads"])
                                aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)
                                aa.insertHostname(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, this_hostname)
                            series_label = cdf_key+"-no-ads"
                            if y_datapoint["no-ads"] != None:
                                aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint["no-ads"])
                                aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)
                                aa.insertHostname(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, this_hostname)
                        else:
                            series_label = cdf_key
                            aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint)
                            aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)
                            aa.insertHostname(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, this_hostname)

        # FINISH LOOPING THROUGH SCATTER PLOTS
    # FINISH LOOPING THROUGH FILES

    # plot range CDFs
    for range_cdf in DICT_RANGE_CDFS:
        i = 0
        directory = os.path.join(csv_dir, "range")
        if not os.path.isdir(directory):
            os.mkdir(directory)
        csv_fname = os.path.join(directory, "rng-"+range_cdf+".csv")
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
            # add data to csv
            csv_writer.writerow([' ']+fnames)
            csv_writer.writerow([cdf_key]+raw_data)
            i+=1
        fname = os.path.join(fig_dir, "rng-"+range_cdf+".pdf")
        # close csv
        f_csv.close()


    for cdf_name in DICT_ORIG_CDFS:
        directory = os.path.join(csv_dir, "orig-percentiles")
        if not os.path.isdir(directory):
            os.mkdir(directory)
        f_csv_percentile = open(os.path.join(directory, cdf_name+"-percentiles.csv"), 'w')
        directory = os.path.join(csv_dir, "orig")
        if not os.path.isdir(directory):
            os.mkdir(directory)
        csv_fname = os.path.join(directory, "orig-"+cdf_name+"-list.csv")
        f_csv = open(csv_fname, 'w')
        csv_writer = csv.writer(f_csv, delimiter=',')

        f_csv_percentile.write("key,avg,0,10,25,50,75,80,90,100"+nl)    # header row
        for cdf_key in DICT_ORIG_CDFS[cdf_name]["raw_data"]:
            # get data out of dict
            fname_and_raw_data = DICT_ORIG_CDFS[cdf_name]["raw_data"][cdf_key]
            fname_and_raw_data = sorted(fname_and_raw_data, key=lambda elem: elem[1])
            raw_data = [elem[1] for elem in fname_and_raw_data]
            fnames = [elem[0] for elem in fname_and_raw_data]

            # add data to csv list
            csv_writer.writerow([' ']+fnames)
            csv_writer.writerow([cdf_key]+raw_data)

            # add data to csv percentile
            f_csv_percentile.write(cdf_key+sep+str(numpy.average(raw_data))+sep+str(percentile(raw_data,0))+sep+str(percentile(raw_data,10))+sep+str(percentile(raw_data,25))+sep+str(percentile(raw_data, 50))+sep+str(percentile(raw_data, 75))+sep+str(percentile(raw_data, 80))+sep+str(percentile(raw_data,90))+sep+str(percentile(raw_data,100))+nl)
        f_csv.close()
        f_csv_percentile.close()


    if doScatterPlots:
        xlabel = "Num objs directly blocked"
        for scatterPlot in DICT_Y_VS_EXPLICITLY_BLOCKED:
            directory = os.path.join(csv_dir, "scatter")
            if not os.path.isdir(directory):
                os.mkdir(directory)
            f_csv = open(os.path.join(directory, scatterPlot+"-scatter.csv"), 'w')
            csv_writer = csv.writer(f_csv, delimiter=',')
            caption_x = 1.3
            caption_y = 0.5
            stats = ""
            ylabel = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["y-label"]
            file_flag = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["file_flag"]
            x_vals = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["x_vals"]
            y_vals = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["y_vals"]
            hostnames = DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["hostnames"]
            i = 0
            for series_label in x_vals:
                x = x_vals[series_label]
                y = y_vals[series_label]
                h = hostnames[series_label]
                csv_writer.writerow([series_label]+h)
                csv_writer.writerow(['numBlockedExplicitly']+x)
                csv_writer.writerow([ylabel]+y)
                try:
                    slope, intercept, rvalue, pvalue, stderr = linregress(x, y)
                except:
                    print(x)
                    print(y)
                    print(len(x))
                    print(len(y))
                stats+=(series_label+": slope="+"{0:.1f}".format(slope)+" intrcpt="+"{0:.1f}".format(intercept)+" corr="+"{0:.3f}".format(rvalue)+nl+(4*tab)+
                            " p="+"{0:.3f}".format(pvalue)+" stderr="+"{0:.3f}".format(stderr)+nl+nl)
            f_csv.close()

    # write the new exclude_list to file
    # but don't overwite if one was provided
    if args.exclude_list_mobile == None:
        new_exclude_mobile_path = os.path.join(list_out_dir, "exclude_list_mobile.json")
        with open(new_exclude_mobile_path, 'w') as f:
            json.dump(new_exclude_dict_mobile, f)
            
    if args.exclude_list_desktop == None:
        new_exclude_desktop_path = os.path.join(list_out_dir, "exclude_list_desktop.json")
        with open(new_exclude_desktop_path, 'w') as f:
            json.dump(new_exclude_dict_desktop, f)

    end_time = time.clock()
    elapsed_time = end_time - start_time
    print("Actual total time: "+str(elapsed_time))
