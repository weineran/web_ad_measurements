import json
import os
import argparse
import time
import numpy
from AdAnalysis import AdAnalysis
from aqualab.plot.mCdf import keyedCdf

LABEL_DICT = {"Final-numBlockedExplicitly": ["\nNumber of objects directly blocked", True, "Final"],
            "DOM-numBlockedExplicitly": ["\nNumber of objects directly blocked", True, "DOM"],
            "Load-numBlockedExplicitly": ["\nNumber of objects directly blocked", True, "Load"],
            "Final-numObjsRequested": ["\nNumber of extra objects requested with ad-blocker disabled", "Diff", "Final"],
            "DOM-numObjsRequested": ["\nNumber of extra objects requested with ad-blocker disabled", "Diff", "DOM"],
            "Load-numObjsRequested": ["\nNumber of extra objects requested with ad-blocker disabled", "Diff", "Load"],
            "Final-responseReceivedCount": ["\nNumber of extra responseReceived notifications with ad-blocker disabled", "Diff", "Final"],
            "DOM-responseReceivedCount": ["\nNumber of extra responseReceived notifications with ad-blocker disabled", "Diff", "DOM"],
            "Load-responseReceivedCount": ["\nNumber of extra responseReceived notifications with ad-blocker disabled", "Diff", "Load"],
            "Final-time_DOMContent": ["\nNumber of extra seconds to reach\nDOMContentLoaded event with ad-blocker disabled", "Diff", "Final"],
            "Final-time_onLoad": ["\nNumber of extra seconds to reach\npage Load event with ad-blocker disabled", "Diff", "Final"],
            "DOM-cumulativeEncodedDataLength_LF": ["\nAmount of extra data transferred with ad-blocker disabled (KB)", "Diff", "DOM"],
            "Load-cumulativeEncodedDataLength_LF": ["\nAmount of extra data transferred with ad-blocker disabled (KB)", "Diff", "Load"]}

# NOTE: other way to make CDF
# http://statsmodels.sourceforge.net/stable/generated/statsmodels.tools.tools.ECDF.html
# linedata = statsmodels.distributions.ECDF(raw_data)
# plt.plot(linedata.x, linedata.y)

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

    ad_compare_dict = {}
    chron_compare_dict = {}
    ad_chron_dict = {}

    # prep directories
    raw_data_dir = os.path.join(data_dir, "raw")
    summaries_dir = os.path.join(data_dir, "summaries")
    fig_dir = os.path.join(data_dir, "figs2")
    raw_data_file_list = os.listdir(raw_data_dir)
    summaries_file_list = os.listdir(summaries_dir)
    if not os.path.isdir(fig_dir):
        os.mkdir(fig_dir)

    aa = AdAnalysis(summaries_file_list)

    phone_measured_dict = {}
    computer_measured_dict= {}

    # loop through summary files and build dicts
    for summary_file in summaries_file_list:

        # make list of hostnames that have been measured
        this_hostname = aa.getHostname(summary_file)
        this_device = aa.getDevice(summary_file)
        if this_device == "phone":
            phone_measured_dict[this_hostname] = True
        elif this_device == "computer":
            computer_measured_dict[this_hostname] = True
        else:
            print("invalid device: "+str(this_device))
            raise

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

    # dump list of measured hostnames to file
    phone_list_path = os.path.join(data_dir, "phone_measured.json")
    computer_list_path = os.path.join(data_dir, "computer_measured.json")
    with open(phone_list_path, 'w') as f:
        json.dump(phone_measured_dict, f)
    with open(computer_list_path, 'w') as f:
        json.dump(computer_measured_dict, f)

    page_stats = {}

    resolution = 0.1

    cdf_list = []
    for baseName in LABEL_DICT:
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
            baseName = cdf.baseName
            attr = cdf.baseName.split('-',1)[1]
            file_flag = LABEL_DICT[baseName][1]
            event = LABEL_DICT[baseName][2]
            datapoint_sum = 0
            datapoint_count = 0

            # loop through pairs in the list
            datapoint_list = []
            for dict_pair in list_of_dicts:
                blocking_summary_dict = dict_pair[0]
                nonblocking_summary_dict = dict_pair[1]
            
                datapoint = aa.getDatapoint(attr, nonblocking_summary_dict, blocking_summary_dict, file_flag, event)
                if datapoint != None:
                    if "DataLength" in attr:
                        datapoint = datapoint/1000    # if it is data, show it in KB
                    #cdf.insert(cdf_key, datapoint)    # add datapoint to cdf

                    # increment sum and count in avg_dict
                    datapoint_list.append(datapoint)
                    datapoint_sum += datapoint
                    datapoint_count += 1

            # add average values to cdf
            try:
                #avg_datapoint = datapoint_sum/datapoint_count
                avg_datapoint = numpy.average(datapoint_list)
            except ZeroDivisionError:
                avg_datapoint = None

            med_datapoint = numpy.median(datapoint_list)

            if avg_datapoint != None and len(datapoint_list) != 0:
                #cdf.insert(cdf_key+" (avg)", avg_datapoint)
                cdf.insert(cdf_key+" (median)", med_datapoint)
                # for category in categories_dict:
                #     if categories_dict[category] <= rank_cutoff:
                #         cdf.insert(cdf_key+"-"+category+" (med)", med_datapoint)


    for cdf in cdf_list:
        cdf.plot(plotdir=fig_dir, title="", bbox_to_anchor=(1.05, 1), legend=2, lw=1.5, numSymbols=3)#styles={'linewidth':0.5})

    pageloadData2 = sorted(pageloadData, key=lambda elem: elem[1])
    for elem in pageloadData2:
        print(elem)

    end_time = time.clock()
    elapsed_time = end_time - start_time
    print("Actual total time: "+str(elapsed_time))
