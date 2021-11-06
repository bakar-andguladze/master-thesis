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


def print_standard_deviation(z):
    standard_deviation = np.std(z)
    print("Standard deviation: {}". format(standard_deviation))

def print_average(z):
    avg = np.average(z)
    print("Average: {}".format(avg))

def print_error_range(z):
    mn = min(z)
    mx = max(z)
    print("min error = {}".format(mn))
    print("max error = {}".format(mx))

def print_details(z):
    print_standard_deviation(z)
    print_average(z)
    print_error_range(z)

# ==================== Plot Methods ===================== #

def plot_values(x, y):
    ax = ns.lineplot(x, x, label = "Expected Capacity", marker="o")
    ns.lineplot(x, y, label = "Estimated Capacity", marker="o")

    ax.set_xlabel('Expected Capacity (Mbit/s)',fontsize=20)
    ax.set_ylabel('Estimated Capacity (Mbit/s)',fontsize=20)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid()
    plt.show()

def plot_error_rate(x, z):
    ax2 = ns.lineplot(x, z, label="Relative Error Rate (%)", marker="o")
    ax2.set_xlabel('Expected Capacity (Mbit/s)',fontsize=20)
    ax2.set_ylabel('Relative Error Rate (%)',fontsize=20)

    ceiling = max(z) + 1
    floor = min(z) - 2 if min(z) - 2 > 0 else 0

    plt.ylim(floor, ceiling)
    plt.legend(fontsize='x-large', title_fontsize='200')
    plt.grid()
    plt.show()

def plot_multiple_error():
    df_list = read_args()
    xx = list()
    zz = list()
    
    sizes = [100, 500, 1000, 1400]

    for i in range(len(df_list)):
        xx.append(df_list[i]['expected'])
        zz.append(df_list[i]['error'])
   

    for i in range(len(zz)):
        ax2 = ns.lineplot(xx[i], zz[i], label="RE(%) - Packet size: {}bytes".format(sizes[i]), marker="o")
        # plt.plot(xx[i], zz[i])
    ax2.set_xlabel('Expected Capacity (Mbit/s)',fontsize=20)
    ax2.set_ylabel('Relative Error Rate (%)',fontsize=20)

    # ceiling = max(z) + 1
    # floor = min(z) - 2 if min(z) - 2 > 0 else 0

    # plt.ylim(floor, ceiling)
    plt.legend(fontsize='x-large', title_fontsize='200')
    plt.grid()
    plt.show()

def plot_multiple_lines():
    df_list = read_args()
    
    sizes = [100, 500, 1000, 1400]

    x = df_list[0]['expected'].tolist()

    x_list = list()
    y_list = list()
    for i in range(len(df_list)):
        x_list.append(df_list[i]['expected'].tolist())
        y_list.append(df_list[i]['estimated'].tolist())

    ax = ns.lineplot(x, x, label = "Expected Capacity", marker="o")
    for i in range(len(y_list)):
        ns.lineplot(x_list[i], y_list[i], label = "Estimated Capacity; Packet size: {} bytes".format(sizes[i]), marker="o")

    ax.set_xlabel('Expected Capacity (Mbit/s)',fontsize=20)
    ax.set_ylabel('Estimated Capacity (Mbit/s)',fontsize=20)
    plt.gca().set_aspect('equal', adjustable='box')
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
packet_sizes = [100, 500, 1000, 1200, 1400]

if len(sys.argv) > 2:
    plot_multiple_lines()
    plot_multiple_error()
else:
    run()

