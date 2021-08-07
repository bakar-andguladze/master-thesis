from datetime import time
import pandas as pd
import os 
import numpy as np
import PPrate as pp

np.set_printoptions(precision=9)

dir_path = os.path.dirname(os.path.realpath(__file__))

def pcap_to_csv(folder, filename):
    filepath = folder + '/' + filename
    command = "tshark -r {}.pcap -T fields -E header=y -E separator=, -E quote=d -E occurrence=f -e frame.time_epoch -e ip.src -e ip.dst -e ip.len > {}.csv"
    os.system(command.format(filepath, filepath))

def read_from_csv(file_path):
    # read_csv() returns DataFrame object
    data = pd.read_csv(file_path, sep=',')
    data.columns = ['ts', 'router', 'src', 'ip_len']

    return data

def get_timestamps(data):
    # read timestamps from data
    timestamps = data['ts'].tolist()
    return timestamps

def subtract_sleep_time(timestamps):
    new_timestamps = []
    seconds = 1.0
    for ts in timestamps:
        new_ts = float(ts) - float(seconds)
        new_timestamps.append(new_ts)
        seconds += 1.0
    return new_timestamps

def calculate_iats(timestamps):
    iats = []
    for i, ts in enumerate(timestamps):
        if(i == 0):
            iats.append(0)
        else:
            ts = ('%.9f'%ts)
            ts2 = ('%.9f'%timestamps[i-1])
            # iats.append(float(ts) - float(timestamps[i-1]))
            iats.append(float(ts) - float(ts2))
        
        print("{}: {}".format(i+1, ts))
    # print(timestamps)
    return iats

def tmp2(filepath=dir_path + "/results/tcp.csv"):
    data = read_from_csv(filepath)
    acks = data.filter(like="ack")
    print(acks)

def tmp(filepath=dir_path + "/results/mininet.csv"):
    data = read_from_csv(filepath)
    timestamps = get_timestamps(data)
    timestamps = subtract_sleep_time(timestamps)
    size = 311 #283

    # print(data.ts[10])
    # timestamps = ["1627504023.251466000", "1627504023.251611000", "1627504023.251628000", "1627504023.251639000", "1627504023.251649000", "1627504023.251659000"]
    iats = calculate_iats(timestamps)
    capacity = pp.find_capacity(size, iats)
    print(capacity)
    # print(timestamps)

def calculate_capacity(data, flows, sender_ip, receiver_ip, size=311, sampling_factor=1):
    """
    Calculates capacity of one hop based on timestamps from the source to one router
    """
    # size is 1514 by default
    # data.columns = ['ts', 'router', 'src', 'ip_len']
    timestamps = []
    ips = []
    # Iterate through segments
    for tpl in data.itertuples():
        # if tpl.data != 0:
        # Address flow via IP address
        key = (tpl.router, tpl.src)

        if pd.isna(tpl.router) or pd.isna(tpl.src):
            continue

        # Create new dict entry for new flows
        if key not in flows:
            flows[key] = [[], []]

        # Append timestamp, IP size and TCP length to flow
        if(tpl.router == sender_ip):
            timestamps.append(tpl.ts)
            ips.append(tpl.ip_len)
        # flows[key][0] = tpl.ts
        # flows[key][1] = tpl.ip_len

    # Calculate Inter-Arrival-Times
    f = flows[(sender_ip, receiver_ip)]


    # iats = calculate_iats(f[0])
    iats = calculate_iats(timestamps)

    f[0] = np.array(iats)
    # Apply sampling if necessary
    iats = f[0][::sampling_factor]
    return pp.find_capacity(size, iats)

def get_all_capacities(filepath=dir_path + "/results/mininet.csv"):
    """
    Calculates capacities of all hops. runs calculate_capacity for each router 
    currently it's a mess but it's fixable
    possibly have to rewrite the whole thing
    """
    data = read_from_csv(filepath)
    flows = {}
    keys = []
    for tup in data.itertuples():
        # Address flow via IP address
        key = (tup.router, tup.src)
        keys.append(key)

    keys = list(set(keys))

    # capacities = []
    # for (a, b) in keys:
    #     cap = calculate_capacity(data, flows, a, b)
    #     capacities.append(cap)
    # print(capacities)

    a = "10.0.5.2"
    b = "10.0.0.10"
    cap = calculate_capacity(data, flows, a, b)
    print(cap)








if __name__ == '__main__':
    tmp2()

