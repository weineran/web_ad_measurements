import requests
import time
import json
import argparse
from MeasurePageLoad2 import MeasurePageLoad, connectToDevice, getNetworkType, shouldContinue, fixURL, getLocation, attemptConnection, getUserOS

def parse_args():
    parser = argparse.ArgumentParser(
            description='load some pages and collect some data')
    parser.add_argument('cutoff_time', type=int,
                    help="The number of seconds to allow a page to load "
                        "(while collecting data) before loading the next page.")
    parser.add_argument('num_samples', type=int,
                    help="The number of times to load each page with and without ads.")
    parser.add_argument('url_list_file', type=str,
                    help="A file containing a list or dict of urls to load.  Each page "
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
    print("\nThis will require at least "+str(min_time)+" minutes to complete.")
    if not shouldContinue():
        print("Canceled.")
        exit()
    
    # connect to device
    device, op_sys = connectToDevice(debug_port)

    # get location
    location = getLocation()

    # get network connection type
    network_type = getNetworkType(device)
    
    # Connect to phone and gather json info
    remote_debug_url = "http://localhost:"+str(debug_port)+"/json"
    while True:
        print("Opening websocket remote debugging connection to "+remote_debug_url)
        r = attemptConnection(remote_debug_url)
        if r == "try_again":
            pass
        elif r == "give_up":
            print("Script aborted.")
            exit()
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

    start_time = time.time()

    print("You are driving this tab remotely:")
    print(resp_json[tab_number])

    target_tab = resp_json[tab_number]   # Possibly need to run adb command to open chrome in the first place?

    #websocket.enableTrace(True) # Not exactly sure what this does

    # connect to first tab via the WS debug URL
    url_ws = str(target_tab['webSocketDebuggerUrl'])
    
    mpl = MeasurePageLoad(url_ws, cutoff_time=cutoff_time, device=device, debug_port=debug_port, 
                        network_type=network_type, location=location, output_dir=output_dir, op_sys=op_sys,
                        start_time=start_time, min_time=min_time)

    mpl.setupOutputDirs()

    # Do this once before we start
    # Every other time it happens at end of runMeasurements
    mpl.setupWebsocket()
    mpl.clearAllCaches()
    mpl.enableAdBlock()     # first run is with ad-blocker (without ads)
    mpl.closeWebsocket()

    for this_url in url_list:
        try:
            mpl.categories_and_ranks = url_list[this_url]['category_ranks']
        except TypeError:
            pass

        this_url = fixURL(this_url)
        
        for sample_num in range(1, num_samples+1):
            # run with ad-blocker ON
            useAdBlocker = True
            msg = "\nLoading "+this_url+" without ads.  sample_num: "+str(sample_num)
            print(msg)
            mpl.runMeasurements(useAdBlocker, this_url, sample_num)

            # run with ad-blocker OFF
            useAdBlocker = False
            msg = "\nLoading "+this_url+" with ads.  sample_num: "+str(sample_num)
            print(msg)
            mpl.runMeasurements(useAdBlocker, this_url, sample_num)
        # end looping through sample_nums
    # end looping through all urls


    mpl.writeLog()

    print("TODO: add outgoing and incoming data")

