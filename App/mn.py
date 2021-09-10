#!/usr/bin/python
from mininet.link import TCLink
from mininet.node import Node
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from prepare_test import generate_capacities
import constants
import os
import time
from subprocess import PIPE


dir_path = os.path.dirname(os.path.realpath(__file__))


def rp_disable(host):
    """
    Disable Reverse Path Filtering 
    """
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
    
    # add routers and top & bottom hosts
    for i in range(1, size+1):
        net.addHost('r{}'.format(i), cls=LinuxRouter, ip='10.0.{}.2'.format(i-1))
    for i in range(1, size+1):
        net.addHost('t{}'.format(i), ip='10.1.{}.20'.format(i))
    for i in range(1, size+1):
        net.addHost('b{}'.format(i), ip='10.2.{}.40'.format(i))    

    net.addLink(h1, net.get('r1'), cls=TCLink, intfName1='h1-eth0', intfName2='r1-eth0')
    
    for i in range(1, size):
        net.addLink(net.get('r{}'.format(i)), net.get('r{}'.format(i+1)), cls=TCLink, intfName1='r{}-eth1'.format(i), intfName2='r{}-eth0'.format(i+1))
    
    for i in range(1, size+1):
        net.addLink(net.get('t{}'.format(i)), net.get('r{}'.format(i)), cls=TCLink, intfName1='t{}-eth0'.format(i), intfName2='r{}-eth2'.format(i))
        net.addLink(net.get('b{}'.format(i)), net.get('r{}'.format(i)), cls=TCLink, intfName1='b{}-eth0'.format(i), intfName2='r{}-eth3'.format(i))
        

    net.addLink(net.get('r{}'.format(size)), h2, cls=TCLink, intfName1='r{}-eth1'.format(size), intfName2='h2-eth0')

    
    net.build()
    net.start()
    configure_net(net, size)

    CLI(net)
    
    net.stop()
    cleanup()

def configure_routers(net, size):
    # command to configure all Routes
    config_routes_right = "ip route add to 10.0.{}.0/24 via 10.0.{}.{}"
    config_routes_left = "ip route add to 10.0.{}.0/24 via 10.0.{}.{}"
    host_part_eth0 = 2
    host_part_eth1 = 1 

    for i in range(1, size+1):
        router = net.get('r{}'.format(i))
        # configure router interfaces
        router.cmd("ifconfig r{}-eth0 10.0.{}.2/24".format(i, i-1)) # left
        router.cmd("ifconfig r{}-eth1 10.0.{}.1/24".format(i, i))   # right
        router.cmd("ifconfig r{}-eth2 10.1.{}.3/24".format(i, i))   # north 
        router.cmd("ifconfig r{}-eth3 10.2.{}.4/24".format(i, i))   # south

        # to the right hosts
        for j in range(i+1, size+1):
            # right routers
            router.cmd(config_routes_right.format(j, i, host_part_eth0))
            # top and bottom hosts on the right
            router.cmd('ip route add to 10.1.{}.0/24 via 10.0.{}.2'.format(j, i))
            router.cmd('ip route add to 10.2.{}.0/24 via 10.0.{}.2'.format(j, i))
        
        # to the left hosts
        for j in range(0, i):
            # left routers
            router.cmd(config_routes_left.format(j, i-1, host_part_eth1))
            # top and bottom hosts on the left
            router.cmd('ip route add to 10.1.{}.0/24 via 10.0.{}.1'.format(j+1, i-1))
            router.cmd('ip route add to 10.2.{}.0/24 via 10.0.{}.1'.format(j+1, i-1))

def configure_cross_hosts(net, size):
    for i in range(1, size+1):
        topHost = net.get('t{}'.format(i))
        topHost.setIP('10.1.{}.20'.format(i), intf='t{}-eth0'.format(i))
        topHost.cmd("ifconfig t{}-eth0 10.1.{}.20/24".format(i, i))
        topHost.cmd('ip route add default via 10.1.{}.3'.format(i))

        bottomHost = net.get('b{}'.format(i))
        bottomHost.setIP('10.2.{}.40'.format(i), intf='b{}-eth0'.format(i))
        bottomHost.cmd("ifconfig b{}-eth0 10.2.{}.40/24".format(i, i))
        bottomHost.cmd('ip route add default via 10.2.{}.4'.format(i))

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
    configure_cross_hosts(net, size)

    h2 = net.get('h2')
    h2.setIP('10.0.{}.10'.format(size), intf='h2-eth0')
    h2.cmd("ifconfig h2-eth0 10.0.{}.10/24".format(size))
    h2.cmd("route add default gw 10.0.{}.1".format(size))

    capacities = generate_capacities(10, 100, size+1)
    print(capacities)
    set_capacities(net, size, capacities)

    # do I actually need this???
    # h1.cmd('tc qdisc replace dev leftHost-eth0 root fq pacing')
    # h1.cmd('ethtool -K leftHost-eth0 tso off')
    # h2.cmd('tc qdisc replace dev rightHost-eth0 root netem delay 50')


    # ############## save capacities to a file ############## #
    textfile = open(constants.topo_caps, "w")
    # textfile.write(capacities)
    for element in capacities:
        textfile.write(str(element) + "\n")
    textfile.close()
    # ####################################################### #

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
    # h1.cmd("tc qdisc add dev h1-eth0 root netem rate {}mbit".format(capacities[0]))
    # h2.cmd("tc qdisc add dev h2-eth0 root netem rate {}mbit".format(capacities[-1]))

    set_capacity = "tc qdisc add dev r{}-eth{} root handle 1: tbf latency 100ms buffer 2000b rate {}mbit"
    disable_icmp_ratemask = "sysctl -w net.ipv4.icmp_ratemask=0"
    # set_capacity = "tc qdisc add dev r{}-eth{} root tbf rate {}mbit latency 100ms buffer 16000b"
    for i in range(n_routers):
        # Apply traffic limiter at router i
        router = net.get("r{}".format(i+1))

        # limit eth0 and eth1 respectively
        router.cmd(disable_icmp_ratemask)
        router.cmd(set_capacity.format(i+1, 0, capacities[i]))
        router.cmd(set_capacity.format(i+1, 1, capacities[i + 1]))
        

def inject_and_capture(host):
    # tcpdump (maybe add timeout if necessary)
    # try:
    #     host.popen("timeout 5 tcpdump -n icmp -w results/icmp.pcap &", stdout=PIPE, stderr=PIPE)
    #     # host.cmd("tcpdump -n icmp -w results/icmp.pcap &")
    # except Exception as e:
    #     print('Error on starting tcpdump\n{}'.format(e))
    # finally:
    #     host.popen("./traffic_icmp", stdout=PIPE, stderr=PIPE)
    try:
        host.popen("tcpdump -n icmp -w results/icmp.pcap", stdout=PIPE, stderr=PIPE)
        print("{} started tcpdump".format(host))
    except Exception as e:
        print(e)
    
    try:
        host.popen("./traffic_icmp", stdout=PIPE, stderr=PIPE)
        print("started traffic")
    except Exception as e:
        print(e)
    finally:
        time.sleep(20)


if __name__ == '__main__':
    setLogLevel('info')
    build_topo(constants.topo_size)
