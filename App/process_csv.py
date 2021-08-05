import os
import subprocess
import PPrate as pp
import numpy as np
import pandas as pd

def convert_pcap(folder, filename):
    """
    Convert pcap trace files into csv files
    :param folder: Folder the pcap file is located in. Use "." for the current directory.
    :param filename: File name of the trace file to be read and output to be written
    """
    with open("{}/{}.csv".format(folder, filename.replace('.pcap', '')), "w") as output:
        FNULL = open(os.devnull, 'w')
        # Convert pcap file using tshark
        # Format: Timestamp, Src IP, Dst IP, IP packet length, TCP segment length, ACK Flag

        # try this with your format..
        tshark = subprocess.call([
            "tshark", "-r", filename, "-l", "-T", "fields", "-E", "separator=;", "-e", "frame.time_epoch", "-e",
            "ip.src",
            "-e", "ip.dst", "-e", "ip.len", "-e", "tcp.len", "-e", "tcp.flags.ack"], stdout=output, stderr=FNULL)

def read_csv(folder, filename):
    pass
    # this function is #1 priority

def calculate_capacities():
    pass
    # after I have sizes & timestamps I can pass them to pprate and results for deadline are done!

def get_capacity():
    pass
    # calls sender algorithm

def sender_algorithm():
    pass

def get_results():
    pass

def save_results_to_file():
    pass

def get_relative_error():
    pass

