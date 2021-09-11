import os
from mininet_topo import run_topo
from mininet.log import setLogLevel, info
from process_csv import get_results
from tcp_csv import get_network_capacity
import constants


def main():
    # setLogLevel('info')
    run_topo(constants.topo_size)
    get_results()
    get_network_capacity()

if __name__ == '__main__':
    # setLogLevel('info')
    main()