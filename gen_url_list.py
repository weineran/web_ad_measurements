import os
import argparse
import json
from MY_CSV import my_csv

def parse_args():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Given:\n'
                        '1) a master list as output by build_full_site_list.py and\n'
                        '2) a file specifying the filter conditions\n'
                        'Generates a filtered list of URLs')
    parser.add_argument('master_list_file', type=str,
                    help="The .json file containing all eligible hostnames.")
    parser.add_argument('conditions_file', type=str,
                    help="File providing categories and cutoff ranks for each.")
    parser.add_argument('output_fname', type=str,
                    help="The file name to use for the output list.")
    parser.add_argument('--exclude_list', type=str,
                    help="A .json file containing hostnames to exclude.  This is useful if, for example, "+
                    "you already have data for the top 10 and want to collect data for ranks 10-20.")
    return parser.parse_args()

def shouldInclude(hostname, hostname_dict, conditions_dict, exclude_dict={}):
    if hostname in exclude_dict:
        return False
        
    for category in hostname_dict['category_ranks']:
        cutoff = max(int((conditions_dict[category]['rank_cutoff'])), int(conditions_dict['all']['rank_cutoff']))
        if hostname_dict['category_ranks'][category] <= cutoff:
            return True
    return False

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    master_list_file = args.master_list_file
    conditions_file = args.conditions_file
    output_fname = args.output_fname
    exclude_list = args.exclude_list

    # get json master list
    f = open(master_list_file, 'r')
    master_dict = json.load(f)
    f.close()

    # get json exclude_list
    if exclude_list == None:
        exclude_dict = {}
    else:
        f = open(exclude_list, 'r')
        exclude_dict = json.load(f)
        f.close()


    # get conditions as dict
    a_csv = my_csv(conditions_file)
    conditions_dict = a_csv.dict
    print(conditions_dict)

    # loop through master list
    output_dict = {}
    for hostname in master_dict:
        if shouldInclude(hostname, master_dict[hostname], conditions_dict, exclude_dict=exclude_dict):
            output_dict[hostname] = master_dict[hostname]

    # dump output_dict to file
    print("Filtered list has "+str(len(output_dict))+" hostnames")
    f = open(output_fname, 'w')
    json.dump(output_dict, f)
    f.close()
    print(output_dict)

    output_csv_obj = my_csv(output_dict)
    output_csv_obj.writeToCSV(output_fname+".csv")
