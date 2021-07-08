from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.clean import cleanup
from subprocess import PIPE
from time import sleep

import sys
import time


class CrossTrafficTopo(Topo):

    def build(self, size=1):
        """
        Declare topology components and links and build topology
        :param size: Amount of intermediary routers
        """

        # At least one sender and receiver required
        assert size >= 1, "Topology size must be at least 1!"

        # Declare main sender and receiver host
        leftHost = self.addHost("leftHost")
        rightHost = self.addHost("rightHost")

        # Iterate through path using last node
        lastNode = leftHost

        # Add all intermediary nodes
        for i in range(0, size):
            # Add Crosstraffic Hosts
            topHost = self.addHost("t" + str(i))
            bottomHost = self.addHost("b" + str(i))

            # Add Router
            r = self.addHost("r" + str(i))

            # Add Link to left Router/Host
            self.addLink(r, lastNode)

            # add Link to TopHost
            self.addLink(topHost, r)

            # add Link to BottomHost
            self.addLink(bottomHost, r)

            # for next Link save current router
            lastNode = r

        # Connect last router with right Host
        self.addLink(lastNode, rightHost)


def build_topo(switch_count, capacities, cross_traffic, packets, size, iterations, packet_loss, bottleneck, folder_name, threads, test_tcp,
               verbose=False, tcpdump=False):
    """
    Build and execute topology
    :param switch_count: number of intermediary routers
    :param capacities: Link capacity distribution list
    :param cross_traffic: Cross traffic load [min,normal,max]
    :param packets: Number of ICMP Packets sent in one bulk to one router
    :param size: ICMP Packet_size + L2+L3 Header
    :param iterations: Number of tests done in one run.
    :param packet_loss: % of Packetloss on each router
    :param bottleneck: [weak,location,strong]   location: The position of the bottleneck
                                                weak,strong: The position of the weakly/strongly congested link
                                                    relative to the bottleneck
    :param folder_name: The folder to put tcpdumps
    :param threads: #Threads to use by the ping program
    :param test_tcp: Weather to run the TCP test or not
    :param verbose: Verbose output mode
    :param tcpdump: Capture all traffic on right side of first router
    """

    try:
        # Initialize topology
        topo = CrossTrafficTopo(size=switch_count)
        net = Mininet(topo=topo, link=TCLink)
        net.start()

    except Exception as e:
        print("Could not start Mininet!")
        print(e)
        sys.exit(1)

    # Print a Graph of the main networkath
    graph = "each IP starting with 10.0.\n[left](0.10)--{}Mbits--".format(capacities[0])
    for i, c in enumerate(capacities[1:]):
        graph += "({}.1)<r{}>({}.2)--{}Mbits--".format(i, i, i + 1, c)
    graph += "({}.10)[right]".format(switch_count)

    if verbose:
        print("Created topology with " + str(switch_count) + " switches.")
        print("Capacity distributions: {}".format(graph))

    leftHost = net.get("leftHost")

    # Configure Routers and Hosts
    configure_net(net, switch_count)

    # Set link capacities
    set_capacities(switch_count, capacities, net, packet_loss)

    print("Network setup done...\n")
    sleep(0.5)

    # Dump on first router for debugging
    if tcpdump:
        try:
            net.get("r0").popen("tcpdump -i r0-eth3 -w {}/sw1.pcap".format(folder_name), stdout=PIPE, stderr=PIPE)
        except Exception as e:
            print("Error on starting tcpdump\n{}".format(e))

    to_close = []
    # Start crosstraffic if it is set
    if cross_traffic[2] != 0.0:
        # duration how long crosstraffic runs
        ct_len = (switch_count + 1) * iterations * 3
        if packets >= 1000:
            ct_len *= packets / 500

        # Crosstraffic setup
        to_close = cross_traffic_setup(cross_traffic, switch_count, ct_len, capacities, net, bottleneck, verbose)

    # Start Main file transfer
    main_test(net, packets, iterations, switch_count, size, verbose, folder_name, threads, test_tcp)

    for cl in to_close:
        cl.kill()

    # exit mininet
    net.stop()
    cleanup()


def to_hex(i):
    return "{:x}{:x}".format(i / 16, i % 16)


