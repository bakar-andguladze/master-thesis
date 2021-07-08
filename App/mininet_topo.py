from mininet.topo import Topo

class customTopo(Topo):
    def __init__(self):
        super(customTopo,self).__init__()

        # add hosts
        leftHost = self.addHost('h1', ip='10.0.0.1/24')        
        rightHost = self.addHost('h2', ip='10.0.1.2/24')
        
        # add routers
        r1 = self.addHost('r1')
        
        
        # switch1 = self.addRouter('r1')
        

        self.addLink(leftHost,r1)
        self.addLink(r1, rightHost)

topos = {'custom':(lambda:customTopo())}