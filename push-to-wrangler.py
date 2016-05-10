# Apparently cattle needs python 2.7.8 (2.7.11 doesn't work)

import os
import time
import argparse
import json
from wranglib.cattle import init as initcattle
from wranglib.cattle import report
from AdAnalysis import AdAnalysis

def parse_args():
    parser = argparse.ArgumentParser(
            description='Push data in the specified directory to Wrangler')
    parser.add_argument('data_dir', type=str,
                    help="The directory containing the data to be pushed to Wrangler.")
    parser.add_argument('num_samples_in_set', type=int,
                    help="The number of data samples (page loads) taken for each page.")
    parser.add_argument('log_filename', type=str,
                    help="The filename of the log associated with the data collection.")
    return parser.parse_args()

def wrapUp(start_time, succeeded_list):
    with open('wrangler_log-4.txt', 'w') as f:
        json.dump(succeeded_list, f)
        f.write('\n')
    end_time = time.time()
    time_elapsed = (end_time - start_time)
    print("time_elapsed: "+str(time_elapsed))

if __name__ == "__main__":
    # Get arguments
    start_time = time.time()
    args = parse_args()
    data_dir = args.data_dir
    num_samples_in_set = args.num_samples_in_set
    log_fname = args.log_filename

    initcattle(project="web-ads", workingdir=".", port=8088, use_ssl=True)

    ad_compare_dict = {}
    succeeded_list = []

    raw_data_dir = os.path.join(data_dir, "raw")
    summaries_dir = os.path.join(data_dir, "summaries")
    raw_data_file_list = os.listdir(raw_data_dir)
    summaries_file_list = os.listdir(summaries_dir)

    aa = AdAnalysis(summaries_file_list)


    # loop through summary files and build dicts
    for summary_file in summaries_file_list:
        data_dict = {}

        if aa.isBlocking(summary_file):
            blocking_summary_file = summary_file
            # map summary files with ad-blocker to the 4 files in that group (non-blocking summary, blocking summary, non-blocking raw, blocking raw)
            nonblocking_summary_file = aa.getAdFileMatch(blocking_summary_file, summaries_file_list)
            ad_compare_dict[blocking_summary_file] = {'blocking_summary': blocking_summary_file, 'nonblocking_summary': nonblocking_summary_file}
            blocking_raw_file = aa.getRawFromSummary(blocking_summary_file, raw_data_file_list)
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

            # meta data
            data_dict['meta_data'] = {}
            data_dict['meta_data']['try_num'] = 4
            data_dict['meta_data']['time_submitted'] = time.time()
            data_dict['meta_data']['sample_num'] = aa.getSampleNum(blocking_summary_file)
            data_dict['meta_data']['num_samples_in_set'] = num_samples_in_set
            data_dict['meta_data']['log_fname'] = log_fname
            data_dict['meta_data']['location'] = aa.getLocation(blocking_summary_file)
            data_dict['meta_data']['device'] = aa.getDevice(blocking_summary_file)
            data_dict['meta_data']['networkType'] = aa.getNetworkType(blocking_summary_file)
            data_dict['meta_data']['hostname'] = aa.getHostname(blocking_summary_file)
            data_dict['meta_data']['pageURL'] = bs_obj['pageURL']
            data_dict['meta_data']['page_categories_and_ranks'] = bs_obj['categories_and_ranks']
            data_dict['meta_data']['cutoffTime'] = bs_obj['cutoffTime']
            data_dict['meta_data']['debugPort'] = bs_obj['debugPort']
            data_dict['meta_data']['orig_directory_name'] = data_dir

            # blocking raw file
            brf_path = os.path.join(raw_data_dir, blocking_raw_file)
            brf = open(brf_path, 'r')
            event_list = [json.loads(line) for line in brf.readlines()]
            data_dict['blocking_raw'] = {}
            data_dict['blocking_raw']['event_list'] = event_list
            brf.close()

            # nonblocking raw file
            nrf_path = os.path.join(raw_data_dir, nonblocking_raw_file)
            nrf = open(nrf_path, 'r')
            event_list = [json.loads(line) for line in nrf.readlines()]
            data_dict['nonblocking_raw'] = {}
            data_dict['nonblocking_raw']['event_list'] = event_list
            nrf.close()

            resource = "page-loads"     # this is actually the dataset
            isAsync = False
            project = "/web-ads"
            response = report(resource, data_dict, async=isAsync, project=project)
            if response[0] == False:
                print("report failed.")
                print(response)
                print("Trying a second time")
                response = report(resource, data_dict, async=isAsync, project=project)
                if response[0] == False:
                	print("report failed again.")
                	print(response)
                	print(data_dict['blocking_summary']['rawDataFile'])
                	wrapUp(start_time, succeeded_list)
            else:
                succeeded_list.append(blocking_summary_file)

    wrapUp(start_time, succeeded_list)




