import os
from mininet_topo import build_topo
from mininet.log import setLogLevel, info
import constants


def main():
    setLogLevel('info')
    build_topo(constants.topo_size)

    os.system("tshark -r results/tcp.pcap -T fields -E header=y -E separator=, -E quote=d -E occurrence=f -e frame.time_epoch -e ip.src -e ip.dst -e ip.len -e tcp.len -e tcp.flags.ack> results/tcp.csv")
    
if __name__ == '__main__':
    # setLogLevel('info')
    main()