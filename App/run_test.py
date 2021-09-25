import os
import argparse
import prepare_test
from mininet_topo import run_topo
from mininet.log import setLogLevel, info
from process_icmp_csv import get_results
from process_tcp_csv import get_network_capacity


def main():
    # Argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to the config file')
    args = parser.parse_args()

    test_parameters = prepare_test.get_config_parameters(args)
    
    # print(test_parameters)

    run_topo(**test_parameters)
    get_results()
    get_network_capacity(test_parameters['topo_size'])

if __name__ == '__main__':
    # setLogLevel('info')
    main()