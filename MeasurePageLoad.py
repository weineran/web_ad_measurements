import json
from urlparse import urlparse
import os
import time
from subprocess import call, Popen

def connectToDevice():
    '''
    Asks the user which device to drive.  Makes a command line call to connect to that device.
    '''
    print("")
    choice_num = input("\nDo you want to drive Chrome on your phone or on your computer?\n"+
                        "Chrome on phone    - enter '1'\n"+
                        "Chrome on computer - enter '2'\n")
    if choice_num == 1:
        device = "phone"
        print("Calling 'adb forward tcp:9222 localabstract:chrome_devtools_remote'")
        call("adb forward tcp:9222 localabstract:chrome_devtools_remote")
    elif choice_num == 2:
        device = "computer"
        #path_to_chrome = _getChromePath()
        #command = '"' + path_to_chrome + '" --remote-debugging-port=9222'
        #print('Calling '+command)
        #p_chrome = Popen(command)
    else:
        print("ERR: Invalid choice.")
        raise

    return device

def _getChromePath():
    '''
    Asks the user to provide the path to the Chrome Canary executable.
    Returns a string representing the full path.
    '''
    path_to_chrome = raw_input("Enter the path to your Chrome Canary executable.\n"+
                            "(If you wish to use 'C:\Users\[username]\AppData\Local\Google\Chrome SxS\Application\chrome.exe', enter '0')\n")
    if path_to_chrome == '0':
        username = raw_input("Enter your username\n")
        path_to_chrome = os.path.join("C:\Users", username, "AppData\Local\Google\Chrome SxS\Application\chrome.exe")
    return path_to_chrome

class MeasurePageLoad:
    """
    MeasurePageLoad is a class for running page load measurements over websockets
    using Google Chrome's Remote Debugging feature.
    """
    
    # constructor
    def __init__(self, ws, page_url = None, cutoff_time = None):
        self.ws = ws                 # websocket.WebSocket object
        self.page_url = page_url
        self.cutoff_time = cutoff_time
        self.first_timestamp = None
        self.last_timestamp = None
        self.msg_list = []             # list of debug messages received from ws
        

    def _getFirstTimestamp(self):
        """
        Finds the first message with a valid timestamp.  Saves this value to 
        the object's first_timestamp attribute and returns the value.
        """
        while True:
            first_resp = self.ws.recv()
            self.msg_list.append(first_resp)

            try:
                first_timestamp = json.loads(first_resp)["params"]["timestamp"]
            except KeyError as e:
                print("KeyError: "+str(first_resp))
            else:
                # if successfully got first_timestamp, break out of loop
                break

        print("first_timestamp: " + str(first_timestamp))
        self.first_timestamp = first_timestamp
        return first_timestamp

    def _getDataUntilCutoff(self):
        """
        Appends data to the object's msg_list until it finds a message whose
        timestamp is past the cutoff_time.  Saves this last timestamp in the
        object's last_timestamp attribute.
        """
        while True:
            this_resp = self.ws.recv()
            self.msg_list.append(this_resp)
            try:
                this_timestamp = json.loads(this_resp)["params"]["timestamp"]
            except KeyError as e:
                #print("KeyError. "+str(this_resp))
                pass # just check the next timestamp
            else:
                # if we have a value for this_timestamp, and it has been long enough
                # since the first timestamp, then break out of loop
                if (this_timestamp - self.first_timestamp) > self.cutoff_time:
                    print("last_timestamp: " + str(this_timestamp))
                    self.last_timestamp = this_timestamp
                    break

    def _getHARresp(self):
        while True:
            this_resp = self.ws.recv()
            self.msg_list.append(this_resp)
            this_timestamp = time.time()

            if (this_timestamp - self.first_timestamp) > self.cutoff_time:
                print("last_timestamp: " + str(this_timestamp))
                self.last_timestamp = this_timestamp
                break


    def LoadPage_SaveData(self, output_dir, i):
        """
        Tells the connected browser to load the desired page.  Loads the page for
        the amount of time specified by the object's cutoff_time attribute.  Saves
        data on the page load to the object's msg_list.  When cutoff_time is reached,
        all the data in msg_list is written to a file in the specified output_dir.
        """
        # Tell browser to load the desired page
        self.ws.send(json.dumps({'id': i, 'method': 'Page.navigate', 'params': {'url': self.page_url}}))

        # get data and put in msg_list
        first_timestamp = self._getFirstTimestamp()
        self._getDataUntilCutoff()

        # save data to file
        hostname = urlparse(self.page_url).netloc + ".txt"
        output_file = os.path.join(output_dir, hostname)
        with open(output_file, "w") as f:
            json.dump(self.msg_list, f)

    def getHar(self, output_dir, i):
        '''
        Tells the connected browser to load the desired page.  Loads the page for
        the amount of time specified by the object's cutoff_time attribute.  Saves the HAR
        file using the chrome.devtools.network.getHAR() method.
        '''
        self.ws.send(json.dumps({'id': i, 'method': 'Page.navigate', 'params': {'url': self.page_url}}))
        self.first_timestamp = time.time()
        self.ws.send(json.dumps({'id': i, 'method': 'chrome.devtools.network.getHAR', 'params': {}}))
        self._getHARresp()

        # save data to file
        hostname = urlparse(self.page_url).netloc + "-HAR.txt"
        output_file = os.path.join(output_dir, hostname)
        with open(output_file, "w") as f:
            json.dump(self.msg_list, f)