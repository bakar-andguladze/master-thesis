import os
import subprocess
import PPrate as pp
import numpy as np
import pandas as pd

dir_path = os.path.dirname(os.path.realpath(__file__))

def read_from_csv(file_path):
    # read_csv() returns DataFrame object
    data = pd.read_csv(file_path, sep=',')
    data.columns = ['ts', 'src', 'dst', 'ip_len', 'tcp_len', 'ack']
    
    return data

def receiver_algo(data, flows, sender_ip="10.0.0.10", receiver_ip="10.0.3.10", size=40):
    """
    Process data using the receiver algorithm and derive capacity using PPrate algorithm
    :param data: Pandas dataframe containing packet traces
    :param flows: dict containing all flows
    :param sender_ip: IP address of the sender host
    :param receiver_ip: IP address of the receiver host
    :param size: Packet size to be used for the PPrate algorithm.
        Default value is the Ethernet frame size of 1514 Bytes which includes a MSS of 1460 Bytes.
    :param sampling_factor: Define sampling factor. 1 = Sampling disabled
    :return: Capacity Estimate in bit/s
    """
    # Iterate through segments
    for p in data.itertuples():
        # Only inspect data segments
        if p != None:
            # Address flow via IP address
            key = (p.src, p.dst)

            if pd.isna(p.src) or pd.isna(p.dst):
                continue

            if (p.ack == 1):
                continue

            # Create new dict entry for new flows
            if key not in flows:
                flows[key] = [[], [], []]

            # Append timestamp, IP size and TCP length to flow
            flows[key][0].append(p.ts)
            flows[key][1].append(p.ip_len)
            flows[key][2].append(p.tcp_len)

            # Append ACK flag status
            if pd.isna(p.ack):
                flows[key][2].append(False)
            else:
                flows[key][2].append(True)

    # Calculate Inter-Arrival-Times
    iats = []
    # sender_ip = "10.0.3.10"
    f = flows[(sender_ip, receiver_ip)]
    for i, ts in enumerate(f[0]):
        if i == 0:
            iats.append(0)
        else:
            iats.append((ts - f[0][i - 1])/2)

        # print(iats)

    f[0] = np.array(iats)
    # Apply sampling if necessary
    # print(iats)
    return bit_to_mbit(pp.find_capacity(size, iats))

def tmp():
    filepath = dir_path + '/results/h2.csv'
    flows = {}
    data = read_from_csv(filepath)
    cap = receiver_algo(data, flows)
    print(cap)

def bit_to_mbit(bits):
    return bits / 1000000

if __name__ == '__main__':
    tmp()

