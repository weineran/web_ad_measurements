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
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    file_to_parse = args.file_to_parse

    list_of_pages = []

    # Read from file into list of dicts
    f = open(file_to_parse, 'r')
    i = 0
    for line in f:
    	this_dict = {}
    	line_num = i % 3
    	if line_num == 0:
    		this_dict['rank'] = int(line)
    	elif line_num == 1:
    		this_dict['title'] = line
    		this_dict['hostname'] = urlparse(line).netloc
    	elif line_num == 2:
    		pass
    		list_of_pages.append(this_dict)
    	else:
    		raise Exception('Modulo error.')
    	i += 1

    f = open(file_to_parse[:-4] + '_parsed.json', 'w')
    json.dump(list_of_pages, f)
