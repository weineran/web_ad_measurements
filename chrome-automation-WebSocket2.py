import requests
import websocket
import time
import json
import argparse
from MeasurePageLoad import MeasurePageLoad, connectToDevice

def parse_args():
    parser = argparse.ArgumentParser(
            description='load some pages and collect some data')
    parser.add_argument('cutoff_time', type=int,
                    help="The number of seconds to allow a page to load "
                        "(while collecting data) before loading the next page.")
    parser.add_argument('url_list_file', type=str,
                    help="A file containing an ordered list of urls to load.  Each page "
                        "is loaded for the amount of time specified by the cutoff_time argument.")
    parser.add_argument('output_dir', type=str,
                    help="A directory where the output data files will be written.")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    cutoff_time = args.cutoff_time
    url_list_file = args.url_list_file
    output_dir = args.output_dir

    # connect to device
    debug_port = 9222
    device = connectToDevice(debug_port)

    # get list of URLs from file
    with open(url_list_file, 'r') as f:
            URL_LIST = json.load(f)
    
    # Connect to phone and gather json info
    r = requests.get("http://localhost:"+str(debug_port)+"/json")
    resp_json = r.json()

    # Choose a browser tab to drive remotely
    if len(resp_json) > 1:
        print("\nThere are "+str(len(resp_json)) + " available tabs:")
        i = 0
        for this_tab in resp_json:
            try:
                page_title = str(this_tab["title"])
            except:
                page_title = "ERR: unable to read page title"
            print(str(i)+": "+page_title)
            i += 1
        tab_number = input("\nWhich tab would you like to drive remotely (0-"+str(len(resp_json)-1)+")?\n"+
                            "(Choose the tab that is active on your phone)")
    else:
        tab_number = 0

    print("You are driving this tab remotely:")
    print(resp_json[tab_number])

    target_tab = resp_json[tab_number]   # Possibly need to run adb command to open chrome in the first place?

    #websocket.enableTrace(True) # Not exactly sure what this does

    # connect to first tab via the WS debug URL
    url_ws = str(target_tab['webSocketDebuggerUrl'])
    ws = websocket.create_connection(url_ws)
    mpl = MeasurePageLoad(ws, cutoff_time=cutoff_time, device=device, debug_port=debug_port)
    mpl.sendMethod("Console.enable", None, True)
    mpl.sendMethod("Debugger.enable", None, False)
    mpl.sendMethod("Network.enable", None, True)
    mpl.sendMethod("Page.enable", None, True)
    mpl.sendMethod("Runtime.enable", None, True)
    mpl.sendMethod("Timeline.start", None, True)

    for this_url in URL_LIST:
        # run with ad-blocker ON
        mpl.enableAdBlock()
        mpl.clearAllCaches()
        print("Loading "+this_url+" without ads.")
        mpl.LoadPage_SaveData(output_dir, this_url)

        # run with ad-blocker OFF
        mpl.disableAdBlock()
        mpl.clearAllCaches()
        print("Loading "+this_url+" with ads.")
        mpl.LoadPage_SaveData(output_dir, this_url)

