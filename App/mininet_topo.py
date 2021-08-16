#!/usr/bin/python
from mininet.link import TCLink
from mininet.node import Node
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from prepare_test import generate_capacities
import constants
# ///////////////////////////////////////////////////////////// #

def rp_disable(host):
    ifaces = host.cmd('ls /proc/sys/net/ipv4/conf')
    ifacelist = ifaces.split()    # default is to split on whitespace
    for iface in ifacelist:
       if iface != 'lo': host.cmd('sysctl net.ipv4.conf.' + iface + '.rp_filter=0')

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    # pylint: disable=arguments-differ
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

def build_topo(size=1):
    net = Mininet()
    h1 = net.addHost('h1', ip='10.0.0.10')
    h2 = net.addHost('h2', ip='10.0.{}.10'.format(size))
    
    
    for i in range(1, size+1):
        net.addHost('r{}'.format(i), cls=LinuxRouter, ip='10.0.{}.2'.format(i-1))
        # print('r{}'.format(i), '10.0.{}.2'.format(i-1))
    

    net.addLink(h1, net.get('r1'), cls=TCLink, intfName1='h1-eth0', intfName2='r1-eth0')
    
    for i in range(1, size):
        net.addLink(net.get('r{}'.format(i)), net.get('r{}'.format(i+1)), cls=TCLink, intfName1='r{}-eth1'.format(i), intfName2='r{}-eth0'.format(i+1))
        # print('r{}'.format(i), 'r{}'.format(i+1), 'r{}-eth1'.format(i), 'r{}-eth0'.format(i+1))
    
    net.addLink(net.get('r{}'.format(size)), h2, cls=TCLink, intfName1='r{}-eth1'.format(size), intfName2='h2-eth0')

    # print(type(net.get('r{}'.format(size))))
    
    net.build()
    net.start()
    configure_net(net, size)
    CLI(net)
    
    # inject_and_capture(h1)
    net.stop()
    

def configure_routers(net, size):
    # command to configure all Routes
    config_routes_right = "ip route add to 10.0.{}.0/24 via 10.0.{}.{}"
    config_routes_left = "ip route add to 10.0.{}.0/24 via 10.0.{}.{}"
    host_part_eth0 = 2
    host_part_eth1 = 1 

    for i in range(1, size+1):
        router = net.get('r{}'.format(i))
        router.cmd("ifconfig r{}-eth0 10.0.{}.2/24".format(i, i-1))
        router.cmd("ifconfig r{}-eth1 10.0.{}.1/24".format(i, i))

        # to the right routers
        for j in range(i+1, size+1):
            router.cmd(config_routes_right.format(j, i, host_part_eth0))
        
        # to the left host
        for j in range(0, i):
            router.cmd(config_routes_left.format(j, i-1, host_part_eth1))

def configure_net(net, size):
    """
    Configure mininet network
    :param net: network object
    :param size: number of routers
    """
    h1 = net.get('h1')
    h1.setIP('10.0.0.10', intf='h1-eth0')
    h1.cmd("ifconfig h1-eth0 10.0.0.10/24")
    h1.cmd("route add default gw 10.0.0.2 dev h1-eth0")

    configure_routers(net, size)

    h2 = net.get('h2')
    h2.setIP('10.0.{}.10'.format(size), intf='h2-eth0')
    h2.cmd("ifconfig h2-eth0 10.0.{}.10/24".format(size))
    h2.cmd("route add default gw 10.0.{}.1".format(size))

    capacities = generate_capacities(10, 100, size+1)
    set_capacities(net, size, capacities)

    # ################## temporary ###################
    textfile = open(constants.topo_caps, "w")
    for element in capacities:
        textfile.write(str(element) + "\n")
    textfile.close()
    # ################################################

def set_capacities(net, n_routers, capacities):
    """
    Set link capacities by applying traffic limiters throughout the path
    :param n_routers: Amount of routers on the path
    :param capacities: list of link capacities
    :param net: Mininet network object
    """
    # Get left and rigth Host
    h1 = net.get("h1")
    h2 = net.get("h2")

    # Apply traffic limiters to first and last link
    h1.cmd("tc qdisc add dev h1-eth0 root handle 1: tbf latency 100ms buffer 2000b rate {}mbit".format(capacities[0]))
    h2.cmd("tc qdisc add dev h2-eth0 root handle 1: tbf latency 100ms buffer 2000b rate {}mbit".format(capacities[-1]))

    # tc qdisc add dev h1-eth0 root netem rate {}mbit
    # h1.cmd("tc qdisc add dev h1-eth0 root netem pfifo rate {}mbit".format(capacities[0]))
    # h2.cmd("tc qdisc add dev h2-eth0 root netem pfifo rate {}mbit".format(capacities[-1]))
    
    # h1.cmd("tc qdisc pfifo")
    # h2.cmd("tc qdisc pfifo")

    set_capacity = "tc qdisc add dev r{}-eth{} root handle 1: tbf latency 100ms buffer 2000b rate {}mbit"
    # set_capacity = "tc qdisc add dev r{}-eth{} root tbf pfifo rate {}mbit latency 100ms buffer 16000b"
    for i in range(1, n_routers):
        # Apply traffic limiter at router i
        router = net.get("r{}".format(i))

        # limit left interface capacity
        router.cmd(set_capacity.format(i, 0, capacities[i]))
        # limit right interface capacity
        router.cmd(set_capacity.format(i, 1, capacities[i + 1]))

        # router.cmd("tc qdisc pfifo")


def inject_and_capture(host):
    # tcpdump (maybe add timeout if necessary)
    host.cmd("tcpdump -n tcp -w results/tcp.pcap &")
    host.cmd("tcpdump -n icmp -w results/icmp.pcap &")

    host.cmd("./TrafficGenerator")
    

# build_topo will be called from launcher.py. this is just for testing
if __name__ == '__main__':
    setLogLevel('info')
    build_topo(constants.topo_size)