def configure_net(net, switch_count):
    """
    Configure all Hosts and Routers
    Define routing tables to correctly distribute traffic

    :param switch_count: Amount of intermediary routers
    :param net: The network

    Routers have on each link a own /24 subnet
    on their left side .1 and on their right side .2 IPs
    on top and bottom .1 IPs
    interface is left:0 top:1 bottom:2 right:3
    for the main networkpath 10.0.0.0/16 is reserved
    for the top hosts 10.1.0.0/16 is reserved
    for th bottom hosts 10.2.0.0/16 is reserved
    """

    # left and right Host configuration
    leftHost = net.get("leftHost")
    rightHost = net.get("rightHost")

    # left and right Host Have in their /24 subnet the .10 IP
    leftHost.cmd("ifconfig leftHost-eth0 0")
    leftHost.cmd("ifconfig leftHost-eth0 hw ether 06:00:00:02:00:01")
    leftHost.cmd("ifconfig leftHost-eth0 mtu 1500")
    leftHost.cmd("ip addr add 10.0.0.10/24 brd + dev leftHost-eth0")
    leftHost.cmd("ip route add 10.0.0.0/8 via 10.0.0.1 dev leftHost-eth0")

    rightHost.cmd("ifconfig rightHost-eth0 0")
    rightHost.cmd("ifconfig rightHost-eth0 hw ether 06:00:00:02:00:02")
    rightHost.cmd("ifconfig rightHost-eth0 mtu 1500")
    rightHost.cmd("ip addr add 10.0.{}.10/24 brd + dev rightHost-eth0".format(switch_count))
    rightHost.cmd("ip route add 10.0.0.0/8 via 10.0.{}.2 dev rightHost-eth0".format(switch_count))

    for i in range(switch_count):
        router = net.get("r{}".format(i))
        bottomHost = net.get("b{}".format(i))
        topHost = net.get("t{}".format(i))

        # Setting up interfaces
        router.cmd("ifconfig r{}-eth0 0".format(i))
        router.cmd("ifconfig r{}-eth1 0".format(i))
        router.cmd("ifconfig r{}-eth2 0".format(i))
        router.cmd("ifconfig r{}-eth3 0".format(i))
        topHost.cmd("ifconfig t{}-eth0 0".format(i))
        bottomHost.cmd("ifconfig b{}-eth0 0".format(i))

        # Setting Hardware-adress to interfaces
        router.cmd("ifconfig r{}-eth0 hw ether 06:00:00:00:{}:01".format(i, to_hex(i)))
        router.cmd("ifconfig r{}-eth1 hw ether 06:00:00:00:{}:02".format(i, to_hex(i)))
        router.cmd("ifconfig r{}-eth2 hw ether 06:00:00:00:{}:03".format(i, to_hex(i)))
        router.cmd("ifconfig r{}-eth3 hw ether 06:00:00:00:{}:04".format(i, to_hex(i)))
        topHost.cmd("ifconfig t{}-eth0 hw ether 06:00:00:01:{}:01".format(i, to_hex(i)))
        bottomHost.cmd("ifconfig b{}-eth0 hw ether 06:00:00:01:{}:02".format(i, to_hex(i)))

        # Setting mtu to interfaces
        router.cmd("ifconfig r{}-eth0 mtu 1500".format(i))
        router.cmd("ifconfig r{}-eth1 mtu 1500".format(i))
        router.cmd("ifconfig r{}-eth2 mtu 1500".format(i))
        router.cmd("ifconfig r{}-eth3 mtu 1500".format(i))
        topHost.cmd("ifconfig t{}-eth0 mtu 1500".format(i))
        bottomHost.cmd("ifconfig b{}-eth0 mtu 1500".format(i))

        # Setting IP adresses to interfaces (described at function-header)
        # to left, top, bottom, right
        router.cmd("ip addr add 10.0.{}.1/24 brd + dev r{}-eth0".format(i, i))
        router.cmd("ip addr add 10.1.{}.1/24 brd + dev r{}-eth1".format(i, i))
        router.cmd("ip addr add 10.2.{}.1/24 brd + dev r{}-eth2".format(i, i))
        router.cmd("ip addr add 10.0.{}.2/24 brd + dev r{}-eth3".format(i + 1, i))
        topHost.cmd("ip addr add 10.1.{}.2/24 brd + dev t{}-eth0".format(i, i))
        bottomHost.cmd("ip addr add 10.2.{}.2/24 brd + dev b{}-eth0".format(i, i))

        # Enable forward of Ip-Packets=> makes Host to router
        router.cmd("sysctl -w net.ipv4.ip_forward=1")

        # For TCP Crosstraffic TCP Segmentation operation needs to be disabled=> for correct mtu
        topHost.cmd("ethtool -K t{}-eth0 tso off".format(i))
        bottomHost.cmd("ethtool -K t{}-eth0 tso off".format(i))

        # Routingtables:
        # each router gets the right Gateway static implemented
        # for Crosstraffic:
        topHost.cmd("ip route add default via 10.1.{}.1 dev t{}-eth0".format(i, i))
        bottomHost.cmd("ip route add default via 10.2.{}.1 dev b{}-eth0".format(i, i))

        # Routes nach links:
        for j in range(i):
            # alle subnetze vom 10.0.0.0/24 bis zum aktuellen 10.0.i.0/24
            router.cmd("ip route add 10.0.{}.0/24 via 10.0.{}.2 dev r{}-eth0 proto kernel".format(j, i, i))

            # alle linken BottomHosts
            router.cmd("ip route add 10.2.{}.0/24 via 10.0.{}.2 dev r{}-eth0 proto kernel".format(j, i, i))

            # alle linken TopHosts
            router.cmd("ip route add 10.1.{}.0/24 via 10.0.{}.2 dev r{}-eth0 proto kernel".format(j, i, i))

        # Routes nach rechts
        for j in range(i + 1, switch_count):
            # alle subnetze vom aktuellen 10.0.i+1.0/24 zum 10.0.switch_count.0/24
            router.cmd("ip route add 10.0.{}.0/24 via 10.0.{}.1 dev r{}-eth3 proto kernel".format(j + 1, i + 1, i))

            # alle rechten BottomHosts
            router.cmd("ip route add 10.2.{}.0/24 via 10.0.{}.1 dev r{}-eth3 proto kernel".format(j, i + 1, i))

            # alle rechten TopHosts
            router.cmd("ip route add 10.1.{}.0/24 via 10.0.{}.1 dev r{}-eth3 proto kernel".format(j, i + 1, i))


