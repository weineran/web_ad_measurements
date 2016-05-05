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

LABEL_DICT = {
    "Final-numBlockedExplicitly": ["\nNumber of objects directly blocked", True, "Final"],
    "DOM-numBlockedExplicitly": ["\nNumber of objects directly blocked", True, "DOM"],
    "Load-numBlockedExplicitly": ["\nNumber of objects directly blocked", True, "Load"],
    "Final-numObjsRequested": ["\nNumber of extra objects requested", "Diff", "Final"],
    "DOM-numObjsRequested": ["\nNumber of extra objects requested", "Diff", "DOM"],
    "Load-numObjsRequested": ["\nNumber of extra objects requested", "Diff", "Load"],
    "Final-responseReceivedCount": ["\nNumber of extra objects loaded", "Diff", "Final"],
    "DOM-responseReceivedCount": ["\nNumber of extra objects loaded", "Diff", "DOM"],
    "Load-responseReceivedCount": ["\nNumber of extra objects loaded", "Diff", "Load"],
    "Final-time_DOMContent": ["\nNumber of extra seconds to reach\nDOMContentLoaded event", "Diff", "Final"],
    "Final-time_onLoad": ["\nNumber of extra seconds to reach\npage Load event", "Diff", "Final"],
    "Final-time_finishLoad": ["\nNumber of extra seconds to finish", "Diff", "Final"],
    "DOM-cumulativeDataLength": ["\nAdditional data transferred (KB)", "Diff", "DOM"],
    "Load-cumulativeDataLength": ["\nAdditional data transferred (KB)", "Diff", "Load"],
    "Final-cumulativeDataLength": ["\nAdditional data transferred (KB)", "Diff", "Final"],
    "DOM-cumulativeEncodedDataLength_LF": ["\nAdditional data transferred (KB)", "Diff", "DOM"],
    "Load-cumulativeEncodedDataLength_LF": ["\nAdditional data transferred (KB)", "Diff", "Load"],
    "Final-cumulativeEncodedDataLength_LF": ["\nAdditional data transferred (KB)", "Diff", "Final"],
    "DOM-cumulativeEncodedDataLength": ["\nAdditional data transferred (KB)", "Diff", "DOM"],
    "Load-cumulativeEncodedDataLength": ["\nAdditional data transferred (KB)", "Diff", "Load"],
    "Final-cumulativeEncodedDataLength": ["\nAdditional data transferred (KB)", "Diff", "Final"]
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

# NOTE: other way to make CDF
# http://statsmodels.sourceforge.net/stable/generated/statsmodels.tools.tools.ECDF.html
# linedata = statsmodels.distributions.ECDF(raw_data)
# plt.plot(linedata.x, linedata.y)

useCategories = False

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

    # create dict of scatter plots
    for y_label in DICT_Y_VS_EXPLICITLY_BLOCKED:
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["scatter_plot_fig"] = plt.figure(figsize=(8,13))
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["x_vals"] = {}    # {series_label1: [], series_label2: []}
        DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["y_vals"] = {}    # {series_label1: [], series_label2: []}

    ad_compare_dict = {}
    chron_compare_dict = {}
    ad_chron_dict = {}      # {summary_file: list_of_pairs}

    # prep directories
    raw_data_dir = os.path.join(data_dir, "raw")
    summaries_dir = os.path.join(data_dir, "summaries")
    fig_dir = os.path.join(data_dir, "figs-min-dif")
    csv_dir = os.path.join(data_dir, "CSVs-min-dif")
    raw_data_file_list = os.listdir(raw_data_dir)
    summaries_file_list = os.listdir(summaries_dir)
    if not os.path.isdir(fig_dir):
        os.mkdir(fig_dir)
    if not os.path.isdir(csv_dir):
        os.mkdir(csv_dir)

    aa = AdAnalysis(summaries_file_list)

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

    resolution = 0.1
    data_dict = {}

    # create list of cdfs
    cdf_list = []
    for baseName in LABEL_DICT:
        data_dict[baseName] = {}
        # make a list of cdfs
        attr = baseName.split('-',1)[1]
        cdf_list.append(keyedCdf(baseName=baseName, xlabel=aa.getXLabel(LABEL_DICT, baseName), resolution=resolution))

    pageloadData = []

    resp_list = None
    #for blocking_summary_file in ad_compare_dict:
    #    nonblocking_summary_file = ad_compare_dict[blocking_summary_file]
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
            print("Loading "+blocking_summary_file)
            blocking_summary_dict = json.load(f)
            f.close()

            full_path_nonblocking = os.path.join(summaries_dir, nonblocking_summary_file)
            f = open(full_path_nonblocking, 'r')
            print("Loading "+nonblocking_summary_file)
            nonblocking_summary_dict = json.load(f)
            f.close()

            list_of_dicts.append((blocking_summary_dict, nonblocking_summary_dict))

        # loop through all cdfs
        if len(list_of_dicts) > 0:
            categories_dict = list_of_dicts[0][0]['categories_and_ranks']

        for cdf in cdf_list:
            # TODO make scatter plots of numBlockedExplicitly vs page load time, responseReceived diff, data diff
            baseName = cdf.baseName
            attr = cdf.baseName.split('-',1)[1]
            file_flag = LABEL_DICT[baseName][1]
            event = LABEL_DICT[baseName][2]
            datapoint_sum = 0
            datapoint_count = 0
            datapoint_blocking_sum = 0
            datapoint_blocking_count = 0
            datapoint_nonblocking_sum = 0
            datapoint_nonblocking_count = 0

            # loop through pairs in the list
            datapoint_list = []         # if there are 5 samples, then there are 5 elems in list
            datapoint_blocking_list = []
            datapoint_nonblocking_list = []
            for dict_pair in list_of_dicts:
                blocking_summary_dict = dict_pair[0]
                nonblocking_summary_dict = dict_pair[1]
            
                datapoint = aa.getDatapoint(attr, nonblocking_summary_dict, blocking_summary_dict, file_flag, event)
                datapoint_blocking = aa.getDatapoint(attr, nonblocking_summary_dict, blocking_summary_dict, True, event)
                datapoint_nonblocking = aa.getDatapoint(attr, nonblocking_summary_dict, blocking_summary_dict, False, event)

                datapoint_sum, datapoint_count = aa.appendDatapoint(datapoint_list, datapoint, datapoint_sum, datapoint_count, attr)
                datapoint_blocking_sum, datapoint_blocking_count = aa.appendDatapoint(datapoint_blocking_list, datapoint_blocking, datapoint_blocking_sum, datapoint_blocking_count, attr)
                datapoint_nonblocking_sum, datapoint_nonblocking_count = aa.appendDatapoint(datapoint_nonblocking_list, datapoint_nonblocking, datapoint_nonblocking_sum, datapoint_nonblocking_count, attr)
                

            # add average values to cdf
            try:
                avg_datapoint = datapoint_sum/datapoint_count
            except ZeroDivisionError:
                avg_datapoint = None

            if len(datapoint_list) > 0:
                # insert datapoints
                # med_datapoint = numpy.median(datapoint_list)
                # cdf.insert(cdf_key+" (median)", med_datapoint)
                # min_datapoint = min(datapoint_list)
                # cdf.insert(cdf_key+" (min-dif)", min_datapoint)
                # max_datapoint = max(datapoint_list)
                # cdf.insert(cdf_key+" (max-dif)", max_datapoint)
                # avg_datapoint = numpy.average(datapoint_list)
                #cdf.insert(cdf_key+" (avg)", avg_datapoint)

                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (median)", med_datapoint)
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (min-dif)", min_datapoint)
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (max-dif)", max_datapoint)

                if useCategories:
                    for category in categories_dict:
                        if categories_dict[category] <= rank_cutoff:
                            #cdf.insert(cdf_key+"-"+category+" (med)", med_datapoint)
                            cdf.insert(category+" (med)", med_datapoint)
                            try:
                                #data_dict[baseName][cdf_key+"-"+category+" (med)"].append(med_datapoint)
                                data_dict[baseName][category+" (med)"].append(med_datapoint)
                            except KeyError:
                                #data_dict[baseName][cdf_key+"-"+category+" (med)"] = [med_datapoint]
                                data_dict[baseName][category+" (med)"] = [med_datapoint]

            if len(datapoint_blocking_list) > 0 and len(datapoint_nonblocking_list) > 0:
                min_blocking = min(datapoint_blocking_list)
                min_nonblocking = min(datapoint_nonblocking_list)
                min_datapoint = min_nonblocking - min_blocking

                cdf.insert(cdf_key+" (using min)", min_datapoint)
                aa.addDatatoDict(data_dict, baseName, cdf_key+" (using min)", min_datapoint)
                

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

    last_cdf = None

    sep = ','
    nl = '\n'
    tab = "    "
    for cdf in cdf_list:
        last_cdf = cdf
        if useCategories:
            cdf.plot(plotdir=fig_dir, title="", legend="lower right", bbox_to_anchor=(1.05, 1), lw=1.5, numSymbols=3)#styles={'linewidth':0.5})
        else:
            cdf.plot(plotdir=fig_dir, title="", legend="lower right", lw=1.5, numSymbols=3)#styles={'linewidth':0.5}) bbox_to_anchor=(1.05, 1)
        f_csv = open(os.path.join(csv_dir, cdf.baseName+".csv"), 'w')
        f_csv.write("key,0,10,25,50,75,90,100"+nl)
        for key in cdf._cdfs:
            #data = cdf._cdfs[key].getPdfData()[0]
            data = data_dict[cdf.baseName][key]
            f_csv.write(key+sep+str(percentile(data,0))+sep+str(percentile(data,10))+sep+str(percentile(data,25))+sep+str(percentile(data, 50))+sep+str(percentile(data, 75))+sep+str(percentile(data,90))+sep+str(percentile(data,100))+nl)
        f_csv.close()

    # print(last_cdf._cdfs)
    # for key in last_cdf._cdfs:
    #     print(key)
    #     print(last_cdf._cdfs[key].getData())
    colors = ['b', 'g', 'r', 'c', 'm', 'k']
    markers = ['o', '^', 's', 'v', '+']
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
