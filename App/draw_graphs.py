import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as ns
import numpy as np
from numpy.core.fromnumeric import sort

arg_list = list()
filename = sys.argv[1]
# ==================== Helper methods ==================== #
def read_from_csv(file_path):
    """
    Reads from csv file and returns a Pandas DataFrame object with full data 
    """
    data = pd.read_csv(file_path, sep=';')
    data.columns = ['path', 'estimated', 'expected', 'error']
    
    return data

def read_args():
    df_list = list()
    for i in range(1, len(sys.argv)):
        df = read_from_csv(sys.argv[i])
        df_list.append(df)

    return df_list


def get_standard_deviation(z):
    standard_deviation = np.std(z)
    print("Standard deviation: {}". format(standard_deviation))
    return standard_deviation

def get_average(z):
    avg = np.average(z)
    print("Average: {}".format(avg))
    return avg

def get_error_range(z):
    mn = min(z)
    mx = max(z)
    error_range = [mn, mx]
    print("min error = {}".format(mn))
    print("max error = {}".format(mx))
    return error_range

def print_details(z):
    average = get_average(z)
    standard_deviation = get_standard_deviation(z)
    error_range =  get_error_range(z)

    err_mn = error_range[0]
    err_mx = error_range[1]

    average = str(round(average, 2))
    standard_deviation = str(round(standard_deviation, 2))
    err_mn = str(round(err_mn, 2))
    err_mx = str(round(err_mx, 2))

    for_latex_table = "& {}\% & {}\% & {}\% & {}\% \\\\".format(average, standard_deviation, err_mn, err_mx)
    print(for_latex_table)

# ==================== Plot Methods ===================== #

def plot_values(x, y):
    ax = ns.lineplot(x, x, label = "Expected Capacity", marker="o")
    ns.lineplot(x, y, label = "Estimated Capacity", marker="o")

    ax.set_xlabel('Expected Capacity (Mbit/s)',fontsize=20)
    ax.set_ylabel('Estimated Capacity (Mbit/s)',fontsize=20)
    plt.gca().set_aspect('equal', adjustable='box')
    
    plt.legend(fontsize='20', title_fontsize='200')
    plt.grid()
    plt.show()

def plot_error_rate(x, z):
    ax2 = ns.lineplot(x, z, label="Relative Error Rate (%)", marker="o")
    ax2.set_xlabel('Expected Capacity (Mbit/s)', fontsize=20)
    ax2.set_ylabel('Relative Error Rate (%)', fontsize=20)

    ceiling = max(z) + 1
    floor = min(z) - 2 if min(z) - 2 > 0 else 0
    # floor = 2
    # ceiling = 4

    # ns.set_xticks([range(5)])
    plt.ylim(floor, ceiling)
    plt.legend(fontsize='20', title_fontsize='200')
    # plt.gca().set_aspect('equal', adjustable='box')
    ax2.set_box_aspect(1)

    plt.grid()
    plt.show()

def plot_multiple_error(legend, legendvalues):
    df_list = read_args()
    xx = list()
    zz = list()
    
    sizes = [3, 8, 20, 32, 63]

    for i in range(len(df_list)):
        xx.append(df_list[i]['expected'])
        zz.append(df_list[i]['error'])
   

    for i in range(len(zz)):
        ax2 = ns.lineplot(xx[i], zz[i], label=legend.format(legendvalues[i]), marker="o")
        
    ax2.set_xlabel('Expected Capacity (Mbit/s)',fontsize=20)
    ax2.set_ylabel('Relative Error Rate (%)',fontsize=20)

    # ceiling = max(z) + 1
    # floor = min(z) - 2 if min(z) - 2 > 0 else 0

    # plt.ylim(floor, ceiling)
    plt.legend(fontsize='20', title_fontsize='200')
    ax2.set_box_aspect(1)
    plt.grid()
    plt.show()

def plot_multiple_lines(legend, legendvalues):
    df_list = read_args()
    
    sizes = [3, 8, 20, 32, 63]

    x = df_list[0]['expected'].tolist()

    x_list = list()
    y_list = list()
    for i in range(len(df_list)):
        x_list.append(df_list[i]['expected'].tolist())
        y_list.append(df_list[i]['estimated'].tolist())

    for i in range(len(y_list)):
        ns.lineplot(x_list[i], y_list[i], label = legend.format(legendvalues[i]), marker="o")
    ax = ns.lineplot(x, x, label = "Expected Capacity", marker="o")

    ax.set_xlabel('Expected Capacity (Mbit/s)',fontsize=20)
    ax.set_ylabel('Estimated Capacity (Mbit/s)',fontsize=20)
    plt.gca().set_aspect('equal', adjustable='box')
    
    plt.legend(fontsize='15', title_fontsize='200')
    plt.grid()
    plt.show()

def run():
    filename = sys.argv[1]
    df = read_from_csv(filename)
    x = df['expected'].tolist()
    y = df['estimated'].tolist()
    z = df['error'].tolist()

    print_details(z)

    plot_values(x, y)
    plot_error_rate(x, z)


# ======================== Run ========================== #
# Packet Size
legendvalues = [100, 500, 1000, 1200, 1500]
plot_legend = "Estimated Capacity; Packet Size: {} bytes"
err_legend = "RE(%); Packet Size: {} bytes"

# Path Length
# plot_legend = "Estimated Capacity; Path Length: {}"
# err_legend = "RE(%); Path Length: {}"
# legendvalues = [1, 3, 8, 20, 32, 63]

# Train Length
# plot_legend = "Estimated Capacity; Train Length: {}"
# err_legend = "RE(%); Train Length: {}"
# legendvalues = [7, 11, 20, 50, 100, 250]


# ICMP_Ratelimit
# legendvalues = [1, 5, 10, 100]
# plot_legend = "Estimated Capacity; icmp_ratelimit={}"
# err_legend = "RE(%); icmp_ratelimit={}"


if len(sys.argv) > 2:
    plot_multiple_lines(plot_legend, legendvalues)
    plot_multiple_error(err_legend, legendvalues)
else:
    run()

