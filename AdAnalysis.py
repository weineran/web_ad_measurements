from urlparse import urlparse

blocked_err_msgs = ["net::ERR_CONNECTION_REFUSED", "net::ERR_BLOCKED_BY_CLIENT"]
loaded_statuses = [200]

class AutoDict(dict):
    """
    Implementation of perl's autovivification feature.
    Copied from http://stackoverflow.com/questions/635483/what-is-the-best-way-to-implement-nested-dictionaries-in-python
    """
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value

class AdAnalysis:

    #constructor
    def __init__(self, summaries_file_list):
        self.summaries_file_list = summaries_file_list
        self.max_sample_num = self.getMaxSampleNum()
        pass

    def appendDatapoint(self, a_list, datapoint, datapoint_sum, datapoint_count, attr):
        if datapoint != None:
            if "DataLength" in attr:
                datapoint = datapoint/1000    # if it is data, show it in KB

            # increment sum and count in avg_dict
            a_list.append(datapoint)
            datapoint_sum += datapoint
            datapoint_count += 1
        return datapoint_sum, datapoint_count

    def addDatatoDict(self, data_dict, baseName, cdf_key, datapoint):
        try:
            data_dict[baseName][cdf_key].append(datapoint)
        except KeyError:
            data_dict[baseName][cdf_key] = [datapoint]


    def insertY_Val(self, DICT_VS_BLOCKED, this_plot, series_label, y_datapoint):
        try:
            DICT_VS_BLOCKED[this_plot]["y_vals"][series_label].append(y_datapoint)
        except KeyError:
            DICT_VS_BLOCKED[this_plot]["y_vals"][series_label] = [y_datapoint]

    def insertX_Val(self, DICT_VS_BLOCKED, this_plot, series_label, x_datapoint):
        try:
            DICT_VS_BLOCKED[this_plot]["x_vals"][series_label].append(x_datapoint)
        except KeyError:
            DICT_VS_BLOCKED[this_plot]["x_vals"][series_label] = [x_datapoint]

    def findFirstEventIdx(self, event_list, filename):
        for idx in range(0, len(event_list)):
            this_event = event_list[idx]
            if type(this_event) != type({}):
                continue
            try:
                method = this_event["method"]
            except KeyError:
                continue
            else:
                if method == "Page.navigate":
                    this_url = this_event["params"]["url"]
                    hostname = urlparse(this_url).netloc
                    file_hostname = self.getHostname(filename)
                    if hostname == file_hostname:
                        #print("found Page.navigate to "+this_url)
                        search_id = this_event["id"]
                        for idx2 in range(idx+1, len(event_list)):
                            this_event = event_list[idx2]
                            try:
                                this_id = this_event["id"]
                            except KeyError:
                                pass
                            else:
                                if this_id == search_id:
                                    return idx2 + 1

    def isLoadEvent(self, this_event):
        method = self.getMethod(this_event)
        if method == "Page.loadEventFired":
            return True
        else:
            return False

    def getFirstTimestamp(self, this_event):
        if self.getMethod(this_event) == "Network.requestWillBeSent":
            firstTimestamp = this_event["params"]["timestamp"]
            foundFirstReq = True
        else:
            firstTimestamp = None
            foundFirstReq = False

        return foundFirstReq, firstTimestamp


    def getMethod(self, this_event):
        try:
            method = this_event["method"]
        except KeyError:
            method = None

        return method


    def processEvent(self, this_event, url_dict, b_or_n, reqID_dict, firstTimestamp):
        try:
            method = this_event["method"]
        except KeyError:
            return
        else:
            if method == "Network.requestWillBeSent":
                requestId = this_event["params"]["requestId"]
                self.processRequestWillBeSent(this_event, url_dict, b_or_n, reqID_dict, requestId)

                # TODO get size of request dict (lookup how online)
                    
            elif method == "Network.responseReceived":
                requestId = this_event["params"]["requestId"]
                this_url = this_event["params"]["response"]["url"]
                if type(url_dict[this_url][b_or_n]) == type(1):
                    url_dict[this_url][b_or_n]['responseCount'] += 1
                else:
                    url_dict[this_url][b_or_n]['responseCount'] = 1

            elif method == "Network.loadingFailed":
                requestId = this_event["params"]["requestId"]
                self.processLoadingFailed(this_event, url_dict, b_or_n, reqID_dict, requestId, firstTimestamp)
            elif method == "Network.loadingFinished":
                requestId = this_event["params"]["requestId"]
                self.processLoadingFinished(this_event, url_dict, b_or_n, reqID_dict, requestId, firstTimestamp)


    def processUrl(self, url, url_dict, blocking_list_timeStartToFinished, nonblocking_list_timeStartToFinished,
                loadEventTimestamp_blocking, loadEventTimestamp_nonblocking):
        # TODO need to check also Referer in headers
        n_initiator_url = url_dict[url]["nonblocking"]["initiator_url"]
        n_initiator_type = url_dict[url]["nonblocking"]["initiator_type"]
        print("process_url: "+str(url))
        print("initiator_url: "+str(n_initiator_url))

        if type(url_dict[url]["isAd"]) != type(True):
            # if this url is not already labeled...
            if n_initiator_url == None:
                # if it has no initiator, assume not an ad
                url_dict[url]["isAd"] = False
            else:
                # if it has initiator, label it same as its initiator
                url_dict[url]["isAd"] = self.isAd(n_initiator_url, url_dict)
        else:
            # if already labeled, then leave it so
            pass

        # timeStartToFinished
        blocking_timeStartToFinished = url_dict[url]["blocking"]["timeStartToFinished"]
        blocking_timestampFinished = url_dict[url]["blocking"]["timestampFinished"]
        nonblocking_timeStartToFinished = url_dict[url]["nonblocking"]["timeStartToFinished"]
        nonblocking_timestampFinished = url_dict[url]["nonblocking"]["timestampFinished"]

        if blocking_timestampFinished < loadEventTimestamp_blocking:
            blocking_list_timeStartToFinished.append(blocking_timeStartToFinished)
        if nonblocking_timestampFinished < loadEventTimestamp_nonblocking:
            nonblocking_list_timeStartToFinished.append(nonblocking_timeStartToFinished)


    def isAd(self, url, url_dict):
        print("url: "+str(url))
        if type(url_dict[url]["isAd"]) == type(True):
            # if already labeled, return answer
            return url_dict[url]["isAd"]
        else:
            # otherwise, find out if initiator is an ad, and assume the same for this
            n_initiator_url = url_dict[url]["nonblocking"]["initiator_url"]
            if n_initiator_url == None:
                url_dict[url]["isAd"] = False
            else:
                url_dict[url]["isAd"] = self.isAd(n_initiator_url, url_dict)

            return url_dict[url]["isAd"]


    def processLoadingFailed(self, this_event, url_dict, b_or_n, reqID_dict, requestId, firstTimestamp):
        this_url = self.getUrlByReqID(reqID_dict, requestId)
        timestamp = this_event['params']['timestamp']
        timeStartToFinished = timestamp - firstTimestamp

        timestampRequest = url_dict[this_url][b_or_n]["timestampRequest"]
        timeRequestToFinished = timestamp - timestampRequest

        url_dict[this_url][b_or_n]['timestampFinished'] = timestamp
        url_dict[this_url][b_or_n]['timeStartToFinished'] = timeStartToFinished
        url_dict[this_url][b_or_n]['timeRequestToFinished'] = timeRequestToFinished

        errorText = this_event['params']['errorText']
        if errorText in blocked_err_msgs:
            if b_or_n == "blocking":
                if type(url_dict[this_url][b_or_n]["blockedCount"]) == type(1):
                    url_dict[this_url][b_or_n]["blockedCount"] += 1
                else:
                    url_dict[this_url][b_or_n]["blockedCount"] = 1
                url_dict[this_url]["isAd"] = True
                url_dict[this_url]["isDirectlyBlocked"] = True
            elif b_or_n == "nonblocking":
                print("nonblocking file blocked a URL?\nurl: "+this_url)
            else:
                print("invalid b_or_n: "+b_or_n)
                raise
        else:
            print("errorText: "+errorText)
            if type(url_dict[this_url][b_or_n]["failedCount"]) == type(1):
                url_dict[this_url][b_or_n]["blockedCount"] += 1
            else:
                url_dict[this_url][b_or_n]["blockedCount"] = 1

        

    def processLoadingFinished(self, this_event, url_dict, b_or_n, reqID_dict, requestId, firstTimestamp):
        this_url = self.getUrlByReqID(reqID_dict, requestId)
        timestamp = this_event['params']['timestamp']
        timeStartToFinished = timestamp - firstTimestamp

        timestampRequest = url_dict[this_url][b_or_n]["timestampRequest"]
        timeRequestToFinished = timestamp - timestampRequest

        url_dict[this_url][b_or_n]['timestampFinished'] = timestamp
        url_dict[this_url][b_or_n]['timeStartToFinished'] = timeStartToFinished
        url_dict[this_url][b_or_n]['timeRequestToFinished'] = timeRequestToFinished

            
    def getUrlByReqID(self, reqID_dict, requestId):
        this_url = reqID_dict[requestId]['url']
        return this_url

                
    def processRequestWillBeSent(self, this_event, url_dict, b_or_n, reqID_dict, requestId, firstTimestamp):
        timestamp = this_event['params']['timestamp']
        timeStartToRequest = timestamp - firstTimestamp
        this_url = this_event["params"]["request"]["url"]
        url_by_id = self.getUrlByReqID(reqID_dict, requestId)
        if type(url_by_id) != type(""):
            reqID_dict[requestId]['url'] = this_url
        else:
            if url_by_id != this_url:
                print("Two different URLs for a single requestId")
                print(url_by_id)
                print(this_url)
                raise

        url_dict[this_url][b_or_n]['timestampRequest'] = timestamp
        url_dict[this_url][b_or_n]['timeStartToRequest'] = timeStartToRequest

        if type(url_dict[this_url][b_or_n]['requestCount']) == type(1):
            url_dict[this_url][b_or_n]['requestCount'] += 1
        else:
            url_dict[this_url][b_or_n]['requestCount'] = 1

        if type(reqID_dict[requestId]["requestCount"]) == type(1):
            reqID_dict[requestId]["requestCount"] += 1
        else:
            reqID_dict[requestId]["requestCount"] = 1
        
        try:
            initiator_type = this_event["params"]["initiator"]["type"]
        except KeyError:
            initiator_type = None

        try:
            initiator_url = this_event["params"]["initiator"]["url"]
        except KeyError:
            try:
                initiator_url = this_event["params"]["initiator"]["stack"]["callFrames"][0]["url"]
            except (KeyError, IndexError):
                initiator_url = None

        url_dict[this_url][b_or_n]['initiator_type'] = initiator_type
        url_dict[this_url][b_or_n]['initiator_url'] = initiator_url
        reqID_dict[requestId]['initiator_type'] = initiator_type
        reqID_dict[requestId]['initiator_url'] = initiator_url


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
        line1 = attr_info["x-label"]+'\n'
        event = attr_info["event"]
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
        elif file_flag == "Both":
            datapoint = {"with-ads": self.getValAtEvent(attr, dictNoBlock, event), "no-ads": self.getValAtEvent(attr, dictYesBlock, event)}
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

    def getRawFromSummary(self, summary_file, raw_data_file_list):
        target_fname = summary_file.replace("-summary.json", ".txt")
        if target_fname in raw_data_file_list:
            return target_fname
        else:
            print(target_fname+" not found")
            #raise
            return None

    #@staticmethod
    def getMatchButFalse(self, this_file, data_file_list):
        target_fname = this_file.replace("-True-","-False-",1)
        if target_fname in data_file_list:
            return target_fname
        else:
            return None
    #@staticmethod
    def getMatchButTrue(self, this_file, data_file_list):
        target_fname = this_file.replace("-False-","-True-",1)
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
            if div_loc == -1:
                # if we're looking in a raw file, not a summary file, there is no final '-'
                div_loc = -4
            this_attr = fname_modified[0:div_loc]
            fname_modified = fname_modified[div_loc+1:]
            i += 1
        return this_attr

    def getHostnameFromAttrStr(self, attrStr):
        i = 0
        while i <= 4:
            div_loc = attrStr.find('-')
            attrStr = attrStr[div_loc+1:]
            i += 1
        return attrStr

    def getHostnameFromSummary(self, summary_file):
        attrStr = summary_file[:-13]
        return self.getHostnameFromAttrStr(attrStr)

    def getHostnameFromRaw(self, raw_file):
        attrStr = raw_file[:-4]
        return self.getHostnameFromAttrStr(attrStr)
            

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

    def getLocation(self, this_file):
        return self.getAttr(0, this_file)

    def getHostname(self, this_file):
        #return self.getAttr(5, this_file)
        if this_file.endswith("-summary.json"):
            hostname = self.getHostnameFromSummary(this_file)
        elif this_file.endswith(".txt"):
            hostname = self.getHostnameFromRaw(this_file)
        else:
            print("invalid filename: "+this_file)
            raise

        return hostname

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
                return True
            else:
                return False