def set_capacities(switch_count, capacities, net, loss):
    """
    Set link capacities by applying traffic limiters throughout the path
    :param switch_count: Amount of intermediary switches
    :param capacities: Link capacity distribution list
    :param net: Mininet network object
    :param loss: The Packetloss per router, if one should be applied
    """

    # Get left and rigth Host
    leftHost = net.get("leftHost")
    rightHost = net.get("rightHost")

    # Apply traffic limiters to first and last link
    leftHost.cmd("tc qdisc add dev leftHost-eth0 root handle 1: tbf latency 100ms buffer 2000b rate {}mbit".format(
        capacities[0]))
    rightHost.cmd("tc qdisc add dev rightHost-eth0 root handle 1: tbf latency 100ms buffer 2000b rate {}mbit".format(
        capacities[-1]))

    for i in range(0, switch_count):
        # Apply traffic limiter at switch i

        router = net.get("r{}".format(i))

        # limit left interface capacity
        comand = "tc qdisc add dev r{}-eth{} root handle 1: tbf latency 100ms buffer 2000b rate {}mbit"
        router.cmd(comand.format(i, 0, capacities[i]))

        # limit right interface capacity
        router.cmd(comand.format(i, 3, capacities[i + 1]))

        # apply artificial packetloss
        if loss != 0:
            # loss on left interface
            router.cmd("tc qdisc add dev r{}-eth0 parent 1:1 handle 10: netem limit 10000 loss {}%".format(i, loss))

            # loss on right interface
            router.cmd("tc qdisc add dev r{}-eth3 parent 1:1 handle 10: netem limit 10000 loss {}%".format(i, loss))


def cross_traffic_setup(cross_traffic, switch_count, ct_len, capacities, net, bottleneck, verbose):
    """
    :param cross_traffic: [min,norm,max]
                            norm:The % amount of crosstraffic sent to one interface: the link has 2* crosstraffic on it
                            min: Crosstraffic % at the minimal crosstraffic location
                            max: Crosstraffic % at the maximal crosstraffic location
    :param switch_count: Number of routers between the Hosts
    :param ct_len: duration the iperf program has to send crosstraffic
    :param capacities: Capacity distribution along the networkpath
    :param net: Mininet network object
    :param bottleneck: [weak,location,strong]   location: The position of the bottleneck
                                                weak,strong: The position of the weakly/strongly congested link
                                                    relative to the bottleneck
    :param verbose: enable verbose output

    in this funtion iperf is configured to send udp packets with a specific crosstraffic amount
    The packets are sent on one link in both directions.
    """
    close = []
    # Setup all iperf servers; located on all top and bottom hosts except of b0 and t(switch_count -1)
    for i in range(0, switch_count - 1):
        cmd = "iperf -s -u -t {} -B 10.1.{}.2".format(ct_len, i)
        close.append(net.get("t{}".format(i)).popen(cmd, stdout=PIPE, stderr=PIPE))

        cmd = "iperf -s -u -t {} -B 10.2.{}.2".format(ct_len, i + 1)
        close.append(net.get("b{}".format(i + 1)).popen(cmd, stdout=PIPE, stderr=PIPE))

    # Setup all iperf clients; located on all top and bottom hosts except of b0 and t(switch_count -1)
    for i in range(1, switch_count):

        # Set the crosstraffic amount depending on the bottlenecklocation
        if i == bottleneck[0]:
            cross = cross_traffic[0]
        elif i == bottleneck[2]:
            cross = cross_traffic[2]
        else:
            cross = cross_traffic[1]

        cmd = "iperf -c 10.1.{}.2 -u -t {} -B 10.2.{}.2 -b {}M".format(i - 1, ct_len, i, capacities[i] * cross)
        #net.get("b{}".format(i)).popen(cmd, stdout=PIPE, stderr=PIPE)

        cmd = "iperf -c 10.2.{}.2 -u -t {} -B 10.1.{}.2 -b {}M".format(i, ct_len, i - 1, capacities[i] * cross)
        net.get("t{}".format(i - 1)).popen(cmd, stdout=PIPE, stderr=PIPE)

    if verbose:
        print("Started cross traffic flows")
    return close


