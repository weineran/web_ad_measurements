import requests
import websocket
import thread
import time
import json
import argparse
import os
from subprocess import call
from urlparse import urlparse

# We have to use several global variables because the websocket callback functions,
# such as on_message, do not allow additional parameters to be passed in
global OUTPUT_DIR
global OUTPUT_FILE
global F_PTR
global CUTOFF_TIME
global URL_LIST
global MSG_LIST

def parse_args():
    parser = argparse.ArgumentParser(
            description='load some pages... '
                        ' ...and collect some data')
    parser.add_argument('cutoff_time', type=int,
                    help="The number of seconds to allow a page to load "
                        "(while collecting data) before loading the next page.")
    parser.add_argument('url_list_file', type=str,
                    help="A file containing an ordered list of urls to load.  Each page "
                        "is loaded for the amount of time specified by the cutoff_time argument.")
    parser.add_argument('output_dir', type=str,
                    help="A directory where the output data files will be written.")
    return parser.parse_args()

def LoadPage_SaveData(ws, this_url, OUTPUT_DIR, i):
    msg_list = []
    ws.send(json.dumps({'id': i, 'method': 'Page.navigate', 'params': {'url': this_url}}))
    first_resp = ws.recv()
    msg_list.append(first_resp)
    try:
        first_timestamp = json.loads(first_resp)["params"]["timestamp"]
    except KeyError as e:
            print("KeyError. "+str(first_resp))
    print("first_timestamp: " + str(first_timestamp))

    while True:
        this_resp = ws.recv()
        msg_list.append(this_resp)
        try:
            this_timestamp = json.loads(this_resp)["params"]["timestamp"]
        except KeyError as e:
            #print("KeyError. "+str(this_resp))
            pass # just check the next timestamp
        if (this_timestamp - first_timestamp) > CUTOFF_TIME:
            break

    hostname = urlparse(this_url).netloc + ".txt"
    output_file = os.path.join(OUTPUT_DIR, hostname)
    with open(output_file, "w") as f:
        json.dump(msg_list, f)


if __name__ == "__main__":
    print("")
    print("Calling 'adb forward tcp:9222 localabstract:chrome_devtools_remote'")
    call("adb forward tcp:9222 localabstract:chrome_devtools_remote")
    # Get arguments
    args = parse_args()
    cutoff_time = args.cutoff_time
    url_list_file = args.url_list_file
    OUTPUT_DIR = args.output_dir

    # get list of URLs from file
    with open(url_list_file, 'r') as f:
            URL_LIST = json.load(f)
    #URL_LIST = ["http://www.cnn.com/", "http://espn.go.com/", "http://www.nytimes.com/"]

    CUTOFF_TIME = cutoff_time

    
    # Connect to phone and gather json info
    r = requests.get("http://localhost:9222/json")
    resp_json = r.json()
    if len(resp_json) > 1:
        print("There are "+str(len(resp_json)) + " available tabs:")
        i = 0
        for this_tab in resp_json:
            print(str(i)+": "+this_tab["title"])
            i += 1
        tab_number = input("Which tab would you like to drive remotely? (0-"+str(len(resp_json)-1)+")")
    else:
        tab_number = 0

    print("You are driving this tab remotely:")
    print(resp_json[tab_number])

    target_tab = resp_json[tab_number]   # Possibly need to run adb command to open chrome in the first place?

    #websocket.enableTrace(True) # Not exactly sure what this does

    # connect to first tab via the WS debug URL
    url_ws = str(target_tab['webSocketDebuggerUrl'])
    ws = websocket.create_connection(url_ws)

    ws.send(json.dumps({'id': 1, 'method': 'Network.enable'}))
    print(ws.recv())
    ws.send(json.dumps({'id': 2, 'method': 'Page.enable'}))
    print(ws.recv())

    i = 3
    for this_url in URL_LIST:
        print("Preparing to load "+this_url)
        LoadPage_SaveData(ws, this_url, OUTPUT_DIR, i)
        i += 1




# payload = {'id': 1, 'method': 'Network.enable'}
# json_payload = json.dumps(payload)
# ws.send(json_payload)

# payload = {'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://www.facebook.com'}}
# json_payload = json.dumps(payload)
# ws.send(json_payload)