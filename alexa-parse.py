import argparse
from urlparse import urlparse
import json

def parse_args():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Given a text file (copied from alexa.com) in this format:\n'
                        '    1\n    Espn.go.com\n    Sports news network.\n    2\n    Sports.yahoo.com\n'
                        '    Listen to live and on-demand sports content\n    ...\n'
                        'Parse the file and output a json file containing a list of dictionaries in this format:\n'
                        '[{"rank":1,"title":"Espn.go.com","hostname":"Espn.go.com"},...]')
    parser.add_argument('file_to_parse', type=str,
                    help="The full path of the file to be parsed.")
    parser.add_argument('category', type=str,
                    help="The Alexa category.")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    file_to_parse = args.file_to_parse
    category = args.category

    list_of_pages = []

    # Read from file into list of dicts
    f = open(file_to_parse, 'r')
    i = 0
    this_dict = {}
    for line in f:
        line_num = i % 3
        if line_num == 0:
            # store rank and category
            this_dict['rank'] = int(line)
            this_dict['category'] = category
        elif line_num == 1:
            # store title and hostname
            this_dict['title'] = line[:-1]
            if this_dict['title'][0:4].lower() == "http":
                hostname = urlparse(this_dict['title']).netloc.lower()
            else:
                hostname = urlparse("http://"+this_dict['title']).netloc.lower()

            if hostname[0:4].lower() == "www.":
                hostname = hostname[4:]

            this_dict['hostname'] = hostname

        elif line_num == 2:
            # add to list and reset
            list_of_pages.append(this_dict)
            this_dict = {}
        else:
            raise Exception('Modulo error.')
        i += 1

    f = open(file_to_parse[:-4] + '_parsed.json', 'w')
    json.dump(list_of_pages, f)
    if len(list_of_pages) != 100:
        print(category+": only "+str(len(list_of_pages))+" pages")
