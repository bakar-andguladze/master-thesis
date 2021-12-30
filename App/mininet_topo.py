#!/usr/bin/python
import os
import time
from mininet.link import TCLink
from mininet.node import Node
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.clean import cleanup
from prepare_test import generate_capacities
from subprocess import PIPE, STDOUT
from prepare_test import set_packet_size
from process_icmp_csv import get_assigned_capacities

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
    """
    A Node with IP forwarding enabled.
    """
    # pylint: disable=arguments-differ
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

# ================= Build and configure ================= #
def build_topo(size=1):
    """
    Build mininet network with left and right hosts, routers between them and top and bottom hosts 
    :param size: number of routers between left and right hosts (and number of top and bottom hosts too)
    """
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

    return net

def configure_routers(net, **test_parameters):
    """
    configures all the routers in the network
    :param net: network instance
    :param test_parameters: test parameters passed via .json file
    """
    # test parameters
    size = test_parameters['topo_size']
    icmp_ratelimit = test_parameters['icmp_ratelimit']
    packet_loss = test_parameters['packet_loss']
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

        configure_icmp_ratelimit(router, icmp_ratelimit)
        if(packet_loss > 0):
            apply_packet_loss(router, packet_loss)

def configure_cross_hosts(net, size):
    """
    Configure the connection between top and bottom hosts. 
    Each T{i} communicates with B{i+1} and T{last} with B{1}
    :param net: network instance
    :param size: network size
    """
    for i in range(1, size+1):
        topHost = net.get('t{}'.format(i))
        topHost.setIP('10.1.{}.20'.format(i), intf='t{}-eth0'.format(i))
        topHost.cmd("ifconfig t{}-eth0 10.1.{}.20/24".format(i, i))
        topHost.cmd('ip route add default via 10.1.{}.3'.format(i))

        bottomHost = net.get('b{}'.format(i))
        bottomHost.setIP('10.2.{}.40'.format(i), intf='b{}-eth0'.format(i))
        bottomHost.cmd("ifconfig b{}-eth0 10.2.{}.40/24".format(i, i))
        bottomHost.cmd('ip route add default via 10.2.{}.4'.format(i))

def configure_net(net, size, **test_parameters):
    """
    Configure mininet network
    :param net: network object
    :param size: number of routers
    """
    size = test_parameters['topo_size']
    capacity_range = test_parameters['capacity_range']
    capacity_delta = test_parameters['capacity_delta']
    a = capacity_range[0]
    b = capacity_range[1]

    h1 = net.get('h1')
    h1.setIP('10.0.0.10', intf='h1-eth0')
    h1.cmd("ifconfig h1-eth0 10.0.0.10/24")
    h1.cmd("route add default gw 10.0.0.2 dev h1-eth0")

    configure_routers(net, **test_parameters)
    configure_cross_hosts(net, size)

    h2 = net.get('h2')
    h2.setIP('10.0.{}.10'.format(size), intf='h2-eth0')
    h2.cmd("ifconfig h2-eth0 10.0.{}.10/24".format(size))
    h2.cmd("route add default gw 10.0.{}.1".format(size))

    capacities = generate_capacities(a, b, size+1, capacity_delta)
    print(capacities)
    set_capacities(net, size, capacities)

    # do I actually need this???
    h1.cmd('tc qdisc replace dev leftHost-eth0 root fq pacing')
    h1.cmd('ethtool -K leftHost-eth0 tso off')
    h2.cmd('tc qdisc replace dev rightHost-eth0 root netem delay 50')

    # save_capacities_to_file(capacities)

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

    set_capacity = "tc qdisc add dev r{}-eth{} root handle 1: tbf latency 100ms buffer 2000b rate {}mbit"

    for i in range(n_routers):
        # Apply traffic limiter at router i
        router = net.get("r{}".format(i+1))

        # limit eth0 and eth1 respectively
        router.cmd(set_capacity.format(i+1, 0, capacities[i]))
        router.cmd(set_capacity.format(i+1, 1, capacities[i + 1]))

        # # loss on left interface
        # router.cmd("tc qdisc add dev r{}-eth0 parent 1:1 handle 10: netem limit 1000 loss {}%".format(i, 10))
        # # loss on right interface
        # router.cmd("tc qdisc add dev r{}-eth1 parent 1:1 handle 10: netem limit 1000 loss {}%".format(i, 10))

def configure_icmp_ratelimit(router, rate_limit=1000):
    """
    Set icmp_ratelimit if it exists.
    :param router: the router that is modified
    :param rate_limit: the rate limit value
    """
    disable_icmp_ratemask = "sysctl -w net.ipv4.icmp_ratemask=0"
    set_icmp_ratelimit = "sysctl -w net.ipv4.icmp_ratelimit={}".format(rate_limit)

    if(rate_limit != 0):
        router.cmd(set_icmp_ratelimit)
    else:
        router.cmd(disable_icmp_ratemask)

