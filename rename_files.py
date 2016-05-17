import argparse
import os
import json
from AdAnalysis import AdAnalysis

def parse_args():
    parser = argparse.ArgumentParser(
            description='Make lists of the urls that have already been measured.  This way measurements can be restarted where we left off when they fail or crash.')
    parser.add_argument('data_dir', type=str,
                    help="The directory containing the data files to rename")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    data_dir = args.data_dir

    # change raw file names
    raw_dict = os.path.join(data_dir, "raw")
    raw_files = os.listdir(raw_dict)
    for filename in raw_files:
    	full_path = os.path.join(raw_dict, filename)
    	if "home-computer-wifi" in filename:
    		new_name = filename.replace("home-computer-wifi", "home-MacBookPro-wifi")
    		new_path = os.path.join(raw_dict, new_name)
    		os.rename(full_path, new_path)