# pld: single trunk topology, righthand servers selected via round-robin

"""
  ./pox.py log.level --INFO forwarding.loadbalancepox 

The --N=3 option is the default.

   h1..              ..t1
   h2.....r-------s....t2
   h3..              ..t3

TCP connection routes are chosen within the PacketIn handler.
ARP traffic is suppressed by the use of static ARP entries.
"""

from pox.core import core
from pox.lib.addresses import EthAddr
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.revent import EventRemove
import pox.lib.util as util

TCPstarted = False	# flag used to identify start of TCP traffic, which generally comes AFTER all hosts have been identified

BROADCAST = EthAddr('ff:ff:ff:ff:ff:ff')

SLEEPTIME = 10		# time in seconds

ICMP_IDLE_TIMEOUT = 0
TCP_IDLE_TIMEOUT  = 0 	# Zero means entries do not expire

# pld: should get N and K from the command line

N=3
K=1


# represents a one-way flow, including ethernet and IPv4 addresses and TCP ports.
class Flow:
    def __init__(self, ethsrc, ethdst, srcip, dstip, srcport, dstport):
        self.ethsrc = ethsrc
        self.ethdst = ethdst
        self.srcip  = srcip
        self.dstip  = dstip
        self.srcport= srcport
        self.dstport= dstport
    def reverse(self):
        return Flow(self.ethdst, self.ethsrc, self.dstip, self.srcip, self.dstport, self.srcport)
    def __str__(self):
        return '({},{},{},{})'.format(self.srcip, self.dstip, self.srcport, self.dstport)

    def __hash__(self):
        return hash((self.ethdst, self.ethsrc, self.dstip, self.srcip, self.dstport, self.srcport))
    def __eq__(self, other):
        return self.ethsrc == other.ethsrc and self.ethdst == other.ethdst and self.srcip == other.srcip and self.dstip == other.dstip and self.srcport == other.srcport      
    def crosses(self):
        if hostnum(self.ethsrc) <= N and hostnum(self.ethdst) > N: return True
        if hostnum(self.ethsrc) > N and hostnum(self.ethdst) <= N: return True
        return False        
    def top_to_bottom(self):
        if hostnum(self.ethsrc) <= N and hostnum(self.ethdst) > N: return True
        return False
     
def printpath(path):
    plen = len(path)
    for i in range(plen):
        node = path[i]
        if type(node) is EthAddr: node = 'h'+str(hostnum(node))
        print node,
    print

# main dictionaries

flow_to_server = {}   # map of Flows to the number of the ti the flow connects to.

log = core.getLogger()


########### _handle_ConnectionUp  ##################

def _handle_ConnectionUp (event):
    # Initialize the forwarding rules for this switch.
    # We create forwarding rules in s so that ICMP traffic from the left side 
    # is always sent to t1. We're hoping it's just pings, and not something important.

    connection = event.connection
    dpid = connection.dpid
    print "handle_ConnectionUP from dpid", dpid, util.dpid_to_str(dpid)
    # Clear first table
    msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)
    connection.send(msg)
    # 
    imsg1 = of.ofp_flow_mod()
    imsg2 = of.ofp_flow_mod()

    imsg1.match.dl_type = pkt.ethernet.IP_TYPE
    imsg2.match.dl_type = pkt.ethernet.IP_TYPE

    imsg1.match.nw_proto = pkt.ipv4.ICMP_PROTOCOL
    imsg2.match.nw_proto = pkt.ipv4.ICMP_PROTOCOL

    imsg1.match.in_port = 1
    imsg2.match.in_port = 2

    imsg1.actions.append(of.ofp_action_output(port = 2))
    imsg2.actions.append(of.ofp_action_output(port = 1))

    connection.send(imsg1)
    connection.send(imsg2)
    print 'sent ICMP actions'

    def ready (event):		# called right below, as parameter
        if event.ofp.xid != 0x80000000:
            # Not the right barrier
            return
        log.info("%s ready", event.connection)
        event.connection.addListenerByName("PacketIn", _handle_PacketIn)
        return EventRemove

    connection.send(of.ofp_barrier_request(xid=0x80000000))
    connection.addListenerByName("BarrierIn", ready)


