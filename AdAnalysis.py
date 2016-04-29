
blocked_err_msgs = ["net::ERR_CONNECTION_REFUSED", "net::ERR_BLOCKED_BY_CLIENT"]
loaded_statuses = [200]

class AdAnalysis:

    #constructor
    def __init__(self, summaries_file_list):
        self.summaries_file_list = summaries_file_list
        self.max_sample_num = self.getMaxSampleNum()
        pass

    def getMaxSampleNum(self):
        max_sample_num = 0
        for filename in self.summaries_file_list:
            if filename[0] == '.':
                continue
            this_num = int(self.getSampleNum(filename))
            if this_num > max_sample_num:
                max_sample_num = this_num
        return max_sample_num

    def getXLabel(self, label_dict, attr):
        attr_info = label_dict[attr]
        line1 = attr_info[0]+'\n'
        event = attr_info[2]
        if event == "DOM":
            line2 = "(cutoff at DOMContentLoaded event)\n"
        elif event == "Load":
            line2 = "(cutoff at page Load event)\n"
        elif event == "Final":
            line2 = "(Loading finished or cutoff time reached)\n"
        else:
            print("invalid event: "+str(event))
            raise
        return line1+line2

    def getKeyAndVal(self, attr, dictNoBlock, dictYesBlock, file_flag, event):
        """
        returns a dict: {'cdf_key': cdf_key, 'datapoint': datapoint}
        """
        if file_flag == True:
            datapoint = self.getValAtEvent(attr, dictYesBlock, event)
        elif file_flag == False:
            datapoint = self.getValAtEvent(attr, dictNoBlock, event)
        elif file_flag == "Diff":
            try:
                datapoint = self.getValAtEvent(attr, dictNoBlock, event) - self.getValAtEvent(attr, dictYesBlock, event)
            except TypeError:
                datapoint = None
        else:
            print("invalid file_flag: "+str(file_flag))
            raise

        cdf_key = self.getCDFKey(dictYesBlock)
        return {'cdf_key': cdf_key, 'datapoint': datapoint}

    def getDatapoint(self, attr, dictNoBlock, dictYesBlock, file_flag, event):
        """
        returns a the datapoint for the given attribute
        """
        if file_flag == True:
            datapoint = self.getValAtEvent(attr, dictYesBlock, event)
        elif file_flag == False:
            datapoint = self.getValAtEvent(attr, dictNoBlock, event)
        elif file_flag == "Diff":
            try:
                datapoint = self.getValAtEvent(attr, dictNoBlock, event) - self.getValAtEvent(attr, dictYesBlock, event)
            except TypeError:
                datapoint = None
        else:
            print("invalid file_flag: "+str(file_flag))
            raise

        return datapoint

    def getValAtEvent(self, attr, the_dict, event):
        if event == "Final":
            datapoint = the_dict[attr]
        elif event == "DOM":
            try:
                datapoint = the_dict['statsAtDOMEvent'][attr]
            except KeyError:
                datapoint = None
        elif event == "Load":
            try:
                datapoint = the_dict['statsAtOnLoadEvent'][attr]
            except KeyError:
                datapoint = None
        else:
            print("invalid event: "+str(event))
            raise

        return datapoint

    def getCDFKey(self, the_dict):
        if type(the_dict) == type(""):
            this_file = the_dict
        else:
            this_file = the_dict['rawDataFile']
        device = self.getDevice(this_file)
        network_type = self.getNetworkType(this_file)
        cdf_key = device+"-"+network_type
        return cdf_key

    def statsDiff(self, dictNoBlock, dictYesBlock, key):
        try:
            return dictNoBlock[key] - dictYesBlock[key]
        except:
            return None

    def DOMDiff(self, dictNoBlock, dictYesBlock, key):
        try:
            return dictNoBlock['statsAtDOMEvent'][key] - dictYesBlock['statsAtDOMEvent'][key]
        except:
            return None

    def LoadDiff(self, dictNoBlock, dictYesBlock, key):
        try:
            return dictNoBlock['statsAtOnLoadEvent'][key] - dictYesBlock['statsAtOnLoadEvent'][key]
        except:
            return None

    #@staticmethod
    def getAdFileMatch(self, this_file, data_file_list):
        if self.isBlocking(this_file):
            return self.getMatchButFalse(this_file, data_file_list)
        else:
            return self.getMatchButTrue(this_file, data_file_list)

    #@staticmethod
    def getMatchButFalse(self, this_file, data_file_list):
        target_fname = this_file.replace("True","False",1)
        if target_fname in data_file_list:
            return target_fname
        else:
            return None
    #@staticmethod
    def getMatchButTrue(self, this_file, data_file_list):
        target_fname = this_file.replace("False","True",1)
        if target_fname in data_file_list:
            return target_fname
        else:
            return None

    def getListOfPairs(self, summary_file, summaries_file_list):
        the_list = []
        blocking_file = summary_file
        for i in range(0, self.max_sample_num):
            this_pair = (blocking_file, self.getMatchButFalse(blocking_file, summaries_file_list))
            the_list.append(this_pair)
            sample_num = self.getSampleNum(blocking_file)
            blocking_file = blocking_file.replace('-'+sample_num+'-', '-'+str(int(sample_num)+1)+'-',1)

        return the_list

    #@staticmethod
    def getChronFileList(self, this_file, data_file_list):
        chron_file_list = [this_file]
        curr_file = this_file
        while True:
            sample_num = self.getSampleNum(curr_file)
            target_fname = curr_file.replace('-'+sample_num+'-', '-'+str(int(sample_num)+1)+'-',1)
            if target_fname in data_file_list:
                chron_file_list.append(target_fname)
                curr_file = target_fname
            else:
                return chron_file_list

    #@staticmethod
    def isBlocking(self, this_file):
        t_or_f = self.getAttr(3, this_file)
        if t_or_f == "True":
            return True
        elif t_or_f == "False":
            return False
        else:
            raise

    #@staticmethod
    def getAttr(self, attr_num, this_file):
        fname_modified = this_file
        i = 0
        while i <= attr_num:
            div_loc = fname_modified.find('-')
            this_attr = fname_modified[0:div_loc]
            fname_modified = fname_modified[div_loc+1:]
            #print(this_attr)
            i += 1
        #print(this_file+": "+this_attr)
        return this_attr

    def isFirstSample(self, this_file):
        sample_num = self.getSampleNum(this_file)
        if sample_num == '1':
            return True
        else:
            return False

    def getSampleNum(self, this_file):
        return self.getAttr(4, this_file)

    def getDevice(self, this_file):
        return self.getAttr(1, this_file)

    def getHostname(self, this_file):
        return self.getAttr(5, this_file)

    def getNetworkType(self, this_file):
        return self.getAttr(2, this_file)

    def isLog(self, this_file):
        if this_file[-3:] == "log":
            return True
        else:
            return False

    def calcNumBlocked(self, resp_list):
        num_blocked = 0
        for this_resp in resp_list:
            if self.isObjBlocked(this_resp):
                num_blocked += 1
        return num_blocked

    def isObjBlocked(self, this_resp):
        try:
            errorText = this_resp["params"]["errorText"]
        except:
            pass
        else:
            if errorText in blocked_err_msgs:
                return True
        return False

    def calcNumRequested(self, resp_list):
        num_requested = 0
        for this_resp in resp_list:
            if self.isObjRequested(this_resp):
                num_requested += 1
        return num_requested

    def isObjRequested(self, this_resp):
        try:
            method = this_resp["method"]
        except:
            pass
        else:
            if method == "Network.requestWillBeSent":
                return True
        return False

    def calcNumLoaded(self, resp_list):
        num_loaded = 0
        for this_resp in resp_list:
            if self.isObjLoaded(this_resp):
                num_loaded += 1
        return num_loaded

    def isObjLoaded(self, this_resp):
        try:
            status = this_resp["params"]["response"]["status"]
        except:
            pass
        else:
            if status in loaded_statuses:
                return True
        return False

    def calcOnLoadTime(self, resp_list):
        first_timestamp = None
        for this_resp in resp_list:
            first_timestamp = self.updateFirstTimestamp(first_timestamp, this_resp)
            if self.isOnLoadEvent(this_resp):
                onLoad_timestamp = this_resp["params"]["timestamp"]
                break
        try:
            onLoad_time_diff = onLoad_timestamp - first_timestamp
        except UnboundLocalError:
            return None
        else:
            return onLoad_time_diff

    def updateFirstTimestamp(self, first_timestamp, this_resp):
        try:
            this_timestamp = this_resp["params"]["timestamp"]
        except KeyError:
            return first_timestamp
        else:
            if first_timestamp == None or this_timestamp < first_timestamp:
                #print(this_timestamp)
                return this_timestamp
            else:
                return first_timestamp

    def isOnLoadEvent(self, this_resp):
        try:
            method = this_resp["method"]
        except KeyError:
            return False
        else:
            if method == "Page.loadEventFired":
                #print("found")
                return True
            else:
                return False