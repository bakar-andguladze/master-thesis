import os
import sys
import argparse
import prepare_test
from mininet_topo import run_topo
from mininet.log import setLogLevel, info
from process_icmp_csv import get_results
from process_tcp_csv import get_network_capacity

def run(**test_parameters):
    run_topo(**test_parameters)
    get_results()
    total_capacity = get_network_capacity(test_parameters['topo_size'])
    print("end-to-end capacity = {}mbps".format(total_capacity))

def analyze_packet_loss(**test_parameters):
    total_packects = test_parameters['topo_size']*test_parameters['packets_per_hop']
    captured_packets = open("results/icmp.csv")
    lines = captured_packets.readlines()
    captured_packets_count = len(lines) - 1
    packet_loss_details = "{}/{} packets captured at the source host\n".format(captured_packets_count, total_packects)
    
    print(packet_loss_details)

def main():
    # Argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to the config file')
    args = parser.parse_args()

    test_parameters = prepare_test.get_config_parameters(args)
    
    # print(test_parameters)
    
    repeat_test = test_parameters['repeat_test']
    for i in range(repeat_test):
        try:
            run(**test_parameters)
            analyze_packet_loss(**test_parameters)
        except BaseException as e:
            print("error occured...\n")
            print(e)
            continue


if __name__ == '__main__':
    # setLogLevel('info')
    main()