def apply_packet_loss(host, packet_loss):
    """
    Apply artificial packet loss to routers
    :param host: target host
    :param packet_loss: percentage of packets to be lost 
    """
    apply_packet_loss = "tc qdisc add dev {}-eth{} parent 1:1 handle 10: netem limit 10000 loss {}%"
    host.cmd(apply_packet_loss.format(host, 0, packet_loss))
    host.cmd(apply_packet_loss.format(host, 1, packet_loss))

# ========================= Run ========================= #
def cross_traffic(net, ct, duration=10, router_count=3):
    """
    Apply cross traffic to the network
    :param net: network instance
    :param ct: cross traffic load
    :param duration: experiment duration
    :param router_count: number of routers
    """
    capacities = get_assigned_capacities()
    topHost = net.get("t1")
    bottomHost = net.get("b2")
    
    cmd_bottom= "iperf -s -t {} -B 10.2.{}.40"
    cmd_top= "iperf -c 10.2.{}.40 -t {} -B 10.1.{}.20 -b {}M"

    # Prefer UDP traffic (-u parameter)
    # cmd_bottom= "iperf -s -u -t {} -B 10.2.{}.40"
    # cmd_top= "iperf -c 10.2.{}.40 -u -t {} -B 10.1.{}.20 -b {}M"

    lastTop = net.get("t{}".format(router_count))
    firstBottom = net.get("b1")

    # lastTop.popen(cmd_top.format(1, duration + 5, router_count, min(capacities) * ct), stdout=PIPE, stderr=PIPE)
    # firstBottom.popen(cmd_bottom.format(duration + 5, 1))

    t1 = net.get("t1")
    b2 = net.get("b2")

    t1.cmd("tcpdump -n -w top_bottom_hosts/tophost.pcap &")
    b2.cmd("tcpdump -n -w top_bottom_hosts/bottomhost.pcap &")
    t1.cmd("tcpdump -A -r top_bottom_hosts/tophost.pcap > top_bottom_hosts/tophost.txt &")
    b2.cmd("tcpdump -A -r top_bottom_hosts/bottomhost.pcap > top_bottom_hosts/bottomhost.txt &")
    
    time.sleep(5)
    for i in range(2, router_count+1):
        bottomHost = net.get("b{}".format(i))
        cmd = cmd_bottom.format(duration + 2, i)
        bottomHost.popen(cmd, stdout=PIPE, stderr=PIPE)

    for i in range(1, router_count):
        topHost = net.get("t{}".format(i))
        cmd = cmd_top.format(i + 1, duration + 2, i, capacities[i] * ct)
        topHost.popen(cmd, stdout=PIPE, stderr=PIPE)

    time.sleep(5)
    t1.cmd("pkill tcpdump")
    b2.cmd("pkill tcpdump")

def inject_and_capture(sender_host, receiver_host, routers=3, packets=300):
    """
    Wrap-up function that injects traffic into network and captures it with tcpdump
    :param sender_host: sender host IP address
    :param receiver_host: receiver host IP address
    :param routers: number of routers in the network
    :param packets: number of packets to target each router
    """
    h1 = sender_host.IP()
    h2 = receiver_host.IP()

    time.sleep(1)
    sender_host.cmd("tcpdump -n icmp -w results/icmp.pcap &")
    time.sleep(3)
    sender_host.cmd("tcpdump -n tcp -w results/tcp.pcap &")
    time.sleep(3)
    sender_host.cmd("./TrafficGenerator {} {} {} {}".format(h1, h2, routers, packets))
    time.sleep(5)
    sender_host.cmd("pkill tcpdump")

def run_topo(**test_parameters):
    """
    Run the experiment
    :param test_parameters: test parameters from the .json file
    """
    size = test_parameters['topo_size']
    packet_size = test_parameters['packet_size']
    packets = test_parameters['packets_per_hop']
    ct = test_parameters['cross_traffic']

    set_packet_size(packet_size)

    net =  build_topo(size)
    net.build()
    net.start()
    configure_net(net, size, **test_parameters)

    # CLI(net)

    h1 = net.get('h1')
    h2 = net.get('h2')
    if(ct > 0):
        cross_traffic(net, ct, 15, size)
    inject_and_capture(h1, h2, size, packets)

    net.stop()
    cleanup()


# if __name__ == '__main__':
#     setLogLevel('info')
#     run_topo()
