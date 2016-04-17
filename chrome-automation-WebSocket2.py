import requests
import websocket
import time
import json
import argparse
from MeasurePageLoad import MeasurePageLoad, connectToDevice, getNetworkType, shouldContinue, fixURL, getLocation

def parse_args():
    parser = argparse.ArgumentParser(
            description='load some pages and collect some data')
    parser.add_argument('cutoff_time', type=int,
                    help="The number of seconds to allow a page to load "
                        "(while collecting data) before loading the next page.")
    parser.add_argument('num_samples', type=int,
                    help="The number of times to load each page with and without ads.")
    parser.add_argument('url_list_file', type=str,
                    help="A file containing an ordered list of urls to load.  Each page "
                        "is loaded for the amount of time specified by the cutoff_time argument.")
    parser.add_argument('output_dir', type=str,
                    help="A directory where the output data files will be written.")
    parser.add_argument('debug_port', type=int,
                    help="The port to use as the 'remote-debugging-port'")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    args = parse_args()
    cutoff_time = args.cutoff_time
    url_list_file = args.url_list_file
    output_dir = args.output_dir
    debug_port = args.debug_port
    num_samples = args.num_samples

    # get list of URLs from file
    with open(url_list_file, 'r') as f:
            url_list = json.load(f)

    num_urls = len(url_list)
    min_time = num_urls * 2 * num_samples * cutoff_time/60.0
    print("This will require at least "+str(min_time)+" minutes to complete.")
    if not shouldContinue():
        print("Canceled.")
        exit()

    # get location
    location = getLocation()

    # connect to device
    device = connectToDevice(debug_port)

    # get network connection type
    network_type = getNetworkType(device)
    
    # Connect to phone and gather json info
    while True:
        try:
            r = requests.get("http://localhost:"+str(debug_port)+"/json")
        except ConnectionError:
            pass
        else:
            break

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
    mpl = MeasurePageLoad(ws, cutoff_time=cutoff_time, device=device, debug_port=debug_port, 
                        network_type=network_type, location=location)
    #mpl.sendMethod("Console.enable", None, True)
    #mpl.sendMethod("Debugger.enable", None, False)
    mpl.sendMethod("Network.enable", None, True)
    mpl.sendMethod("Page.enable", None, True)
    #mpl.sendMethod("Runtime.enable", None, True)
    mpl.sendMethod("Timeline.start", None, True)

    for this_url in url_list:
        this_url = fixURL(this_url)
        
        sample_num = 1
        while sample_num <= num_samples:
            # run with ad-blocker ON
            mpl.enableAdBlock()
            mpl.clearAllCaches()
            print("\nLoading "+this_url+" without ads.")
            mpl.LoadPage_SaveData(output_dir, this_url, sample_num)

            # run with ad-blocker OFF
            mpl.disableAdBlock()
            mpl.clearAllCaches()
            print("\nLoading "+this_url+" with ads.")
            mpl.LoadPage_SaveData(output_dir, this_url, sample_num)
            sample_num += 1

    mpl.writeLog(output_dir)