def main_test(net, packets, iterations, switch_count, size, verbose, folder_name, threads, test_tcp):
    """
    :param net: Mininet instance
    :param packets: Number of ICMP Packets sent in one bulk to one router
    :param iterations: Number of tests done in one run (one network setup).
    :param switch_count: number of intermediary routers
    :param size: ICMP Packet_size + L2+L3 Header
    :param verbose: Verbose output mode
    :param folder_name: Folder to put TCPdumps
    :param threads: number threads to use by the pp_locate_helper(ping)
    :param test_tcp: Weather to run the TCP test or not

    Main Testfunction:
    sent as fast as possible #packets with size size from leftHost to each router and then righthost.
    save tcpdump of sent and received packets
    """

    leftHost = net.get('leftHost')
    duration = 0.1
    sp1 = []
    try:
         sp1.append(net.get('rightHost').popen("iperf -s -B 10.0.{}.10".format(switch_count), stdout=PIPE, stderr=PIPE))
    except Exception as e:
        print("Error on starting tcpdump\n{}".format(e))
        sys.exit(1)
    for it in range(iterations):
        # Start capturing ICMP Packets
        sp2 = []
        try:
            capture_packets = packets * 2 * (switch_count + 1)
            sp2.append(leftHost.popen(
                "tcpdump -i leftHost-eth0 -c {} -w {}/sender-tcp-{}.pcap tcp".format(5*packets, folder_name, it),
                stdout=PIPE, stderr=PIPE))
            leftHost.popen("tcpdump --time-stamp-precision=nano -i leftHost-eth0 icmp -c {} -w {}/sender-{}.pcap".format(capture_packets, folder_name,it),
                           stdout=PIPE, stderr=PIPE)
        except Exception as e:
            print("Error on starting tcpdump\n{}".format(e))
            sys.exit(1)

        if verbose:
            print("Started tcpdump")

        # Wait for tcpdump to initialize
        time.sleep(1)

        # Start Pings
        try:
            if verbose:
                print("Running main file transfer...")
            if test_tcp:
                leftHost.cmd("iperf -c 10.0.{}.10 -B 10.0.0.10 -t 3".format(switch_count))
                time.sleep(duration)
            #Main ping program => ping #threads #icmp msg size #packets #ip
            comand = "./pp_locate_helper {} {} {} 10.0.{}.1"

            #Send to each Router
            for i in range(switch_count):
                leftHost.cmd(comand.format(threads, size-34, packets, i))
                time.sleep(duration)

            #Send to rightHost
            leftHost.cmd(comand.format(threads, size-34, packets, switch_count) + "0")
            time.sleep(duration)

            #do some pings to stop tcpdump if packetloss happend
            leftHost.cmd("timeout -k 0.1 0.1 ping -s {} -c {} -i 0 10.2.0.2".format(64, 2 * packets))
            time.sleep(duration)
        except (KeyboardInterrupt, Exception) as e:
            if isinstance(e, KeyboardInterrupt):
                print("\nReceived keyboard interrupt. Stop Mininet.")
            else:
                print(e)
    if verbose:
        print("Networktest Done! Stopping mininet!")
    sleep(1)


def run_topo(folder_name, capacities, cross_traffic, packet_count, packet_size, verbose, iterations, packet_loss, threads,
             bottleneck_location, test_tcp, **kwargs):
    """
    Helper-Function:
    for parameter description look at build_topo()
    """

    switch_count = len(capacities) - 1

    try:

        build_topo(switch_count, capacities, cross_traffic, packet_count, packet_size, iterations, packet_loss,
                   bottleneck_location, folder_name, threads, test_tcp, verbose=verbose)
    except Exception as e:
        print(e)
        print("Cleaning up environment...")
        cleanup()
