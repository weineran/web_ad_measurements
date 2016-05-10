import argparse
import os
import json
from AdAnalysis import AdAnalysis

def parse_args():
    parser = argparse.ArgumentParser(
            description='Make lists of the urls that have already been measured.  This way measurements can be restarted where we left off when they fail or crash.')
    parser.add_argument('data_dir', type=str,
                    help="The directory containing the data files to analyze.  Should contain subdirectories\n"+
                        "called 'raw', 'summaries', and 'log'.  Plots will be saved to a subdirectory called 'figs'")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    data_dir = args.data_dir

    # ad_compare_dict = {}
    # chron_compare_dict = {}
    # ad_chron_dict = {}

    # prep directories
    summaries_dir = os.path.join(data_dir, "summaries")
    list_out_dir = os.path.join(data_dir, "measured_lists")
    summaries_file_list = os.listdir(summaries_dir)
    if not os.path.isdir(list_out_dir):
        os.mkdir(list_out_dir)

    aa = AdAnalysis(summaries_file_list)

    phone_4g_measured_dict = {}
    phone_wifi_measured_dict = {}
    computer_wired_measured_dict= {}
    computer_wifi_measured_dict= {}
    macbookpro_wired_measured_dict= {}
    macbookpro_wifi_measured_dict= {}

    # loop through summary files and build dicts
    for summary_file in summaries_file_list:

        # make list of hostnames that have been measured
        this_hostname = aa.getHostname(summary_file)
        this_device = aa.getDevice(summary_file)
        this_network = aa.getNetworkType(summary_file)
        if this_device == "phone":
            if this_network == "4g":
                phone_4g_measured_dict[this_hostname] = True
            elif this_network == "wifi":
                phone_wifi_measured_dict[this_hostname] = True
            else:
                print("invalid network: "+str(this_network))
                raise
        elif this_device == "computer":
            if this_network == "wired":
                computer_wired_measured_dict[this_hostname] = True
            elif this_network == "wifi":
                computer_wifi_measured_dict[this_hostname] = True
            else:
                print("invalid network: "+str(this_network))
                raise
        elif this_device == "MacBookPro":
            if this_network == "wired":
                macbookpro_wired_measured_dict[this_hostname] = True
            elif this_network == "wifi":
                macbookpro_wifi_measured_dict[this_hostname] = True
            else:
                print("invalid network: "+str(this_network))
                raise
        else:
            print("invalid device: "+str(this_device))
            raise

    # dump list of measured hostnames to file
    phone_4g_list_path = os.path.join(list_out_dir, "phone_4g_measured.json")
    phone_wifi_list_path = os.path.join(list_out_dir, "phone_wifi_measured.json")
    computer_wired_list_path = os.path.join(list_out_dir, "computer_wired_measured.json")
    computer_wifi_list_path = os.path.join(list_out_dir, "computer_wifi_measured.json")
    macbookpro_wired_list_path = os.path.join(list_out_dir, "macbookpro_wired_measured.json")
    macbookpro_wifi_list_path = os.path.join(list_out_dir, "macbookpro_wifi_measured.json")

    with open(phone_4g_list_path, 'w') as f:
        json.dump(phone_4g_measured_dict, f)
    with open(phone_wifi_list_path, 'w') as f:
        json.dump(phone_wifi_measured_dict, f)
    with open(computer_wired_list_path, 'w') as f:
        json.dump(computer_wired_measured_dict, f)
    with open(computer_wifi_list_path, 'w') as f:
        json.dump(computer_wifi_measured_dict, f)
    with open(macbookpro_wired_list_path, 'w') as f:
        json.dump(macbookpro_wired_measured_dict, f)
    with open(macbookpro_wifi_list_path, 'w') as f:
        json.dump(macbookpro_wifi_measured_dict, f)











