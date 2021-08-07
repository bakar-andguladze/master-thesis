import os
import subprocess
import PPrate as pp
import numpy as np
import pandas as pd

def read_from_csv(file_path):
    # read_csv() returns DataFrame object
    data = pd.read_csv(file_path, sep=',')
    data.columns = ['ts', 'router', 'src', 'ip_len', 'ack']
    
    flows = {}

    return data

def receiver_algo(data, flows, sender_ip="10.0.0.10", receiver_ip="10.0.3.10", size=66, sampling_factor=1):
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
        if p.data != 0:
            # Address flow via IP address
            key = (p.src, p.dst)

            if pd.isna(p.src) or pd.isna(p.dst):
                continue

            # Create new dict entry for new flows
            if key not in flows:
                flows[key] = [[], [], [], []]

            # Append timestamp, IP size and TCP length to flow
            flows[key][0].append(p.ts)
            flows[key][1].append(p.size)
            flows[key][2].append(p.data)

            # Append ACK flag status
            if pd.isna(p.ack):
                flows[key][3].append(False)
            else:
                flows[key][3].append(True)

    # Calculate Inter-Arrival-Times
    iats = []
    f = flows[(sender_ip, receiver_ip)]
    for i, ts in enumerate(f[0]):
        if i == 0:
            iats.append(0)
        else:
            iats.append(ts - f[0][i - 1])

    f[0] = np.array(iats)
    # Apply sampling if necessary
    iats = f[0][::sampling_factor]
    return pp.find_capacity(size, iats)




if __name__ == '__main__':
    tmp()
