import json
import os
import argparse
from AdAnalysis import AdAnalysis
from aqualab.plot.mCdf import keyedCdf

def parse_args():
    parser = argparse.ArgumentParser(
            description='analyze data')
    parser.add_argument('data_dir', type=str,
                    help="The directory containing the data files to analyze")
    parser.add_argument('fig_dir', type=str,
                    help="The directory to save the plots")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    data_dir = args.data_dir
    fig_dir = args.fig_dir

    ad_compare_dict = {}
    chron_compare_dict = {}

    data_file_list = os.listdir(data_dir)

    aa = AdAnalysis()

    # loop through list and build dicts
    for this_file in data_file_list:
        if aa.isLog(this_file):
            continue

        if aa.isBlocking(this_file):
            ad_file_match = aa.getAdFileMatch(this_file, data_file_list)
            ad_compare_dict[this_file] = ad_file_match
        if aa.isFirstSample(this_file):
            chron_list = aa.getChronFileList(this_file, data_file_list)
            chron_compare_dict[this_file] = chron_list

    print(ad_compare_dict)
    print(chron_compare_dict)

    page_stats = {}
    blocked_cdf = keyedCdf(baseName="blocked_cdf", 
        xlabel="Number of objects directly blocked")
    num_requested_diff_cdf = keyedCdf(baseName="num_requested_diff_cdf", 
        xlabel="Number of extra objects requested with ad-blocker disabled")
    num_loaded_diff_cdf = keyedCdf(baseName="num_loaded_diff_cdf", 
        xlabel="Number of extra objects loaded with ad-blocker disabled")
    onLoad_time_diff_cdf = keyedCdf(baseName="onLoad_time_diff_cdf", 
        xlabel="Number of extra seconds to load the page with ad-blocker disabled")

    resp_list = None
    for blocking_file in ad_compare_dict:
        nonblocking_file = ad_compare_dict[blocking_file]
        page_stats[blocking_file] = {}
        page_stats[nonblocking_file] = {}

        full_path_blocking = os.path.join(data_dir, blocking_file)
        with open(full_path_blocking, 'r') as f:
            print("Loading "+blocking_file)
            resp_list = json.load(f)

            num_blocked = aa.calcNumBlocked(resp_list)
            page_stats[blocking_file]['num_blocked'] = num_blocked
            blocked_cdf.insert('ad-blocker enabled', num_blocked)

            num_requested_b = aa.calcNumRequested(resp_list)
            page_stats[blocking_file]['num_requested'] = num_requested_b

            num_loaded_b = aa.calcNumLoaded(resp_list)
            page_stats[blocking_file]['num_loaded'] = num_loaded_b

            onLoad_time_b = aa.calcOnLoadTime(resp_list)
            page_stats[blocking_file]['onLoad_time'] = onLoad_time_b

        full_path_nonblocking = os.path.join(data_dir, nonblocking_file)
        with open(full_path_nonblocking, 'r') as f:
            print("Loading "+nonblocking_file)
            resp_list = json.load(f)

            num_requested_n = aa.calcNumRequested(resp_list)
            page_stats[nonblocking_file]['num_requested'] = num_requested_n
            num_requested_diff = num_requested_n - num_requested_b
            num_requested_diff_cdf.insert('label', num_requested_diff)

            num_loaded_n = aa.calcNumLoaded(resp_list)
            page_stats[nonblocking_file]['num_loaded'] = num_loaded_n
            num_loaded_diff = num_loaded_n - num_loaded_b
            num_loaded_diff_cdf.insert('label', num_loaded_diff)

            onLoad_time_n = aa.calcOnLoadTime(resp_list)
            page_stats[nonblocking_file]['onLoad_time'] = onLoad_time_n
            try:
                onload_time_diff = onLoad_time_n - onLoad_time_b
            except TypeError:
                pass
            else:
                onLoad_time_diff_cdf.insert('label', onload_time_diff)

    print(page_stats)
    blocked_cdf.plot(plotdir=fig_dir, title="")
    num_requested_diff_cdf.plot(plotdir=fig_dir, title="")
    num_loaded_diff_cdf.plot(plotdir=fig_dir, title="")
    onLoad_time_diff_cdf.plot(plotdir=fig_dir, title="")