########  _handle_PacketIn  #######################

# PacketIn should tell us what switch ports connect to HOSTS 

TCPflows = []		# list of TCP connections starting at lefthand/upper side

def _handle_PacketIn (event):
    global TCPstarted, flow_to_server, known_hosts
    packet = event.parsed
    packet_in = event.ofp	 # The actual ofp_packet_in message.
    inport = packet_in.in_port	# is this the same as event.port?
    dpid = event.connection.dpid

    if isdhcp(packet): return		# pld: ignore DHCP traffic

    proto = packet_type(packet)

    print 's: received {} packet from {} to {} via port {}'.format(proto, packet.src, packet.dst, inport)

    if proto == 'unknown':
        print "unknown packet type:", packet.type

    if proto != 'tcp': return

    # now we know it's a TCP packet
    ipv4 = packet.find('ipv4')
    tcp  = packet.find('tcp')
    if not TCPstarted:
        TCPstarted = True
    flow = Flow(packet.src, packet.dst, ipv4.srcip, ipv4.dstip, tcp.srcport, tcp.dstport)
    server = flow_to_server.get(flow)
    if server is None:
        server = pickserver(flow)
        flow_to_server[flow] = server
    print 'adding TCP flow {} to t{}'.format(flow, server)
    # now create TCP forwarding:
    # if from r side (arriving via s port 1), forward to port serverport
    # if arriving from serverport, forward to port 1
    addTCPrule(event.connection, flow, server+1)	# ti is at port i+1
    addTCPrule(event.connection, flow.reverse(), 1)

lastServer = N		# guarantees next server assigned will be s1

def pickserver(flow):	# returns 1..N
    global lastServer
    if lastServer==N: lastServer=1
    else: lastServer+=1
    return lastServer

def packet_type(packet):
    if packet.find('icmp'): return 'icmp'
    if packet.find('arp'):  return 'arp'
    if packet.find('dhcp'): return 'dhcp'
    if packet.find('tcp'):  return 'tcp'
    if packet.find('udp'):  return 'udp'
    return 'unknown'


#######################  TCP handling ##########################

#The switch at the given connection is told that traffic matching the given flow should be sent via the given port
def addTCPrule(connection, flow, port):
    msg = of.ofp_flow_mod()
    msg.idle_timeout    = TCP_IDLE_TIMEOUT
    msg.match.dl_src    = flow.ethsrc
    msg.match.dl_dst    = flow.ethdst
    msg.match.dl_type   = pkt.ethernet.IP_TYPE
    msg.match.nw_proto  = pkt.ipv4.TCP_PROTOCOL
    msg.match.nw_src    = flow.srcip
    msg.match.nw_dst    = flow.dstip
    msg.match.tp_src    = flow.srcport
    msg.match.tp_dst    = flow.dstport
    msg.actions.append(of.ofp_action_output(port = port))
    connection.send(msg)
    


def launch (N=3,K=1):
  global st, cv
  n = int(N)
  k = int(K)
  NKsetter(n,k)
  print "N=", N, "K=", K
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
  core.openflow.addListenerByName("PacketIn", _handle_PacketIn) 

# action to be taken on receipt of first TCP packet:
# calculate routes, or print host destinations, etc

def TCPstart():
    print "TCP traffic starting"

def NKsetter(n,k):
  global N,K
  (N,K) = (n,k)

def hostswitch(i):    # host is hi
    return i+2*K

def switchpeer(i):
    if i<=K: return i+K
    return i-K

# pld utility about strange dhcp packets
def isdhcp(packet):
    dhcp = packet.find('dhcp')		# pld: doesn't work?
    if dhcp is None: return False
    return True


def hostnum(addr):   # returns, eg, x for 00:00:00:00:00:0x, 0 for other formats
   addr = addr.toStr()
   if addr[:14] == '00:00:00:00:00':
       return int(addr[15:],16)		# pld: this is a 2-byte hex string
   else:
       return 0

def ishost(addr):   # returns true for, eg, 00:00:00:00:00:0x
   addr = addr.toStr()
   if addr[:14] == '00:00:00:00:00':
      return True
   return False

