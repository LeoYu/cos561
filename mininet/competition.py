"""router topology example for TCP competions.
   This remains the default version

router between two subnets:

   h1----+
         |
         r ---- h3
         |
   h2----+

For running a TCP competition, consider the runcompetition.sh script
"""

QUEUE=10
DELAY='110ms'		# r--h3 link
BottleneckBW=8
BBR=False

# reno-bbr parameters:
if BBR:
    DELAY='40ms'	
    QUEUE=267
    # QUEUE=25
    QUEUE=10
    BottleneckBW=10

from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch, Controller, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import setLogLevel, info

h1addr = '10.0.1.2/24'
h2addr = '10.0.2.2/24'
r1addr1= '10.0.1.1/24'
r1addr2= '10.0.2.1/24'

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        info ('enabling forwarding on ', self)
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class RTopo(Topo):
    #def __init__(self, **kwargs):
    #global r
    def build(self, **_opts):     # special names?
        defaultIP = '10.0.1.1/24'  # IP address for r0-eth1
        r  = self.addNode( 'r', cls=LinuxRouter) # , ip=defaultIP )
        h1 = self.addHost( 'h1', ip='10.0.1.10/24', defaultRoute='via 10.0.1.1' )
        h2 = self.addHost( 'h2', ip='10.0.2.10/24', defaultRoute='via 10.0.2.1' )
        h3 = self.addHost( 'h3', ip='10.0.3.10/24', defaultRoute='via 10.0.3.1' )

        #  h1---80Mbit---r---8Mbit/100ms---h2
 
        self.addLink( h1, r, intfName1 = 'h1-eth', intfName2 = 'r-eth1', bw=80,
                 params2 = {'ip' : '10.0.1.1/24'})

        self.addLink( h2, r, intfName1 = 'h2-eth', intfName2 = 'r-eth2', bw=80,
                 params2 = {'ip' : '10.0.2.1/24'})

        self.addLink( h3, r, intfName1 = 'h3-eth', intfName2 = 'r-eth3', 
                 params2 = {'ip' : '10.0.3.1/24'}, 
                 bw=BottleneckBW, delay=DELAY, queue=QUEUE) 	# apparently queue is IGNORED here.

# delay is the ONE-WAY delay, and is applied only to traffic departing h3-eth.

# BBW=8: 1 KB/ms, for 1K packets; 110 KB in transit
# BBW=10: 1.25 KB/ms, or 50 KB in transit if the delay is 40 ms.
# queue = 267: extra 400 KB in transit, or 8x bandwidthxdelay

def main():
    rtopo = RTopo()
    net = Mininet(topo = rtopo,
                  link=TCLink,
                  #switch = OVSKernelSwitch, 
                  #controller = RemoteController,
		  autoSetMacs = True   # --mac
                )  
    net.start()
    r = net['r']
    r.cmd('ip route list');
    #r.cmd('ifconfig r-eth0 10.0.1.1/24')
    #r.cmd('ifconfig r-eth1 10.0.2.1/24')
    #r.cmd('ifconfig r-eth2 10.0.3.1/24')
    #r.cmd('sysctl net.ipv4.ip_forward=1')
    r.cmd('tc qdisc change dev r-eth3 handle 10: netem limit {}'.format(QUEUE))

    h1 = net['h1']
    h2 = net['h2']
    h3 = net['h3']


    h1.cmd('tc qdisc del dev h1-eth root')
    h1.cmd('tc qdisc add dev h1-eth root fq')
    h2.cmd('tc qdisc del dev h2-eth root')
    h2.cmd('tc qdisc add dev h2-eth root fq')

    hosts = [h1, h2, h3]
    for i in range(1,4):
        hosts[i-1].cmd('ip route add 10.0.{}.1/32 dev h{}-eth'.format(i,i))
        for j in range(1,4):
            if j != i:
                hosts[i-1].cmd('ip route add 10.0.{}.0/24 via 10.0.{}.1'.format(j,i))
        r.cmd('ifconfig r-eth{} inet 10.0.{}.1'.format(i,i))
        r.cmd('route add 10.0.{}.10 dev r-eth{}'.format(i,i))
    for h in [r, h1, h2, h3]: h.cmd('/usr/sbin/sshd')

    
    h3.cmd('python3 hello.py>>tt.txt&')
    h3.cmd('netcat -l 5433&')
    h3.cmd('netcat -l 5434&')
    h1.cmd('python3 randomtelnet.py 10.0.3.10 5433&')
    h2.cmd('python3 randomtelnet.py 10.0.3.10 5434&')
    #CLI( net)
    h3.cmd('python3 dualreceive.py>>ttt.txt&')
    #CLI(net)
    h1.cmd('netcat -l 2345&')
    h1.cmd('python3 sender.py 100 10.0.3.10 5430 reno&')
    h2.cmd('netcat -l 2345&')
    h2.cmd('python3 sender.py 100 10.0.3.10 5431 vegas&')
    r.cmd('echo hello | netcat 10.0.1.10 2345&')
    r.cmd('echo hello | netcat 10.0.2.10 2345&')
    net.stop()

setLogLevel('info')
main()

"""
This leads to a queuing hierarchy on r with an htb node, 5:0, as the root qdisc. 
The class below it is 5:1. Below that is a netem qdisc with handle 10:, with delay 110.0ms.
We can change the limit (maximum queue capacity) with:

	tc qdisc change dev r-eth1 handle 10: netem limit 5 delay 110.0ms

"""
