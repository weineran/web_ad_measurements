import json
from urlparse import urlparse
import os
import time
from subprocess import call, Popen
import requests
from PIL import Image
import multiprocessing
#from timeout import timeout


def shouldContinue():
    resp = raw_input("Would you like to continue? (y or n)\n>")
    if resp == 'y':
        return True
    elif resp == 'n':
        return False
    else:
        print("Invalid response.  Please try again.")
        return shouldContinue()

def getLocation():
    return raw_input("What is your location?\n(e.g. 'home'. Needed for filename convention)\n>")

def connectToDevice(debug_port):
    '''
    Asks the user which device to drive.  Makes a command line call to connect to that device.
    '''
    print("")
    choice_num = input("\nDo you want to drive Chrome on your phone or on your computer?\n"+
                        "Chrome on phone    - enter '1'\n"+
                        "Chrome on computer - enter '2'\n>")
    if choice_num == 1:
        device = "phone"
        command = "adb forward tcp:"+str(debug_port)+" localabstract:chrome_devtools_remote"
        ret_code = printAndCall(command)
        if ret_code == 1:
            print("Error.  Please ensure that phone is connected and try again.")
            return connectToDevice(debug_port)
    elif choice_num == 2:
        device = "computer"
        if shouldOpenChromeCanary():
            openChromeCanary(debug_port)
    else:
        print("ERR: Invalid choice.")
        raise

    return device

def fixURL(url):
    if not urlHasScheme(url):
        return "http://"+url
    else:
        return url

def urlHasScheme(url):
    if url[0:4] == "http":
        return True
    else:
        return False

def getNetworkType(device):
    if device == "phone":
        valid_resp_list = ["wifi", "4g"]
    elif device == "computer":
        valid_resp_list = ["wifi", "wired"]
    else:
        print("ERR. Invalid device: "+str(device))
        raise

    ask_str = "What type of network are you connected to?\nValid responses are: "
    for resp in valid_resp_list:
        ask_str += (resp+", ")
    network_type = raw_input(ask_str+"\n>")
    network_type = network_type.lower()
    if network_type in valid_resp_list:
        return network_type
    else:
        print("Invalid response.  Please try again.")
        return getNetworkType(device)

def openChromeCanary(debug_port):
    path_to_chrome = _getChromePath()
    command = '"' + path_to_chrome + '" --remote-debugging-port='+str(debug_port)
    print('Popening '+command)
    p_chrome = Popen(command)

def shouldOpenChromeCanary():
    resp = raw_input("Is Chrome Canary already open with --remote-debugging-port flag?\n"+
                    "(Enter y or n)\n>")
    if resp == 'y':
        return False
    elif resp == 'n':
        return True
    else:
        print("Invalid response.  Please enter y or n")
        return shouldOpenChromeCanary()

def _getChromePath():
    '''
    Asks the user to provide the path to the Chrome Canary executable.
    Returns a string representing the full path.
    '''
    path_to_chrome = raw_input("Enter the path to your Chrome Canary executable.\n"+
                            "(If you wish to use 'C:\Users\[username]\AppData\Local\Google\Chrome SxS\Application\chrome.exe', enter '0')\n>")
    if path_to_chrome == '0':
        username = raw_input("Enter your username\n>")
        path_to_chrome = os.path.join("C:\Users", username, "AppData\Local\Google\Chrome SxS\Application\chrome.exe")
    elif path_to_chrome == 'a':
        # easter egg for me
        username = "Andrew"
        path_to_chrome = os.path.join("C:\Users", username, "AppData\Local\Google\Chrome SxS\Application\chrome.exe")
    return path_to_chrome

def printAndCall(command):
    print("Calling '"+command+"'")
    return call(command)

