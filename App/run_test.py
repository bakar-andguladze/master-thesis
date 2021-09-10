import os
from mininet_topo import run_topo
from mininet.log import setLogLevel, info
from process_csv import get_results
import constants


def main():
    # setLogLevel('info')
    run_topo(constants.topo_size)
    get_results()

if __name__ == '__main__':
    # setLogLevel('info')
    for i in range(5):
        main()