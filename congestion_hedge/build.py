from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch, Controller, RemoteController, DefaultController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from sys import argv
import numpy as np
import time

m =0

class RTopo(Topo):
    #def __init__(self, **kwargs):
    #global r
    def build(self, **_opts):     # special names?
        global m
        topo_file = 'default.topo'
        if len(argv) > 1:
            topo_file = argv[1]
        f = open(topo_file, 'r')
        n, m, k, queue = [int(x) for x in f.readline()[:-1].split()] # #hosts, #switches, # edges
        dic = {}
        for i in range(n):
            name = f.readline()[:-1]
            #dic[name] = self.addHost(name, ip = '10.0.1.{}/32'.format(i))
            dic[name] = self.addHost(name)
        for i in range(m):
            name = f.readline()[:-1]
            dic[name] = self.addSwitch(name) #, protocols = "OpenFlow13")
        print(dic)
        print type(dic['h1'])
        
        for i in range(k):
            x, y, bw, delay = f.readline()[:-1].split()
            bw = int(bw)
            self.addLink(dic[x], dic[y])
            #self.addLink(dic[x], dic[y], bw = bw, delay = delay, queue = queue)

        # defaultIP = '10.0.1.1/24'  # IP address for r0-eth1
        # r  = self.addNode( 'r', cls=LinuxRouter) # , ip=defaultIP )
        # h1 = self.addHost( 'h1', ip='10.0.1.10/24', defaultRoute='via 10.0.1.1' )
        # h2 = self.addHost( 'h2', ip='10.0.2.10/24', defaultRoute='via 10.0.2.1' )
        # h3 = self.addHost( 'h3', ip='10.0.3.10/24', defaultRoute='via 10.0.3.1' )

        # #  h1---80Mbit---r---8Mbit/100ms---h2
 
        # self.addLink( h1, r, intfName1 = 'h1-eth', intfName2 = 'r-eth1', bw=80,
        #          params2 = {'ip' : '10.0.1.1/24'})

        # self.addLink( h2, r, intfName1 = 'h2-eth', intfName2 = 'r-eth2', bw=80,
        #          params2 = {'ip' : '10.0.2.1/24'})

        # self.addLink( h3, r, intfName1 = 'h3-eth', intfName2 = 'r-eth3', 
        #          params2 = {'ip' : '10.0.3.1/24'}, 
        #          bw=BottleneckBW, delay=DELAY, queue=QUEUE)     # apparently queue is IGNORED here.

# delay is the ONE-WAY delay, and is applied only to traffic departing h3-eth.

# BBW=8: 1 KB/ms, for 1K packets; 110 KB in transit
# BBW=10: 1.25 KB/ms, or 50 KB in transit if the delay is 40 ms.
# queue = 267: extra 400 KB in transit, or 8x bandwidthxdelay

def main():
    rtopo = RTopo()
    net = Mininet(topo = rtopo,
                   #link=TCLink,
                   switch = OVSKernelSwitch, 
                   controller = RemoteController,
          autoSetMacs = True   # --mac
                )  
    #c1 = net.addController('c1',controller = RemoteController, ip='127.0.0.1', port = 6633)
    #c1.start()    
    #for i in range(1,m+1):
    #    net['s'+str(i)].start([c1])
    c = RemoteController( 'c', ip='127.0.0.1', port=6633 )
    net.addController(c)

    net.start()
    CLI(net)
    hosts =[] 
    for i in range(2,8):
        hosts.append('h'+str(i))
    portnum = range(5000+2,5000+8)
    schedule = np.array(range(1,7))+ time.time() #time 

    print(type(net['h1']))
    for t in range(0,6):
        net[hosts[t]].cmd('python2 receive.py {} {}>>{}.txt&'.format(portnum[t], schedule[t], hosts[t]))
        net['h1'].cmd('python2 send.py {} {} {} {}>>sender.txt&'.format(1000,net[hosts[t]].IP(), portnum[t], schedule[t], 0.1))

    CLI(net)
    net.stop()

setLogLevel('info')
main()

"""
This leads to a queuing hierarchy on r with an htb node, 5:0, as the root qdisc. 
The class below it is 5:1. Below that is a netem qdisc with handle 10:, with delay 110.0ms.
We can change the limit (maximum queue capacity) with:

    tc qdisc change dev r-eth1 handle 10: netem limit 5 delay 110.0ms

"""