class MeasurePageLoad:
    """
    MeasurePageLoad is a class for running page load measurements over websockets
    using Google Chrome's Remote Debugging feature.
    """
    
    # constructor
    def __init__(self, ws, page_url = None, cutoff_time = None, device = "computer", debug_port=9222, 
                 phone_adBlockPackage="com.savageorgiev.blockthis", network_type=None, location=None):
        self.ws = ws                 # websocket.WebSocket object
        self.page_url = page_url
        self.cutoff_time = cutoff_time
        self.first_timestamp = None
        self.last_timestamp = None
        self.msg_list = []             # list of debug messages received from ws
        self.device = device           # "phone" or "computer"
        self.debug_port = debug_port
        self.id = 1
        self.network_type = network_type
        self.phone_adBlockPackage = phone_adBlockPackage
        #self.p = None
        self.frames = {}
        self.firstFrame = False
        self.logMsgs = []
        self.location = location
        self.fname = None
        self._isBlockingAds = self.isAdBlockEnabled()

    def writeLog(self, output_dir):
        log_fname = str(time.time())+".log"
        log_path = os.path.join(output_dir,log_fname)
        f = open(log_path, 'w')
        for msg in self.logMsgs:
            f.write(msg+"\n")
        f.close()

    def sendMethod(self, method_name, params, shouldPrintResp):
        if params == None:
            payload = json.dumps({'id': self.id, 'method': method_name})
        else:
            payload = json.dumps({'id': self.id, 'method': method_name, 'params': params})

        print("sending: "+payload)
        self.ws.send(payload)

        resp = self.ws.recv()
        self.id += 1

        if shouldPrintResp:
            print("received: "+resp)

    def isAdBlockEnabled(self):
        if self.device == "computer":
            return self.isAdBlockEnabledComputer()
        elif self.device == "phone":
            print("Attempting to kill ad block on phone in case it's already running")
            self._disableAdBlockPhone()
            return False
            #return self.isAdBlockEnabledPhone()
        else:
            print("ERR. Unknown device '"+str(self.device)+"'.")
            raise

    def isAdBlockEnabledComputer(self):
        r = requests.get("http://localhost:"+str(self.debug_port)+"/json")
        resp_json = r.json()
        for this_tab in resp_json:
            if this_tab['title'] == "Adblock Plus":
                return True

        # if Adblock Plus not found in json obj, then not enabled
        return False

    # def isAdBlockEnabledPhone(self):
    #     self._disableAdBlockPhone()
    #     return False

    def clearAllCaches(self):
        self.clearBrowserObjCache()
        self.clearDeviceDNSCache()
        self.clearBrowserDNSCache()

    # def adBlockerSwitch(self, on_or_off):
    #     if on_or_off == "on":
    #         if self.isAdBlockEnabled() == True:
    #             print("Ad-blocker is already enabled")
    #             return      # if it's already on, do nothing
    #         else:
    #             print("Enabling ad-blocker")
    #             self.enableAdBlock()
    #     elif on_or_off == "off":
    #         if self.isAdBlockEnabled() == False:
    #             print("Ad-blocker is already disabled")
    #             return      # if it's already off, do nothing
    #         else:
    #             print("Disabling ad-blocker")
    #             self.disableAdBlock()
    #     else:
    #         print("ERR. Invalid param '"+str(on_or_off)+"' to adBlockerSwitch() function")
    #         raise

    def enableAdBlock(self):
        if self.device == "computer":
            if self.isAdBlockEnabled() == False:
                print("Enabling ad-blocker")
                self._enableAdBlockComputer()
                print("Ad-blocker is now enabled")
            else:
                print("Ad-blocker is already enabled")
                return
        elif self.device == "phone":
            print("Enabling ad-blocker")
            self._enableAdBlockPhone()
            print("Ad-blocker is now enabled")
        else:
            print("ERR. Unknown device '"+self.device+"'")
            raise

        self._isBlockingAds = True

    def disableAdBlock(self):
        if self.device == "computer":
            self._disableAdBlockComputer()
        elif self.device == "phone":
            self._disableAdBlockPhone()
        else:
            print("ERR. Unknown device '"+self.device+"'")
            raise

        self._isBlockingAds = False

    def _disableAdBlockComputer(self):
        dst_url = "chrome://extensions/"
        self.loadURLandWait(dst_url)

        # tab 5 times
        tab_key = "U+0009"
        self.pressKeyKtimes(tab_key, 5)

        # then space bar
        space_bar = "U+0020"
        self.pressAndReleaseKey(space_bar)

    def _disableAdBlockPhone(self):
        command = "adb shell am force-stop "+self.phone_adBlockPackage
        printAndCall(command)

    def _enableAdBlockComputer(self):
        dst_url = "chrome://extensions/"
        self.loadURLandWait(dst_url)

        # tab 3 times
        tab_key = "U+0009"
        self.pressKeyKtimes(tab_key, 3)

        # then space bar
        space_bar = "U+0020"
        self.pressAndReleaseKey(space_bar)

    def _enableAdBlockPhone(self):
        # first try to force-stop in case it's already running
        print("Killing any already running ad-blocker")
        self._disableAdBlockPhone()

        # then start the ad-blocker
        command = "adb shell am start "+self.phone_adBlockPackage
        printAndCall(command)
        
        # then tap start button
        tap_xcoord = 525
        tap_ycoord = 925
        self.waitForBlockThisStartBtn(tap_xcoord, tap_ycoord)
        command = "adb shell input tap "+str(tap_xcoord)+" "+str(tap_ycoord)
        printAndCall(command)

    def waitForBlockThisStartBtn(self, xcoord, ycoord):
        target_R = 119
        target_G = 179
        target_B = 212
        while True:
            if self.checkPixelColor(xcoord, ycoord, target_R, target_G, target_B):
                return

    def checkPixelColor(self, xcoord, ycoord, target_R, target_G, target_B):
        # save screencap
        command = "adb shell screencap /sdcard/screen.png"
        printAndCall(command)

        # pull screencap to computer
        command = "adb pull /sdcard/screen.png"
        printAndCall(command)

        im = Image.open("screen.png")
        pixels = im.load()
        target_pixel = pixels[xcoord, ycoord]
        if target_pixel[0] == target_R:
            if target_pixel[1] == target_G:
                if target_pixel[2] == target_B:
                    os.remove("screen.png")
                    return True

        os.remove("screen.png")
        return False

    def pressAndReleaseKey(self, keyIdentifier):
        params = {'type': 'keyDown', 'keyIdentifier': keyIdentifier}
        self.sendMethod("Input.dispatchKeyEvent", params, True)
        params = {'type': 'keyUp', 'keyIdentifier': keyIdentifier}
        self.sendMethod("Input.dispatchKeyEvent", params, True)


    def waitForPageLoad(self):
        while True:
            resp = json.loads(self.ws.recv())
            try:
                method_name = str(resp["method"])
            except:
                pass
            else:
                #print("method: "+method_name)
                if method_name == "Page.loadEventFired":
                    time.sleep(0.5)
                    return

    def loadURLandWait(self, dst_url):
        self.navToURL(dst_url)
        self.waitForPageLoad()

    def clearBrowserObjCache(self):
        self.sendMethod("Network.setCacheDisabled", None, True)
        self.sendMethod("Network.clearBrowserCache", None, True)
        return

    def clearBrowserDNSCache(self):
        dst_url = "chrome://net-internals/#dns"
        self.loadURLandWait(dst_url)

        # tab 6 times
        tab_key = "U+0009"
        self.pressKeyKtimes(tab_key, 6)

        # press and release space bar
        space_bar = "U+0020"
        self.pressAndReleaseKey(space_bar)

        return

    def clearDeviceDNSCache(self):
        if self.device == "computer":
            self.clearComputerDNScache()
        elif self.device == "phone":
            self.clearPhoneDNScache()
        else:
            print("ERR. Unknown device '"+str(self.device)+"'")
            raise
        return

    def clearComputerDNScache(self):
        command = "ipconfig /flushdns"
        printAndCall(command)

    def clearPhoneDNScache(self):
        #print("Toggling Airplane Mode")
        #self.toggleAirplaneMode()
        return

    def toggleAirplaneMode(self):
        sleep_time = 0.5

        # open settings window
        command = "adb shell am start -a android.settings.AIRPLANE_MODE_SETTINGS"
        printAndCall(command)
        time.sleep(sleep_time)

        # tap on airplane mode
        self.adbShellKeyEvent("KEYCODE_DPAD_UP")
        time.sleep(sleep_time)
        self.adbShellKeyEvent("KEYCODE_ENTER")
        time.sleep(sleep_time)

        # tap on off/on button twice
        self.adbShellKeyEvent("KEYCODE_DPAD_RIGHT")
        time.sleep(sleep_time)
        self.adbShellKeyEvent("KEYCODE_ENTER")
        time.sleep(sleep_time*4)
        self.adbShellKeyEvent("KEYCODE_ENTER")
        time.sleep(sleep_time*4)

    def adbShellKeyEvent(self, keycode):
        command = "adb shell input keyevent "+keycode
        printAndCall(command)

    def pressKeyKtimes(self, keyIdentifier, num_times):
        params = {'type': 'rawKeyDown', 'keyIdentifier': keyIdentifier}
        for i in range(0, num_times):
            self.sendMethod("Input.dispatchKeyEvent", params, True)

    def navToURL(self, dst_url):
        if self.device == "phone":
            # bring chrome to front so we can watch
            command = "adb shell am start com.android.chrome"
            printAndCall(command)

        params = {'url': dst_url}
        self.sendMethod('Page.navigate', params, True)

    def _updateFrameDict(self, resp):
        try:
            method = resp["method"]
        except:
            pass
        else:
            if method == "Page.frameStartedLoading":
                frameId = resp["params"]["frameId"]
                self.frames[frameId] = True
                self.firstFrame = True
            elif method == "Page.frameStoppedLoading":
                frameId = resp["params"]["frameId"]
                self.frames.pop(frameId)

    #@timeout(3)
    def _getNextWsResp(self):
        resp = json.loads(self.ws.recv())
        self._updateFrameDict(resp)
        #conn.send(resp)
        return resp

    def _getFirstTimestamp(self):
        """
        Finds the first message with a valid timestamp.  Saves this value to 
        the object's first_timestamp attribute and returns the value.
        """
        print("Getting first_timestamp")
        while True:
            first_resp = self._getNextWsResp()
            self.msg_list.append(first_resp)

            try:
                method = first_resp["method"]
            except:
                method = None
                pass

            if method == "Network.requestWillBeSent":
                try:
                    first_timestamp = first_resp["params"]["timestamp"]
                except KeyError as e:
                    print("KeyError: "+str(first_resp))
                else:
                    # if successfully got first_timestamp, break out of loop
                    break

        print("first_timestamp: " + str(first_timestamp))
        self.first_timestamp = first_timestamp
        return first_timestamp

    def _isPastCutOffTime(self, this_timestamp):
        if (this_timestamp - self.first_timestamp) > self.cutoff_time:
            return True

    def _timeout(self, this_timestamp):
        print("last_timestamp: " + str(this_timestamp))
        self.last_timestamp = this_timestamp

    def _finishedLoading(self):
        # print("Nothing received through websocket for a few seconds.  Assume page is finished loading.")
        # print("Last resp recieved:")
        # print(this_resp)
        # print("last_timestamp: "+str(this_timestamp))
        # self.last_timestamp = this_timestamp
        if self.firstFrame == True and len(self.frames) == 0:
            return True

    def enforceNoneBlocked(self, resp):
        try:
            errorText = resp["params"]["errorText"]
        except:
            pass
        else:
            if errorText == "net::ERR_BLOCKED_BY_CLIENT" or errorText == "net::ERR_CONNECTION_REFUSED":
                self.logMsgs.append("Obj blocked while ad-blocker disabled: "+self.fname+" "+errorText)

    def enforceNoCache(self, resp):
        try:
            method = resp["method"]
        except:
            pass
        else:
            if method == "Network.requestServedFromCache":
                self.logMsgs.append("Obj served from cache: "+self.fname+" "+str(resp))

    def validateResp(self, resp):
        if self._isBlockingAds == False:
            self.enforceNoneBlocked(resp)
        self.enforceNoCache(resp)

    def _getDataUntilCutoff(self):
        """
        Appends data to the object's msg_list until it finds a message whose
        timestamp is past the cutoff_time.  Saves this last timestamp in the
        object's last_timestamp attribute.
        """
        this_resp = "{'None': None}"
        while True:
            if self._finishedLoading():
                print("Finished loading page.")
                return
            this_resp = self._getNextWsResp()
            self.validateResp(this_resp)
            # parent_conn, child_conn = multiprocessing.Pipe()    # open a channel
            # self.p = multiprocessing.Process(target=_getNextWsResp(self.ws, child_conn))
            # self.p.start()
            # self.p.join(3)  # block parent process until timeout or p terminates
            # if self.p.is_alive():
            #     # nothing received through websocket
            #     self.p.terminate()
            #     self.p.join()
            #     parent_conn.close()
            #     child_conn.close()
            #     self._finishedLoading(this_resp, this_timestamp)
            #     return
            #     # this_timestamp = time.time()
            #     # if self._isPastCutOffTime(this_timestamp):
            #     #     self._timeout(this_timestamp)
            #     #     return
            #     # else:
            #     #     # loop again
            #     #     continue
            # else:
            #     # there should be a resp waiting for us on the channel
            #     this_resp = parent_conn.recv()
            #     #print(this_resp)
            # parent_conn.close()
            # child_conn.close()
            
            self.msg_list.append(this_resp)

            try:
                method = this_resp["method"]
            except:
                method = None

            #if method == "Network.responseReceived":
                #print(this_resp)
            try:
                this_timestamp = this_resp["params"]["timestamp"]
                #this_timestamp = time.time()
            except KeyError as e:
                #print("KeyError. "+str(this_resp))
                pass # just check the next timestamp
            else:
                # if we have a value for this_timestamp, and it has been long enough
                # since the first timestamp, then break out of loop
                if self._isPastCutOffTime(this_timestamp):
                    self._timeout(this_timestamp)
                    print(this_resp)
                    return

    def _getHARresp(self):
        while True:
            this_resp = self.ws.recv()
            self.msg_list.append(this_resp)
            this_timestamp = time.time()

            if (this_timestamp - self.first_timestamp) > self.cutoff_time:
                print("last_timestamp: " + str(this_timestamp))
                self.last_timestamp = this_timestamp
                break


    def LoadPage_SaveData(self, output_dir, dst_url, sample_num):
        """
        Tells the connected browser to load the desired page.  Loads the page for
        the amount of time specified by the object's cutoff_time attribute.  Saves
        data on the page load to the object's msg_list.  When cutoff_time is reached,
        all the data in msg_list is written to a file in the specified output_dir.
        """
        # reset frame dict
        self.frames = {}
        self.firstFrame = False
        
        # update attributes
        self.page_url = dst_url
        hostname = urlparse(self.page_url).netloc
        self.fname = self.location+"-"+self.device+"-"+self.network_type+"-"+str(self._isBlockingAds)+"-"+\
                str(sample_num)+"-"+hostname+".txt"

        # Tell browser to load the desired page
        self.navToURL(self.page_url)

        # get data and put in msg_list
        first_timestamp = self._getFirstTimestamp()
        #self.first_timestamp = time.time()
        self._getDataUntilCutoff()

        # save data to file
        output_file = os.path.join(output_dir, self.fname)
        with open(output_file, "w") as f:
            json.dump(self.msg_list, f)

    # def getHar(self, output_dir, i):
    #     '''
    #     Tells the connected browser to load the desired page.  Loads the page for
    #     the amount of time specified by the object's cutoff_time attribute.  Saves the HAR
    #     file using the chrome.devtools.network.getHAR() method.
    #     '''
    #     self.ws.send(json.dumps({'id': i, 'method': 'Page.navigate', 'params': {'url': self.page_url}}))
    #     self.first_timestamp = time.time()
    #     self.ws.send(json.dumps({'id': i, 'method': 'chrome.devtools.network.getHAR', 'params': {}}))
    #     self._getHARresp()

    #     # save data to file
    #     hostname = urlparse(self.page_url).netloc + "-HAR.txt"
    #     output_file = os.path.join(output_dir, hostname)
    #     with open(output_file, "w") as f:
    #         json.dump(self.msg_list, f)