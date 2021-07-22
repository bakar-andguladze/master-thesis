#!/usr/bin/python
from random import random
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import buildTopo
from mininet.clean import cleanup

class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):
    def build(self, size=1):
        assert size >= 1, "minimum size of the topology must be 1"

        leftHost = self.addHost("h1", ip="10.0.0.10", defaultRoute="via 10.0.0.2") 
        rightHost = self.addHost("h2", ip="10.0.{}.10".format(size), defaultRoute="via 10.0.{}.1".format(size-1))

        lastNode = leftHost
        for i in range(0, size):
            # Add Router
            router = self.addHost("r" + str(i), cls=LinuxRouter)
            # Add Link to left Router/Host
            self.addLink(router, lastNode)
            # for next Link save current router
            lastNode = router

        # Connect last router with right Host
        self.addLink(lastNode, rightHost)
        

def configure_routers(net, router_count):
    for i in range(0, router_count):
        router = net.get("r{}".format(i))

        # Setting up interfaces
        router.cmd("ifconfig r{}-eth0 0".format(i))
        router.cmd("ifconfig r{}-eth1 0".format(i))
        # router.cmd("ifconfig r{}-eth2 0".format(i))
        # router.cmd("ifconfig r{}-eth3 0".format(i))

        # Setting mac-adress to interfaces
        router.cmd("ifconfig r{}-eth0 hw ether 06:00:00:00:{}:01".format(i, to_hex(i)))
        router.cmd("ifconfig r{}-eth1 hw ether 06:00:00:00:{}:02".format(i, to_hex(i)))
        # router.cmd("ifconfig r{}-eth2 hw ether 06:00:00:00:{}:03".format(i, to_hex(i)))
        # router.cmd("ifconfig r{}-eth3 hw ether 06:00:00:00:{}:04".format(i, to_hex(i)))

        # Setting mtu to interfaces
        router.cmd("ifconfig r{}-eth0 mtu 1500".format(i))
        router.cmd("ifconfig r{}-eth1 mtu 1500".format(i))
        # router.cmd("ifconfig r{}-eth2 mtu 1500".format(i))
        # router.cmd("ifconfig r{}-eth3 mtu 1500".format(i))

        # Setting IP adresses to interfaces (described at function-header)
        # to left, top, bottom, right
        router.cmd("ip addr add 10.0.{}.1/24 brd + dev r{}-eth0".format(i, i))
        router.cmd("ip addr add 10.1.{}.1/24 brd + dev r{}-eth1".format(i, i))
        # router.cmd("ip addr add 10.2.{}.1/24 brd + dev r{}-eth2".format(i, i))
        # router.cmd("ip addr add 10.0.{}.2/24 brd + dev r{}-eth3".format(i + 1, i))

        # 2 commands: one for left, one for right:
        router.cmd("ip route add to 10.0.3.0/24 via 10.0.{}.2".format(i))
        router.cmd("ip route add to 10.0.{}.0/24 via 10.0.{}.1".format(router_count, i+1))

        # Enable forward of Ip-Packets=> makes Host to router
        # router.cmd("sysctl -w net.ipv4.ip_forward=1")

        # Routes to the LEFT:
        # for j in range(i):
        #    #  alle subnetze vom 10.0.0.0/24 bis zum aktuellen 10.0.i.0/24
        #     router.cmd("ip route add 10.0.{}.0/24 via 10.0.{}.2 dev r{}-eth0 proto kernel".format(j, i, i))

            # alle linken BottomHosts
            # router.cmd("ip route add 10.2.{}.0/24 via 10.0.{}.2 dev r{}-eth0 proto kernel".format(j, i, i))

            # alle linken TopHosts
            # router.cmd("ip route add 10.1.{}.0/24 via 10.0.{}.2 dev r{}-eth0 proto kernel".format(j, i, i))

        # Routes to the RIGHT:
        # for j in range(i + 1, router_count):
        #     # alle subnetze vom aktuellen 10.0.i+1.0/24 zum 10.0.switch_count.0/24
        #     router.cmd("ip route add 10.0.{}.0/24 via 10.0.{}.1 dev r{}-eth3 proto kernel".format(j + 1, i + 1, i))

            # alle rechten BottomHosts
            # router.cmd("ip route add 10.2.{}.0/24 via 10.0.{}.1 dev r{}-eth3 proto kernel".format(j, i + 1, i))

            # alle rechten TopHosts
            # router.cmd("ip route add 10.1.{}.0/24 via 10.0.{}.1 dev r{}-eth3 proto kernel".format(j, i + 1, i))

def configure_net(net, router_count):
    leftHost = net.get("h1")
    rightHost = net.get("h2")

    # left and right Host have in their /24 subnet the .10 IP
    # leftHost.cmd("ifconfig leftHost-eth0 0")
    leftHost.cmd("ifconfig leftHost-eth0 hw ether 06:00:00:02:00:01")
    leftHost.cmd("ifconfig leftHost-eth0 mtu 1500")
    # leftHost.cmd("ip addr add 10.0.0.10/24 brd + dev leftHost-eth0")
    # leftHost.cmd("ip route add 10.0.0.0/8 via 10.0.0.1 dev leftHost-eth0")

    # rightHost.cmd("ifconfig rightHost-eth0 0")
    rightHost.cmd("ifconfig rightHost-eth0 hw ether 06:00:00:02:00:02")
    rightHost.cmd("ifconfig rightHost-eth0 mtu 1500")
    # rightHost.cmd("ip addr add 10.0.{}.10/24 brd + dev rightHost-eth0".format(router_count))
    # rightHost.cmd("ip route add 10.0.0.0/8 via 10.0.{}.2 dev rightHost-eth0".format(router_count))

    configure_routers(net, router_count) 
 
def set_capacities(net, capacities):
    print("dummy") 

def build_topo(router_count):
    topo = NetworkTopo(size=router_count)
    net = Mininet(topo=topo)
    # net.build()
    net.start()
    
    configure_net(net, router_count)


    CLI(net)
    net.stop()
    cleanup()


def to_hex(i):
    return "{:x}{:x}".format(i / 16, i % 16)

def generate_capacities(n):
    capacities = []
    for i in range(n):
        capacities.append(random.randrange(100, 500))
    
    return capacities

def run():
    build_topo(4)

    # Add routing for reaching networks that aren't directly connected
    # info(net['r1'].cmd("ip route add 10.1.0.0/24 via 10.100.0.2 dev r1-eth2"))
    # info(net['r2'].cmd("ip route add 10.0.0.0/24 via 10.100.0.1 dev r2-eth2"))

   
    


if __name__ == '__main__':
    setLogLevel('info')
    run()
