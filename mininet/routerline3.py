"""router topology example

chain of 3 routers between two hosts; simpler than the general version

   h1---r1---r2---r3---h2

Subnets are 10.0.0 to 10.0.3
Last byte (host byte) is 2 on the left and 1 on the right
   10.0.0.2-r1-10.0.1.1
   10.0.1.2-r2-10.0.2.1
   10.0.2.2-r3-10.0.3.1
ri-eth0 is on the left and ri-eth1 is on the right

"""

# mn --custom router.py --topo rtopo

from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch, Controller, RemoteController
#from mininet.node import Node, Host, OVSSwitch, OVSKernelSwitch, Controller, RemoteController, DefaultController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import setLogLevel, info

ENABLE_LEFT_TO_RIGHT_ROUTING = True		# tell all routers how to get to h2

class RTopo(Topo):

    def build(self, **_opts):     # special names?
        h1 = self.addHost( 'h1', ip='10.0.0.10/24', defaultRoute='via 10.0.0.2' )
        h2 = self.addHost( 'h2', ip='10.0.3.10/24', defaultRoute='via 10.0.3.1' )
        r1 = self.addHost( 'r1' )
        r2 = self.addHost( 'r2' )
        r3 = self.addHost( 'r3' )

        self.addLink( h1, r1, intfName1 = 'h1-eth0', intfName2 = 'r1-eth0')
        self.addLink( r1, r2, inftname1 = 'r1-eth1', inftname2 = 'r2-eth0')
        self.addLink( r2, r3, inftname1 = 'r2-eth1', inftname2 = 'r3-eth0')
        self.addLink( r3, h2, intfName1 = 'r3-eth1', intfName2 = 'h2-eth0')


def run():
    rtopo = RTopo()
    net = Mininet(topo = rtopo, link=TCLink, autoSetMacs = True)
    net.start()
    
    r1 = net['r1']
    r2 = net['r2']
    r3 = net['r3']
    h1 = net['h1']
    h2 = net['h2']

    r1.cmd('ifconfig r1-eth0 10.0.0.2/24')
    r1.cmd('ifconfig r1-eth1 10.0.1.1/24')
    r1.cmd('sysctl net.ipv4.ip_forward=1')
    rp_disable(r1)

    r2.cmd('ifconfig r2-eth0 10.0.1.2/24')
    r2.cmd('ifconfig r2-eth1 10.0.2.1/24')
    r2.cmd('sysctl net.ipv4.ip_forward=1')
    rp_disable(r2)

    r3.cmd('ifconfig r3-eth0 10.0.2.2/24')
    r3.cmd('ifconfig r3-eth1 10.0.3.1/24')
    r3.cmd('sysctl net.ipv4.ip_forward=1')
    rp_disable(r3)

    # add one-way routes to 10.0.3.0/24:
    if ENABLE_LEFT_TO_RIGHT_ROUTING:
        r1.cmd('route add -net 10.0.3.0/24 gw 10.0.1.2')
        r2.cmd('route add -net 10.0.3.0/24 gw 10.0.2.2')
    
    for h in [h1, r1, r2, r3, h2]:  h.cmd('/usr/sbin/sshd')

    CLI( net)
    net.stop()

# in the following, ip(4,2) returns 10.0.4.2
def ip(subnet,host,prefix=None):
    addr = '10.0.'+str(subnet)+'.' + str(host)
    if prefix != None: addr = addr + '/' + str(prefix)
    return addr

# For some examples we need to disable the default blocking of forwarding of packets with no reverse path
def rp_disable(host):
    ifaces = host.cmd('ls /proc/sys/net/ipv4/conf')
    ifacelist = ifaces.split()    # default is to split on whitespace
    for iface in ifacelist:
       if iface != 'lo': host.cmd('sysctl net.ipv4.conf.' + iface + '.rp_filter=0')
    #print 'host', host, 'iface list:',  ifacelist


setLogLevel('info')
run()

"""
Manual routing commands:

r1: ip route add to 10.0.3.0/24 via 10.0.1.2 dev r1-eth1
r2: ip route add to 10.0.3.0/24 via 10.0.2.2 dev r2-eth2

r1: route add -net 10.0.3.0/24 gw 10.0.1.2
r2: route add -net 10.0.3.0/24 gw 10.0.2.2

r3: ip route add to 10.0.0.0/24 via 10.0.2.1 dev r3-eth0
r2: ip route add to 10.0.0.0/24 via 10.0.1.1 dev r2-eth0

r3: route add -net 10.0.0.0/24 gw 10.0.2.1
r2: route add -net 10.0.0.0/24 gw 10.0.1.1

"""
