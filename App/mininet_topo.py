#!/usr/bin/python
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info

# ///////////////////////////////////////////////////////////// #

def rp_disable(host):
    ifaces = host.cmd('ls /proc/sys/net/ipv4/conf')
    ifacelist = ifaces.split()    # default is to split on whitespace
    for iface in ifacelist:
       if iface != 'lo': host.cmd('sysctl net.ipv4.conf.' + iface + '.rp_filter=0')

def build_topo(size=1):
    net = Mininet()
    h1 = net.addHost('h1', ip='10.0.0.10')
    h2 = net.addHost('h2', ip='10.0.{}.10'.format(size))
    
    
    for i in range(1, size+1):
        net.addHost('r{}'.format(i), ip='10.0.{}.2'.format(i-1))
        # print('r{}'.format(i), '10.0.{}.2'.format(i-1))
    

    net.addLink(h1, net.get('r1'), intfName1='h1-eth0', intfName2='r1-eth0')
    
    for i in range(1, size):
        net.addLink(net.get('r{}'.format(i)), net.get('r{}'.format(i+1)), intfName1='r{}-eth1'.format(i), intfName2='r{}-eth0'.format(i+1))
        # print('r{}'.format(i), 'r{}'.format(i+1), 'r{}-eth1'.format(i), 'r{}-eth0'.format(i+1))
    
    net.addLink(net.get('r{}'.format(size)), h2, intfName1='r{}-eth1'.format(size), intfName2='h2-eth0')

    # print(type(net.get('r{}'.format(size))))
    
    net.build()
    
    configure_net(net, size)

    net.start()
    CLI(net)
    net.stop()

def configure_routers(net, size):
    for i in range(1, size+1):
        router = net.get('r{}'.format(i))
        router.cmd("ifconfig r{}-eth0 10.0.{}.2/24".format(i, i-1))
        router.cmd("ifconfig r{}-eth1 10.0.{}.1/24".format(i, i))

        # to the right
        if(i<size):
            router.cmd("ip route add to 10.0.{}.0/24 via 10.0.{}.2".format(size, i))
        else:
            router.cmd("ip route add to 10.0.{}.0/24 via 10.0.{}.10".format(size, size))
        
        # to the left
        if(i>1):
            router.cmd("ip route add to 10.0.0.0/24 via 10.0.{}.1".format(i-1))
        else:
            router.cmd("ip route add to 10.0.0.0/24 via 10.0.0.10")
        
        router.cmd("sysctl net.ipv4.ip_forward=1")
        
        # rp_disable(router)

def configure_net(net, size):
    h1 = net.get('h1')
    h1.setIP('10.0.0.10', intf='h1-eth0')
    h1.cmd("ifconfig h1-eth0 10.0.0.10/24")
    h1.cmd("route add default gw 10.0.0.2 dev h1-eth0")

    configure_routers(net, size)

    h2 = net.get('h2')
    h2.setIP('10.0.{}.10'.format(size), intf='h2-eth0')
    h2.cmd("ifconfig h2-eth0 10.0.{}.10/24".format(size))
    h2.cmd("route add default gw 10.0.{}.1".format(size))

def set_capacities(net, capacities):
    pass

if __name__ == '__main__':
    setLogLevel('info')
    build_topo(9)
