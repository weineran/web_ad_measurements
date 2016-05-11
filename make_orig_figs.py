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

doScatterPlots = True
useCategories = True
orig_cdf_method = "diff_of_mins"
fig_subdir = "figs-5-11-cat-exclude/orig"
csv_subdir = "CSVs-5-11-cat-exclude/orig"
# fig_dir = os.path.join(data_dir, "figs-exclude-volatile-no-cat/orig")
# csv_dir = os.path.join(data_dir, "CSVs-exclude-volatile-no-cat/orig")
# fig_dir = os.path.join(data_dir, "figs-test/orig")
# csv_dir = os.path.join(data_dir, "CSVs-test/orig")

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
    return parser.parse_args()

if __name__ == "__main__":
    # Get arguments
    start_time = time.clock()
    args = parse_args()
    data_dir = args.data_dir
    rank_cutoff = args.rank_cutoff

    # prep directories
    fig_dir = os.path.join(data_dir, fig_subdir)
    csv_dir = os.path.join(data_dir, csv_subdir)
    summaries_dir = os.path.join(data_dir, "summaries")
    summaries_file_list = os.listdir(summaries_dir)

    if not os.path.isdir(fig_dir):

        os.mkdir(fig_dir)

    aa = AdAnalysis(summaries_file_list)
    csv_files = os.listdir(csv_dir)

    #for csv_file in csv_files:
    for orig_file in aa.DICT_ORIG_CDFS:
        csv_file = "orig-"+orig_file+"-list.csv"
        if csv_file[0] == '.':
            continue
        f_csv = open(os.path.join(csv_dir, csv_file), 'r')
        csv_reader = csv.reader(f_csv, delimiter=',')
        bar_plot = plt.figure(1, figsize=(8,3))
        cdf_plot = plt.figure(2, figsize=(4,3))
        box_plot = plt.figure(3, figsize=(8,3))
        i = 0
        means = []
        yerrs = []
        labels = []
        boxdata = []
        for row in csv_reader:
            if i%2 == 0:
                hostnames = row[1:]
            elif i%2 == 1:
                datapoints = row
                label = datapoints[0].split(' ')[0]
                datapoints = [float(y) for y in datapoints[1:]]
                boxdata.append(datapoints)
                avg = numpy.average(datapoints)
                means.append(avg)
                stdev = numpy.std(datapoints)
                yerrs.append(stdev)
                labels.append(label)

                linedata = statsmodels.distributions.ECDF(datapoints)
                #cdf_plot.plot(linedata.x, linedata.y, label=label, c=colors[i%len(colors)])#S marker=markers[i%len(markers)])
            i+=1
        f_csv.close()

        plt.figure(1)   # switch to bar plot
        fig, ax = plt.subplots()
        bar_locs = numpy.arange(len(means))
        width = 0.35
        bars = ax.bar(bar_locs, means, width, color='r', yerr=yerrs)
        ax.set_xticks(bar_locs + width)
        ax.set_xticklabels(labels, rotation="vertical")
        bar_fname = csv_file[:-4]+"-bar.pdf"
        bar_path = os.path.join(fig_dir, bar_fname)
        plt.savefig(bar_path, bbox_inches="tight")

        plt.figure(2)   # switch to cdf
        cdf_fname = csv_file[:-4]+"-cdf.pdf"
        cdf_path = os.path.join(fig_dir, cdf_fname)
        plt.savefig(cdf_path, bbox_inches="tight")
        plt.close()

        plt.figure(3)   # switch to box
        fig, ax = plt.subplots(figsize=(12,4.5))
        bp = ax.boxplot(boxdata, whis=0, showfliers=False)
        try:
            ylabel = aa.DICT_ORIG_CDFS[orig_file]["box_ylabel"]
        except KeyError:
            ylabel = None
        ax.set_ylabel(ylabel)
        ax.set_xticklabels(labels, rotation="vertical")
        box_fname = csv_file[:-4]+"-box.pdf"
        box_path = os.path.join(fig_dir, box_fname)
        plt.savefig(box_path, bbox_inches="tight")
        plt.close()
        


    end_time = time.clock()
    elapsed_time = end_time - start_time
    print("Actual total time: "+str(elapsed_time))
