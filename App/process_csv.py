import os
import subprocess
import PPrate as pp
import numpy as np
import pandas as pd
import constants 

dir_path = os.path.dirname(os.path.realpath(__file__))

def pcap_to_csv():
    command = "tshark -r results/icmp.pcap -T fields -E header=y -E separator=, -E quote=d -E occurrence=f -e frame.time_epoch -e ip.src -e ip.dst -e ip.len > results/icmp.csv"
    os.system(command)

def read_from_csv(file_path):
    """
    Reads from csv file and returns a Pandas DataFrame object with full data 
    """
    data = pd.read_csv(file_path, sep=',')
    data.columns = ['ts', 'src', 'dst', 'ip_len']

    return data

def group_by_routers(data, streams):
    # streams = {}
    for tpl in data.itertuples():
        if tpl != None:
            key = (tpl.src, tpl.dst)
        
            if pd.isna(tpl.src) or pd.isna(tpl.dst):
                continue

            # Create new dict entry for new flows
            if key not in streams:
                streams[key] = [[], []]

            # Append timestamp, IP size and TCP length to flow
            streams[key][0].append(tpl.ts)
            streams[key][1].append(tpl.ip_len)

def tmp():
    pcap_to_csv()
    filepath = dir_path + "/results/icmp.csv"
    streams = {}

    df = read_from_csv(filepath)
    
    group_by_routers(df, streams)
    # for i in streams ... calculate iats
    # print("iats lists ========================================")
    for key in streams:
        streams[key][0] = calculate_iats(streams[key][0])
        # streams[key][0] = remove_intervals(streams[key][0])
        # print(streams[key][0])
        cap = pp.find_capacity(576, streams[key][0])
        cap = bit_to_mbit(cap)
        print(cap)
    # print(streams)


def calculate_iats(timestamps):
    """
    Calculates inter-arrival times for packet pairs
    """
    iats = []
    for i, ts in enumerate(timestamps):
        if(i == 0):
            # iats.append(0)
            continue
        iat = ts - timestamps[i-1]
        if(iat > 0 and iat < 1.0):
            iats.append(iat)
    # print(iats)
    return iats

def remove_intervals(iats):
    for i in iats:
        if (i >= 1.0):
            iats.remove(i)
    print(len(iats))
    print("======================================================================================================")

    return iats

def calculate_capacity_for_hop(hop):
    """
    Calculates capacity to a certain router
    """
    pass
    # after I have sizes & timestamps I can pass them to pprate and results for deadline are done!


def bit_to_mbit(bits):
    return bits / 1000000


if __name__ == '__main__':
    tmp()