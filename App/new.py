#!/usr/bin/python
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI

def rp_disable(host):
    ifaces = host.cmd('ls /proc/sys/net/ipv4/conf')
    ifacelist = ifaces.split()    # default is to split on whitespace
    for iface in ifacelist:
       if iface != 'lo': host.cmd('sysctl net.ipv4.conf.' + iface + '.rp_filter=0')


def build(n_hosts):

    net = Mininet()

    h1 = net.addHost('h1',ip='10.0.0.1')

    for i in range (1, n_hosts+1):
        net.addHost("r{}".format(i), ip="10.0.{}.2".format(i-1))


    h2 = net.addHost('h2', ip='10.0.{}.2'.format(n_hosts))

    # =========================
    r1 = net.get('r1')
    net.addLink(h1,r1,intfName1='h1-eth0',intfName2='r1-eth0')

    for i in range (1, n_hosts):
        net.addLink(net.get('r{}'.format(i)), net.get('r{}'.format(i + 1)), intfName1='r{}-eth1'.format(i),
                    intfName2='r{}-eth0'.format(i + 1))

    net.addLink(net.get('r{}'.format(n_hosts)), h2, intfName1='r4-eth1',intfName2='h2-eth0')
    net.build()

    return net
#enddef

# def config_routers():
#     pass
# #enddef

def config_net(net, n_hosts):

    h1 = net.get('h1')
    h2 = net.get('h2')

    h1.setIP('10.0.0.1', intf='h1-eth0')
    h1.cmd("ifconfig h1-eth0 10.0.0.1 netmask 255.255.255.0")
    h1.cmd("route add default gw 10.0.0.2 dev h1-eth0")

    for i in range(1, n_hosts+1):
        net.get('r{}'.format(i)).cmd("ifconfig r{}-eth0 10.0.{}.2/24".format(i, i-1))
        net.get('r{}'.format(i)).cmd("ifconfig r{}-eth1 10.0.{}.1/24".format(i, i))
        net.get('r{}'.format(i)).cmd("ip route add to 10.0.4.0/24 via 10.0.{}.2".format(i))
        net.get('r{}'.format(i)).cmd("ip route add to 10.0.0.0/24 via 10.0.{}.1".format(i-1))
        net.get('r{}'.format(i)).cmd('sysctl net.ipv4.ip_forward=1')
        rp_disable(net.get('r{}'.format(i)))

    h2.setIP('10.0.{}.2'.format(n_hosts), intf='h2-eth0')
    h2.cmd("ifconfig h2-eth0 10.0.{}.2/24".format(n_hosts))
    h2.cmd("route add default gw 10.0.{}.1".format(n_hosts))
    return net
#enddef


# def run(n_hosts):
#     net = Mininet()
#
#     h1 = net.addHost('h1',ip='10.0.0.1')
#
#     for i in range (1, n_hosts+1):
#         net.addHost("r{}".format(i), ip="10.0.{}.2".format(i-1))
#
#
#     h2 = net.addHost('h2', ip='10.0.{}.2'.format(n_hosts))
#
#     # =========================
#     r1 = net.get('r1')
#     net.addLink(h1,r1,intfName1='h1-eth0',intfName2='r1-eth0')
#
#     for i in range (1, n_hosts):
#         net.addLink(net.get('r{}'.format(i)), net.get('r{}'.format(i + 1)), intfName1='r{}-eth1'.format(i),
#                     intfName2='r{}-eth0'.format(i + 1))
#
#     net.addLink(net.get('r{}'.format(n_hosts)), h2, intfName1='r4-eth1',intfName2='h2-eth0')
#     net.build()
#
#
#     # =====================================
#
#
#     h1.setIP('10.0.0.1', intf='h1-eth0')
#     h1.cmd("ifconfig h1-eth0 10.0.0.1 netmask 255.255.255.0")
#     h1.cmd("route add default gw 10.0.0.2 dev h1-eth0")
#
#     for i in range(1, n_hosts+1):
#         net.get('r{}'.format(i)).cmd("ifconfig r{}-eth0 10.0.{}.2/24".format(i, i-1))
#         net.get('r{}'.format(i)).cmd("ifconfig r{}-eth1 10.0.{}.1/24".format(i, i))
#         net.get('r{}'.format(i)).cmd("ip route add to 10.0.4.0/24 via 10.0.{}.2".format(i))
#         net.get('r{}'.format(i)).cmd("ip route add to 10.0.0.0/24 via 10.0.{}.1".format(i-1))
#         net.get('r{}'.format(i)).cmd('sysctl net.ipv4.ip_forward=1')
#         rp_disable(net.get('r{}'.format(i)))
#
#     h2.setIP('10.0.{}.2'.format(n_hosts), intf='h2-eth0')
#     h2.cmd("ifconfig h2-eth0 10.0.{}.2/24".format(n_hosts))
#     h2.cmd("route add default gw 10.0.{}.1".format(n_hosts))
#
#
#     net.start()
#     # time.sleep(1)
#     CLI(net)
#     net.stop()

if __name__ == '__main__':
    n_hosts = 4
    net = build(n_hosts)
    x = config_net(net, n_hosts)

    print(x==net)
    # ================

    net.start()
    CLI(net)
    net.stop()




