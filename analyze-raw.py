import json
import os
import argparse
import time
import numpy
from AdAnalysis import AdAnalysis, AutoDict
from aqualab.plot.mCdf import keyedCdf
from collections import defaultdict

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

def tree():
    return defaultdict(tree)

def parse_args():
    parser = argparse.ArgumentParser(
            description='analyze data from raw data files')
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
    data_dict = {}
    succeedList = []
    failList = []

    # prep directories
    raw_data_dir = os.path.join(data_dir, "raw")
    summaries_dir = os.path.join(data_dir, "summaries")
    raw_data_file_list = os.listdir(raw_data_dir)
    summaries_file_list = os.listdir(summaries_dir)
    fig_dir = os.path.join(data_dir, "figs2")
    if not os.path.isdir(fig_dir):
        os.mkdir(fig_dir)

    aa = AdAnalysis(summaries_file_list)

    # loop through summary files and build dicts
    for summary_file in summaries_file_list:
        #url_dict = tree()
        url_dict = AutoDict()

        if aa.isBlocking(summary_file):
            blocking_summary_file = summary_file
            # map summary files with ad-blocker to the 4 files in that group (non-blocking summary, blocking summary, non-blocking raw, blocking raw)
            nonblocking_summary_file = aa.getAdFileMatch(blocking_summary_file, summaries_file_list)
            ad_compare_dict[blocking_summary_file] = {'blocking_summary': blocking_summary_file, 'nonblocking_summary': nonblocking_summary_file}
            blocking_raw_file = aa.getRawFromSummary(blocking_summary_file, raw_data_file_list)
            if blocking_raw_file == None:
                print("Skipping file (getRawFromSummary returned None): "+blocking_raw_file)
                failList.append(blocking_raw_file)
                failList.append(nonblocking_raw_file)
                continue
            nonblocking_raw_file = aa.getAdFileMatch(blocking_raw_file, raw_data_file_list)
            ad_compare_dict[blocking_summary_file]['blocking_raw_file'] = blocking_raw_file
            ad_compare_dict[blocking_summary_file]['nonblocking_raw_file'] = nonblocking_raw_file

            # blocking summary file
            bsf_path = os.path.join(summaries_dir, blocking_summary_file)
            bsf = open(bsf_path, 'r')
            bs_obj = json.load(bsf)
            data_dict['blocking_summary'] = bs_obj
            bsf.close()

            # non-blocking summary file
            nsf_path = os.path.join(summaries_dir, nonblocking_summary_file)
            nsf = open(nsf_path, 'r')
            ns_obj = json.load(nsf)
            data_dict['nonblocking_summary'] = ns_obj
            nsf.close()

            # blocking raw file
            brf_path = os.path.join(raw_data_dir, blocking_raw_file)
            brf = open(brf_path, 'r')
            b_event_list = [json.loads(line) for line in brf.readlines()]
            data_dict['blocking_raw'] = {}
            data_dict['blocking_raw']['event_list'] = b_event_list
            brf.close()

            # nonblocking raw file
            nrf_path = os.path.join(raw_data_dir, nonblocking_raw_file)
            nrf = open(nrf_path, 'r')
            n_event_list = [json.loads(line) for line in nrf.readlines()]
            data_dict['nonblocking_raw'] = {}
            data_dict['nonblocking_raw']['event_list'] = n_event_list
            nrf.close()

            b_idx = aa.findFirstEventIdx(b_event_list, blocking_raw_file)
            n_idx = aa.findFirstEventIdx(n_event_list, nonblocking_raw_file)

            if b_idx == None:
                final_event = b_event_list[-1]
                try:
                    final_method = final_event["method"]
                except KeyError:
                    pass
                else:
                    if final_method == "Page.interstitialShown":
                        print("skipping file (Page.interstitialShown): "+blocking_summary_file)
                        failList.append(blocking_summary_file)
                        continue

            if n_idx == None:
                final_event = b_event_list[-1]
                try:
                    final_method = final_event["method"]
                except KeyError:
                    pass
                else:
                    if final_method == "Page.interstitialShown":
                        print("skipping file (Page.interstitialShown): "+nonblocking_summary_file)
                        failList.append(nonblocking_summary_file)
                        continue

            foundFirstReq = False
            firstTimestamp = None
            loadEventTimestamp_blocking = None
            reqID_dict = AutoDict()
            for idx in range(b_idx, len(b_event_list)):
                this_event = b_event_list[idx]
                if not foundFirstReq:
                    foundFirstReq, firstTimestamp = aa.getFirstTimestamp(this_event)
                if aa.isLoadEvent(this_event):
                    loadEventTimestamp_blocking = this_event["params"]["timestamp"]
                aa.processEvent(this_event, url_dict, "blocking", reqID_dict, firstTimestamp)

            foundFirstReq = False
            firstTimestamp = None
            loadEventTimestamp_nonblocking = None
            reqID_dict = AutoDict()
            for idx in range(n_idx, len(n_event_list)):
                this_event = n_event_list[idx]
                if not foundFirstReq:
                    foundFirstReq, firstTimestamp = aa.getFirstTimestamp(this_event)
                if aa.isLoadEvent(this_event):
                    loadEventTimestamp_nonblocking = this_event["params"]["timestamp"]
                aa.processEvent(this_event, url_dict, "nonblocking", reqID_dict, firstTimestamp)

            # print(url_dict.items()[0])
            # print(url_dict.items()[1])
            # print(url_dict.items()[2])
            blocking_list_timeStartToFinished = []
            nonblocking_list_timeStartToFinished = []
            for url, v in url_dict.items():
                print(url)
                print(v)
                aa.processUrl(url, url_dict, blocking_list_timeStartToFinished, nonblocking_list_timeStartToFinished,
                            loadEventTimestamp_blocking, loadEventTimestamp_nonblocking)

            # TODO cdf showing %objs loaded vs time for each file here
            succeedList.append(blocking_summary_file)
            succeedList.append(nonblocking_summary_file)
                
    end_time = time.clock()
    elapsed_time = end_time - start_time
    print("Actual total time: "+str(elapsed_time))
