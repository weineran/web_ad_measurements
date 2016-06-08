import json
import os
import argparse
import time
import numpy
from numpy import percentile
from AdAnalysis import AdAnalysis
from aqualab.plot.mCdf import keyedCdf
import matplotlib.pyplot as plt
from scipy.stats import linregress
#from statsmodels.distributions.empirical_distribution import ECDF
import statsmodels.distributions
import csv
from collections import OrderedDict

doScatterPlots = False
useCategories = False
orig_cdf_method = "median_diff"
fig_subdir = "figs-5-11"
csv_subdir = "CSVs-5-11"
excludeNoAds = False
excludeTime = False

# For CDFs
colors = ['b', 'g', 'r', 'c', 'm', 'k']
markers = ['o', '^', 's', 'v', '+']
sep = ','
nl = '\n'
tab = "    "

def parse_args():
    parser = argparse.ArgumentParser(
            description='analyze data')
    parser.add_argument('data_dir', type=str,
                    help="The directory containing the data files to analyze.  Should contain subdirectories\n"+
                        "called 'raw', 'summaries', and 'log'.  Plots will be saved to a subdirectory called 'figs'")
    parser.add_argument('rank_cutoff', type=int,
                    help="All websites ranked higher than rank_cutoff in a given category will be included in the figure.  Websites ranked "+
                        "lower will be excluded.")
    parser.add_argument('--exclude_list_mobile', type=str,
                    help="A .json file containing mobile hostnames to exclude.  This is useful if, for example, "+
                    "you want to filter out certain websites that are known to be special cases or outliers.")
    parser.add_argument('--exclude_list_desktop', type=str,
                    help="A .json file containing desktop hostnames to exclude.  This is useful if, for example, "+
                    "you want to filter out certain websites that are known to be special cases or outliers.")
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    start_time = time.clock()
    args = parse_args()
    data_dir = args.data_dir
    rank_cutoff = args.rank_cutoff
    exclude_list_mobile = args.exclude_list_mobile
    exclude_list_desktop = args.exclude_list_desktop

    # prep directories
    list_out_dir = os.path.join(data_dir, "measured_lists")
    raw_data_dir = os.path.join(data_dir, "raw")
    summaries_dir = os.path.join(data_dir, "summaries")
    fig_dir = os.path.join(data_dir, fig_subdir)
    csv_dir = os.path.join(data_dir, csv_subdir)
    raw_data_file_list = os.listdir(raw_data_dir)
    summaries_file_list = os.listdir(summaries_dir)
    if not os.path.isdir(fig_dir):
        os.mkdir(fig_dir)
    if not os.path.isdir(csv_dir):
        os.mkdir(csv_dir)
    if not os.path.isdir(list_out_dir):
        os.mkdir(list_out_dir)

    aa = AdAnalysis(summaries_file_list)

    # create list of cdfs
    resolution = 0.1
    data_dict = {}
    for baseName in aa.MASTER_DICT:
        if baseName in aa.DICT_ORIG_CDFS:
            data_dict[baseName] = {}
            # make a list of cdfs
            attr = baseName.split('-',1)[1]
            aa.DICT_ORIG_CDFS[baseName]["cdf"] = keyedCdf(baseName=baseName, xlabel=aa.getXLabel(aa.DICT_ORIG_CDFS, baseName), resolution=resolution)
            aa.DICT_ORIG_CDFS[baseName]["raw_data"] = {} # <cdf_key, (fname, raw_data)[]>

    # create dict of scatter plots
    for y_label in aa.DICT_Y_VS_EXPLICITLY_BLOCKED:
        aa.DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["scatter_plot_fig"] = plt.figure(figsize=(8,13))
        aa.DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["x_vals"] = {}    # {series_label1: [], series_label2: []}
        aa.DICT_Y_VS_EXPLICITLY_BLOCKED[y_label]["y_vals"] = {}    # {series_label1: [], series_label2: []}

    # create dict of range CDFs
    for range_cdf in aa.DICT_RANGE_CDFS:
        aa.DICT_RANGE_CDFS[range_cdf]["range_cdf_fig"] = plt.figure(figsize=(6,4.5))
        aa.DICT_RANGE_CDFS[range_cdf]["raw_data"] = OrderedDict() # <cdf_key, (fname, raw_data)[]>

    ad_compare_dict = {}
    chron_compare_dict = {}
    ad_chron_dict = OrderedDict()      # {summary_file: list_of_pairs}
    new_exclude_dict_mobile = {}   # we are building in this script
    new_exclude_dict_desktop = {}   # we are building in this script

    if exclude_list_mobile != None:
        with open(exclude_list_mobile, 'r') as x_file:
            exclude_dict_mobile = json.load(x_file)
    else:
        exclude_dict_mobile = {}

    if exclude_list_desktop != None:
        with open(exclude_list_desktop, 'r') as x_file:
            exclude_dict_desktop = json.load(x_file)
    else:
        exclude_dict_desktop = {}

    # loop through summary files and build dicts
    aa.setLegendOrder(summaries_file_list, aa.LEGEND_DICT)
    for summary_file in summaries_file_list:

        if aa.isBlocking(summary_file):
            # map summary files with ad-blocker to summary files without ad-blocker
            ad_file_match = aa.getAdFileMatch(summary_file, summaries_file_list)
            ad_compare_dict[summary_file] = ad_file_match
            if aa.isFirstSample(summary_file):
                # map first blocking summary file to chronological list of all pairs of (blocking, nonblocking)
                list_of_pairs = aa.getListOfPairs(summary_file, summaries_file_list)
                ad_chron_dict[summary_file] = list_of_pairs
        if aa.isFirstSample(summary_file):
            # map first summary file to list of all matching summary files
            chron_list = aa.getChronFileList(summary_file, summaries_file_list)
            chron_compare_dict[summary_file] = chron_list
    print(len(ad_chron_dict))
    #a = input("enter a num to continue")

    page_stats = {}

    pageloadData = []

    resp_list = None
    #for blocking_summary_file in ad_compare_dict:
    #    nonblocking_summary_file = ad_compare_dict[blocking_summary_file]
    print("num key_files: "+str(len(ad_chron_dict)))
    for key_file in ad_chron_dict:
        cdf_key = aa.getCDFKey(key_file)
        try:
            cdf_key = aa.LEGEND_DICT[cdf_key]
        except KeyError:
            print(key_file)
            continue

        list_of_dicts = []

        # open a list of pairs of summary dictionaries
        for file_pair in ad_chron_dict[key_file]:
            blocking_summary_file = file_pair[0]
            nonblocking_summary_file = file_pair[1]

            if nonblocking_summary_file == None or blocking_summary_file == None:
                continue

            # open the pair of files
            full_path_blocking = os.path.join(summaries_dir, blocking_summary_file)
            f = open(full_path_blocking, 'r')
            #print("Loading "+blocking_summary_file)
            blocking_summary_dict = json.load(f)
            f.close()

            full_path_nonblocking = os.path.join(summaries_dir, nonblocking_summary_file)
            f = open(full_path_nonblocking, 'r')
            #print("Loading "+nonblocking_summary_file)
            nonblocking_summary_dict = json.load(f)
            f.close()

            list_of_dicts.append((blocking_summary_dict, nonblocking_summary_dict))

        # skip hostnames designated for exclusion
        hostname = aa.getHostname(key_file)
        device_type = aa.getDeviceTypeFromSummary(list_of_dicts[0][0])
        if device_type == "phone" and hostname in exclude_dict_mobile:
            print("phone "+hostname)
            continue
        if device_type == "computer" and hostname in exclude_dict_desktop:
            print("computer "+hostname)
            continue

        # loop through all cdfs
        if len(list_of_dicts) > 0:
            categories_dict = list_of_dicts[0][0]['categories_and_ranks']
        else:
            continue

        for fig_key in aa.MASTER_DICT:
            baseName = fig_key
            attr = aa.MASTER_DICT[fig_key]["attr"]
            #file_flag = aa.DICT_ORIG_CDFS[baseName]["file_flag"]
            #event = aa.DICT_ORIG_CDFS[baseName]["event"]
            event = baseName.split('-',1)[0]
            datapoint_sum = 0
            datapoint_count = 0
            datapoint_blocking_sum = 0
            datapoint_blocking_count = 0
            datapoint_nonblocking_sum = 0
            datapoint_nonblocking_count = 0

            # loop through pairs in the list
            datapoint_diff_list = []         # if there are 5 samples, then there are 5 elems in list
            datapoint_blocking_list = []
            datapoint_nonblocking_list = []
            for dict_pair in list_of_dicts:
                blocking_summary_dict = dict_pair[0]
                nonblocking_summary_dict = dict_pair[1]
            
                datapoint_blocking = aa.getDatapoint(attr, nonblocking_summary_dict, blocking_summary_dict, True, event)
                datapoint_nonblocking = aa.getDatapoint(attr, nonblocking_summary_dict, blocking_summary_dict, False, event)
                try:
                    datapoint_diff = datapoint_nonblocking - datapoint_blocking
                except TypeError:
                    datapoint_diff = None

                datapoint_sum, datapoint_count = aa.appendDatapoint(datapoint_diff_list, datapoint_diff, datapoint_sum, datapoint_count, attr)
                datapoint_blocking_sum, datapoint_blocking_count = aa.appendDatapoint(datapoint_blocking_list, datapoint_blocking, datapoint_blocking_sum, datapoint_blocking_count, attr)
                datapoint_nonblocking_sum, datapoint_nonblocking_count = aa.appendDatapoint(datapoint_nonblocking_list, datapoint_nonblocking, datapoint_nonblocking_sum, datapoint_nonblocking_count, attr)

            if len(datapoint_blocking_list) > 0:
                med_blocking_datapoint = numpy.median(datapoint_blocking_list)
                min_blocking_datapoint = min(datapoint_blocking_list)
                max_blocking_datapoint = max(datapoint_blocking_list)
                avg_blocking_datapoint = numpy.average(datapoint_blocking_list)

            if len(datapoint_nonblocking_list) > 0:
                med_nonblocking_datapoint = numpy.median(datapoint_nonblocking_list)
                min_nonblocking_datapoint = min(datapoint_nonblocking_list)
                max_nonblocking_datapoint = max(datapoint_nonblocking_list)
                avg_nonblocking_datapoint = numpy.average(datapoint_nonblocking_list)

            if len(datapoint_diff_list) > 0:
                # get datapoints
                med_diff_datapoint = numpy.median(datapoint_diff_list)
                min_diff_datapoint = min(datapoint_diff_list)
                max_diff_datapoint = max(datapoint_diff_list)
                avg_diff_datapoint = numpy.average(datapoint_diff_list)

                # insert datapoints
                # cdf.insert(cdf_key+" (median)", med_diff_datapoint)
                # cdf.insert(cdf_key+" (min-dif)", min_diff_datapoint)
                # cdf.insert(cdf_key+" (max-dif)", max_diff_datapoint)
                # cdf.insert(cdf_key+" (avg)", avg_diff_datapoint)

                # add datapoints to datadict
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (med-dif)", med_diff_datapoint)
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (min-dif)", min_diff_datapoint)
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (max-dif)", max_diff_datapoint)
                # aa.addDatatoDict(data_dict, baseName, cdf_key+" (avg-dif)", avg_diff_datapoint)

            # make Range CDFs
            if fig_key in aa.DICT_RANGE_CDFS:
                if len(datapoint_blocking_list) > 0 and len(datapoint_nonblocking_list) > 0:
                    ff = aa.DICT_RANGE_CDFS[baseName]["file_flag"]
                    if ff == "Diff":
                        range_datapoint = max_diff_datapoint - min_diff_datapoint
                        denominator = min_diff_datapoint
                    elif ff == True:
                        range_datapoint = max_blocking_datapoint - min_blocking_datapoint
                        denominator = min_blocking_datapoint
                    elif ff == False:
                        range_datapoint = max_nonblocking_datapoint - min_nonblocking_datapoint
                        denominator = min_nonblocking_datapoint

                    if aa.DICT_RANGE_CDFS[fig_key]["doPercent"] == True:
                        try:
                            range_datapoint = (float(range_datapoint) / float(denominator))*100
                        except (ZeroDivisionError, TypeError):
                            range_datapoint = None

                    if aa.shouldExclude("Load-responseReceivedCount-True-doPercent", fig_key, range_datapoint, denominator, excludeNoAds, excludeTime):
                    #or aa.shouldExclude("Final-time_onLoad-False", fig_key, range_datapoint, denominator, excludeNoAds, excludeTime):
                        if device_type == "phone":
                            new_exclude_dict_mobile[hostname] = True
                        elif device_type == "computer":
                            new_exclude_dict_desktop[hostname] = True

                    if range_datapoint != None:
                        try:
                            aa.DICT_RANGE_CDFS[baseName]["raw_data"][cdf_key].append((key_file, range_datapoint))
                        except KeyError:
                            aa.DICT_RANGE_CDFS[baseName]["raw_data"][cdf_key] = [(key_file, range_datapoint)]
                            #DICT_RANGE_CDFS[range_cdf]["fnames"][cdf_key]= [key_file]
                        else:
                            #DICT_RANGE_CDFS[range_cdf]["fnames"][cdf_key].append(key_file)
                            pass

            if fig_key in aa.DICT_ORIG_CDFS:
                #if hostname == "msn.com": print(key_file)
                cdf = aa.DICT_ORIG_CDFS[fig_key]["cdf"]
                if len(datapoint_blocking_list) > 0 and len(datapoint_nonblocking_list) > 0:
                    try:
                        this_orig_cdf_method = aa.DICT_ORIG_CDFS[fig_key]["method"]
                    except KeyError:
                        this_orig_cdf_method = orig_cdf_method

                    datapoint, key_suffix = aa.selectDatapoint(this_orig_cdf_method, min_nonblocking_datapoint, min_blocking_datapoint,
                                                                max_diff_datapoint, min_diff_datapoint,
                                                                med_blocking_datapoint, med_diff_datapoint)

                    if aa.shouldExclude("Load-numBlockedExplicitly", fig_key, datapoint, None, excludeNoAds, excludeTime):
                        if device_type == "phone":
                            new_exclude_dict_mobile[hostname] = True
                        elif device_type == "computer":
                            new_exclude_dict_desktop[hostname] = True

                    cdf.insert(cdf_key+key_suffix, datapoint)
                    aa.addDatatoDict(data_dict, baseName, cdf_key+key_suffix, datapoint)
                    try:
                        aa.DICT_ORIG_CDFS[fig_key]["raw_data"][cdf_key].append((key_file, datapoint))
                    except KeyError:
                        aa.DICT_ORIG_CDFS[fig_key]["raw_data"][cdf_key] = [(key_file, datapoint)]

                    if useCategories:
                        for category in categories_dict:
                            if categories_dict[category] <= rank_cutoff:
                                #cdf.insert(cdf_key+"-"+category+" (med)", med_diff_datapoint)
                                cdf.insert(category+key_suffix, datapoint)
                                try:
                                    #data_dict[baseName][cdf_key+"-"+category+" (med)"].append(med_diff_datapoint)
                                    data_dict[baseName][category+key_suffix].append(datapoint)
                                except KeyError:
                                    #data_dict[baseName][cdf_key+"-"+category+" (med)"] = [med_diff_datapoint]
                                    data_dict[baseName][category+key_suffix] = [datapoint]

        # FINISH LOOPING THROUGH CDFs

                
        # This loop is executed for each file
        # We add this file (or rather file group) to the plot data
        if doScatterPlots:
            for this_scatterPlot in aa.DICT_Y_VS_EXPLICITLY_BLOCKED:
                event = aa.DICT_Y_VS_EXPLICITLY_BLOCKED[this_scatterPlot]["event"]
                y_attr = aa.DICT_Y_VS_EXPLICITLY_BLOCKED[this_scatterPlot]["attr"]
                file_flag = aa.DICT_Y_VS_EXPLICITLY_BLOCKED[this_scatterPlot]["file_flag"]
                #cdf_key = aa.getDevice(key_file)
                cdf_key = aa.getCDFKey(key_file)
                for dict_pair in list_of_dicts:
                    blocking_summary_dict = dict_pair[0]
                    nonblocking_summary_dict = dict_pair[1]

                    x_datapoint = aa.getDatapoint("numBlockedExplicitly", nonblocking_summary_dict,
                                                blocking_summary_dict, True, event)
                    
                    y_datapoint = aa.getDatapoint(y_attr, nonblocking_summary_dict,
                                                blocking_summary_dict, file_flag, event)
                    if y_datapoint != None:
                        if "DataLength" in y_attr:
                            y_datapoint = y_datapoint/1000    # if it is data, show it in KB
                        if file_flag == "Both":
                        # getDatapoint returned a dict {"with-ads": datapoint, "no-ads": datapoint}
                            series_label = cdf_key+"-with-ads"
                            if y_datapoint["with-ads"] != None:
                                aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint["with-ads"])
                                aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)
                            series_label = cdf_key+"-no-ads"
                            if y_datapoint["no-ads"] != None:
                                aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint["no-ads"])
                                aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)
                        else:
                            series_label = cdf_key
                            aa.insertY_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, y_datapoint)
                            aa.insertX_Val(DICT_Y_VS_EXPLICITLY_BLOCKED, this_scatterPlot, series_label, x_datapoint)

        # FINISH LOOPING THROUGH SCATTER PLOTS
    # FINISH LOOPING THROUGH FILES

    # plot range CDFs
    for range_cdf in aa.DICT_RANGE_CDFS:
        i = 0
        csv_fname = os.path.join(csv_dir, "rng-"+range_cdf+".csv")
        f_csv = open(csv_fname, 'w')
        csv_writer = csv.writer(f_csv, delimiter=',')
        try:
            xlabel = aa.DICT_RANGE_CDFS[range_cdf]["x-label"]
        except KeyError:
            xlabel = None
        try:
            ylabel = aa.DICT_RANGE_CDFS[range_cdf]["y-label"]
        except:
            ylabel = None
        for cdf_key in aa.DICT_RANGE_CDFS[range_cdf]["raw_data"]:
            # get data out of dict
            fname_and_raw_data = aa.DICT_RANGE_CDFS[range_cdf]["raw_data"][cdf_key]
            fname_and_raw_data = sorted(fname_and_raw_data, key=lambda elem: elem[1])
            raw_data = [elem[1] for elem in fname_and_raw_data]
            fnames = [elem[0] for elem in fname_and_raw_data]
            # add data to plot cdf
            linedata = statsmodels.distributions.ECDF(raw_data)
            plt.plot(linedata.x, linedata.y, lw=3, label=cdf_key, c=colors[i%len(colors)])#S marker=markers[i%len(markers)])
            # add data to csv
            csv_writer.writerow([' ']+fnames)
            csv_writer.writerow([cdf_key]+raw_data)
            i+=1
        # plot cdf
        plt.legend(loc="lower right")
        axes = plt.gca()
        axes.set_xlim([0,100])
        axes.set_xlabel(xlabel)
        axes.set_ylabel(ylabel)
        fname = os.path.join(fig_dir, "rng-"+range_cdf+".pdf")
        #DICT_RANGE_CDFS[range_cdf]["range_cdf_fig"].savefig(fname, bbox_inches="tight")
        plt.savefig(fname, bbox_inches="tight")
        plt.close()
        # close csv
        f_csv.close()


    for cdf_name in aa.DICT_ORIG_CDFS:
        cdf = aa.DICT_ORIG_CDFS[cdf_name]["cdf"]
        #xlim = [-6,12]
        if useCategories:
            cdf.plot(plotdir=fig_dir, title="", legend="lower right", bbox_to_anchor=(1.05, 1), lw=1.5, numSymbols=3)#, xlim=xlim)#styles={'linewidth':0.5})
        else:
            cdf.plot(plotdir=fig_dir, title="", legend="lower right", lw=1.5, numSymbols=3)#, xlim=xlim)#styles={'linewidth':0.5}) bbox_to_anchor=(1.05, 1)
        f_csv = open(os.path.join(csv_dir, cdf.baseName+".csv"), 'w')
        f_csv.write("key,avg,0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100"+nl)
        for key in cdf._cdfs:
            #data = cdf._cdfs[key].getPdfData()[0]
            data = data_dict[cdf.baseName][key]
            f_csv.write(key+sep+str(numpy.average(data))+
                            sep+str(percentile(data,0))+
                            sep+str(percentile(data,5))+
                            sep+str(percentile(data,10))+
                            sep+str(percentile(data,15))+
                            sep+str(percentile(data,20))+
                            sep+str(percentile(data,25))+
                            sep+str(percentile(data,30))+
                            sep+str(percentile(data,35))+
                            sep+str(percentile(data,40))+
                            sep+str(percentile(data,45))+
                            sep+str(percentile(data, 50))+
                            sep+str(percentile(data,55))+
                            sep+str(percentile(data,60))+
                            sep+str(percentile(data,65))+
                            sep+str(percentile(data,70))+
                            sep+str(percentile(data, 75))+
                            sep+str(percentile(data, 80))+
                            sep+str(percentile(data,85))+
                            sep+str(percentile(data,90))+
                            sep+str(percentile(data,95))+
                            sep+str(percentile(data,100))+nl)
        f_csv.close()

        csv_fname = os.path.join(csv_dir, "orig-"+cdf_name+"-list.csv")
        f_csv = open(csv_fname, 'w')
        csv_writer = csv.writer(f_csv, delimiter=',')
        for cdf_key in aa.DICT_ORIG_CDFS[cdf_name]["raw_data"]:
            # get data out of dict
            fname_and_raw_data = aa.DICT_ORIG_CDFS[cdf_name]["raw_data"][cdf_key]
            fname_and_raw_data = sorted(fname_and_raw_data, key=lambda elem: elem[1])
            raw_data = [elem[1] for elem in fname_and_raw_data]
            fnames = [elem[0] for elem in fname_and_raw_data]
            # add data to csv
            csv_writer.writerow([' ']+fnames)
            csv_writer.writerow([cdf_key]+raw_data)
        f_csv.close()

    if doScatterPlots:
        xlabel = "Num objs directly blocked"
        for scatterPlot in aa.DICT_Y_VS_EXPLICITLY_BLOCKED:
            caption_x = 1.3
            caption_y = 0.5
            stats = ""
            print(scatterPlot)
            ylabel = aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["y-label"]
            file_flag = aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["file_flag"]
            x_vals = aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["x_vals"]
            y_vals = aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["y_vals"]
            # if scatterPlot == "Final-time_DOMContent":
            #     print(x_vals)
            #     print(y_vals)
            i = 0
            aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"] = {}
            for series_label in x_vals:
                aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i] = aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["scatter_plot_fig"].add_subplot(len(x_vals),1,i+1)
                x = x_vals[series_label]
                y = y_vals[series_label]
                aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i].scatter(x, y, label=series_label, c=colors[i%len(colors)], marker=markers[i%len(markers)])
                aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i].legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
                try:
                    slope, intercept, rvalue, pvalue, stderr = linregress(x, y)
                except:
                    print(x)
                    print(y)
                    print(len(x))
                    print(len(y))
                stats+=(series_label+": slope="+"{0:.1f}".format(slope)+" intrcpt="+"{0:.1f}".format(intercept)+" corr="+"{0:.3f}".format(rvalue)+nl+(4*tab)+
                            " p="+"{0:.3f}".format(pvalue)+" stderr="+"{0:.3f}".format(stderr)+nl+nl)
                i+=1
            aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i-1].set_xlabel(xlabel)
            aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["axis"][i-1].set_ylabel(ylabel)
            aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["scatter_plot_fig"].text(caption_x, caption_y, stats, verticalalignment="bottom")
            fname = os.path.join(fig_dir, "sct-"+scatterPlot+".pdf")
            aa.DICT_Y_VS_EXPLICITLY_BLOCKED[scatterPlot]["scatter_plot_fig"].savefig(fname, bbox_inches="tight")
        plt.close()

    # write the new exclude_list to file
    # but don't overwite if one was provided
    fname_mobile = "exclude_list_mobile"
    fname_desktop = "exclude_list_desktop"
    if excludeNoAds:
        fname_mobile += "_noads"
        fname_desktop += "_noads"
    if excludeTime:
        fname_mobile += "_time"
        fname_desktop += "_time"
    fname_mobile += ".json"
    fname_desktop += ".json"
    if args.exclude_list_mobile == None:
        new_exclude_mobile_path = os.path.join(list_out_dir, fname_mobile)
        with open(new_exclude_mobile_path, 'w') as f:
            json.dump(new_exclude_dict_mobile, f)
            
    if args.exclude_list_desktop == None:
        new_exclude_desktop_path = os.path.join(list_out_dir, fname_desktop)
        with open(new_exclude_desktop_path, 'w') as f:
            json.dump(new_exclude_dict_desktop, f)

    end_time = time.clock()
    elapsed_time = end_time - start_time
    print("Actual total time: "+str(elapsed_time))
