import os
import argparse
import json

def parse_args():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Given files in the form:\n'
                        '[{"rank":1,"title":"Espn.go.com","hostname":"Espn.go.com"},...]\n\n'
                        'Aggregates them into a dict of the form:\n'
                        '{"Craigslist.org": {\n'
                        '                    "category_ranks": {"US": 14, "Global": 72},\n'
                        '                    "title": "Craigslist.org"\n'
                        '                   }}')
    parser.add_argument('input_directory', type=str,
                    help="The path of the directory containing the input files.")
    parser.add_argument('output_directory', type=str,
                    help="The path of the directory to write the output file.")
    parser.add_argument('output_fname', type=str,
                    help="The file name to use for the output file.")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    input_directory = args.input_directory
    output_directory = args.output_directory
    output_fname = args.output_fname

    file_list = os.listdir(input_directory)
    output_dict = {}

    for file in file_list:
        full_path = os.path.join(input_directory, file)
        f = open(full_path, 'r')
        site_list = json.load(f)
        for this_site in site_list:
            hostname = this_site['hostname']
            if hostname not in output_dict:
                output_dict[hostname] = {
                                        "category_ranks": {this_site['category']: this_site['rank']},
                                        "title": this_site['title']
                                        }
            else:
                this_category = this_site['category']
                if this_category not in output_dict[hostname]["category_ranks"]:
                    # Simple case
                    output_dict[hostname]["category_ranks"][this_category] = this_site['rank']
                else:
                    # Collision
                    # google.com and google.com/analytics have same hostname, and both
                    # appear in the top 100 Computer sites.
                    # Use higher rank and corresponding title
                    stored_rank = output_dict[hostname]["category_ranks"][this_category]
                    stored_title = output_dict[hostname]['title']
                    this_rank = this_site['rank']
                    this_title = this_site['title']
                    print("Collision: "+this_category+" "+str(stored_rank)+" "+stored_title+".  "+str(this_rank)+" "+this_title+".")
                    if this_rank < stored_rank:
                        print("Storing "+str(this_rank)+" "+this_title)
                        output_dict[hostname]["category_ranks"][this_category] = this_rank
                        output_dict[hostname]['title'] = this_title

    # create json file
    output_file = open(os.path.join(output_directory, output_fname+".json"), 'w')
    json.dump(output_dict, output_file)
    print("num hostnames: "+str(len(output_dict)))

    # create txt file (line-separated)
    output_file2 = open(os.path.join(output_directory, output_fname+"_list.txt"), "w")
    for this_hostname in output_dict:
        output_file2.write(this_hostname + ": "+json.dumps(output_dict[this_hostname])+"\n")