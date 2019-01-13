# copyright 2017 Peter Dordal and Ihab Alshaikhli
# licensed under the Apache 2.0 license
"""
   loadbalance31: 3 hosts at each end, with 1 trunk connection
   In between are a router r (in Mininet this is considered to be a host)
   and a switch s. 

   h1                      t1
   h2 ... r----------s ... t2
   h3                      t3

"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import Node, Host, OVSSwitch, OVSKernelSwitch, Controller, RemoteController, DefaultController
from mininet.cli import CLI
from mininet.log import setLogLevel
import argparse

BANDWIDTH=20		 # in megabits per second

etherfake = '00:00:00:00:01:ff'

class TrunkNKTopo( Topo ):
    "Two clusters of N hosts each, joined by K trunk lines."

    def __init__( self , **kwargs):
        "Create trunk topo."
        super(TrunkNKTopo, self).__init__(**kwargs)
        h = []
        t = []
        ##t = []

        N=3
        K=1
        for key in kwargs:
           if key == 'N':
               N=kwargs[key]
           if key == 'K':
               K=kwargs[key]

        r = self.addHost('r')
        s = self.addSwitch('s',dpid='1')	# this is really s1
        self.addLink(r,s)

        # now start with the hosts

        # add N hosts hi and N hosts ti
        for i in range(1,N+1):
           h.append(self.addHost('h' + str(i)))
           t.append(self.addHost('t' + str(i), mac=etherfake))

        # Add links from hi to r, and from s to ti
        for i in range(N):
           self.addLink(h[i], r)
           self.addLink(t[i], s)

	c = RemoteController( 'c', ip='127.0.0.1', port=6633 )


topos = { 'trunkNK': ( lambda **kwargs: TrunkNKTopo(**kwargs) ) }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-N', '--N', type=int)
    parser.add_argument('-K', '--K', type=int)
    args = parser.parse_args()
    N=3		# the defaults
    K=1
    if args.N is not None:
        N = args.N
    if args.K is not None:
        K = args.K
    trunktopo = TrunkNKTopo(N=N,K=K)
    #setLogLevel('info')
    net = Mininet(topo = trunktopo, switch = OVSKernelSwitch, controller = RemoteController,
		autoSetMacs = True,
		link = TCLink
                )  
    c = RemoteController( 'c', ip='127.0.0.1', port=6633 )
    net.addController(c)
    net.start()

    r = net['r']
    s = net['s']
    
    # left hosts: hi has IPv4 address 10.0.i.1/24
    for i in range(1,N+1):
       hi = net['h' + str(i)]
       hi.cmd('ifconfig {} {}'.format(iface('h', i, 0), ip(i,1,24)))
       hi.cmd('ip route add to default via {} dev {}'.format(ip(i,2), iface('h',i,0)))

    for i in range(1,N+1):
       r.cmd('ifconfig r-eth{} {}'.format(i, ip(i,2,24)))

    r_eth0_addr = '00:00:00:00:00:04'

    r.cmd('sysctl net.ipv4.ip_forward=1')
    r.cmd('ifconfig r-eth0 10.0.0.2/24')
    r.cmd('arp -s 10.0.0.1 {}'.format(etherfake))
    # r.cmd('ip route add to 10.0.0.0/24 via 10.0.0.1 dev r-eth0')   # shouldn't be necessary
    # s.cmd('ifconfig s-eth1 10.0.0.1/24')
    # s.cmd('ip route add to 10.0.0.0/16 via 10.0.0.2 dev s-eth1')

    # now configure the righthand hosts (the servers)
    for i in range(1,N+1):
        ti = net['t' + str(i)]
        ti.cmd('ifconfig {} 10.0.0.1/24'.format(iface('t',i,0)))
        ti.cmd('ip route add to default via 10.0.0.2 dev {}'.format(iface('t',i,0)))
        ti.cmd('arp -s 10.0.0.2 {}'.format(r_eth0_addr))
        ti.cmd('/usr/sbin/sshd')

    CLI( net)
    net.stop()

# iface('h', 1, 3) returns 'h1-eth3'
def iface(letter, num, inum):
    return str(letter) + str(num) + '-eth' + str(inum)

# The following generates IP addresses from a subnet number and a host number
# ip(4,2) returns 10.0.4.2, and ip(4,2,24) returns 10.0.4.2/24
def ip(subnet,host,prefix=None):
    addr = '10.0.'+str(subnet)+'.' + str(host)
    if prefix != None: addr = addr + '/' + str(prefix)
    return addr

setLogLevel('debug')	# or 'info'
main()

