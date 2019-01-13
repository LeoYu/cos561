# copyright 2017 Peter Dordal and Ihab Alshaikhli
# licensed under the Apache 2.0 license
 
"""multitrunk12: 1 hosts at each end, with 2 trunk connections::

           s1--------------------s3  
          /                        \
    h1--s5                          s6--h2
          \                        /
           s2--------------------s4  

	s1-s4: trunk switches
	s5,s6: entry/exit switches

(This is the picture with N=1 hosts at each end and K=2 trunk lines in the middle.
N and K can be changed, but results are not guaranteed. 
Though, actually, nothing in this file is guaranteed.)
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import Node, Host, OVSSwitch, OVSKernelSwitch, Controller, RemoteController, DefaultController
from mininet.cli import CLI
from mininet.log import setLogLevel
import argparse

BANDWIDTH=20		 # in megabits per second

class TrunkNKTopo( Topo ):
    "Two clusters of N hosts each, joined by K trunk lines."

    def __init__( self , **kwargs):
        super(TrunkNKTopo, self).__init__(**kwargs)
        h = []
        s = []

        N=1
        K=2
        for key in kwargs:	# allow keyword specification of N and K
           if key == 'N':
               N=kwargs[key]
           if key == 'K':
               K=kwargs[key]

        # add 2K trunk switches
        # trunk switches with i=1 and i=K+1 are the "primary" path from left to right
        for i in range(1, 2*K+1):
           s += [self.addSwitch('s' + str(i))]

        # add 2N entry/exit switches
        for i in range(2*K+1, 2*K+2*N+1):
           s += [self.addSwitch('s' + str(i))]

        # add trunk links
        for i in range(K):
            self.addLink(s[i], s[i+K], bw=BANDWIDTH) 	# recall s1 is s[0], etc

        # link the si trunk switches to the sj entry/exit switches, at both left and right sides:
        for i in range(N):
            for j in range(K):
                self.addLink(s[2*K+i],s[j], bw=BANDWIDTH)
                self.addLink(s[2*K+N+i],s[K+j], bw=BANDWIDTH)

        # now add the 2N hosts
        for i in range(1, 2*N+1):
           h += [self.addHost('h' + str(i))]

        # Add links from each hi to its corresponding entry/exit switch sj
        for i in range(N):
           self.addLink(h[i], s[2*K+i], bw=BANDWIDTH)
           self.addLink(h[N+i], s[2*K+N+i], bw=BANDWIDTH)

	c = RemoteController( 'c', ip='127.0.0.1', port=6633 )


topos = { 'trunkNK': ( lambda **kwargs: TrunkNKTopo(**kwargs) ) }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-N', '--N', type=int)
    parser.add_argument('-K', '--K', type=int)
    args = parser.parse_args()
    N=1		# the defaults
    K=2
    if args.N is not None:
        N = args.N
    if args.K is not None:
        K = args.K
    trunktopo = TrunkNKTopo(N=N,K=K)

    net = Mininet(topo = trunktopo, switch = OVSKernelSwitch, 
                controller = RemoteController,
		autoSetMacs = True,
		link = TCLink		# this kind of link can have a BANDWIDTH
                )
    c = RemoteController( 'c', ip='127.0.0.1', port=6633 )
    net.addController(c)
    net.start()

    for i in range(1, 2*N+1):
       hi = net['h' + str(i)]
       hi.cmd('/usr/sbin/sshd')
       # hi.cmd('/bin/nc -kl 5432  >/dev/null 2>&1 &')		# may not work as expected
 
    CLI( net)
    net.stop()

setLogLevel('info')	# or 'debug', etc
main()

