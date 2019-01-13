#!/usr/bin/python

# writes to stdout
# this version monitors TWO different interfaces. Output is written as (time,intf1, intf2)
# we use the same filter on both interfaces.
# dev is no longer a parameter

import pcapy
import time
import threading
import sys

# TCP HEADER FIELDS
TCP_DATAOFFSET = 12
TCP_SEQ_OFFSET = 4
TCP_ACK_OFFSET = 8
TCP_SRCPORT_OFFSET = 0
TCP_DSTPORT_OFFSET = 2
IPv4_SRC_OFFSET = 12
IPv4_DST_OFFSET = 16
port1 = 5430
port2 = 5431
seq1  = 0
ack1  = 0
seq2  = 0
ack2  = 0
starttime = -1
pktcount = 0		# count of packets
pktprev  = 0
repeats = 0
halting = False
statcount = 0
interval = 0.1
dev1 = 'r-eth1'
dev2 = 'r-eth2'

def setup():
    global dev
    #if len(sys.argv) > 1:         dev = sys.argv[1]
    cap1 = pcapy.open_live(dev1, 128, 0, 50)  # (dev, snaplen, is_promiscuous, read_timeout_ms)
    cap2 = pcapy.open_live(dev2, 128, 0, 50)
    filter = 'host 10.0.3.10 and tcp and portrange 5430-5431'
    bpf = pcapy.compile(pcapy.DLT_EN10MB, 1500, filter, 0, 0xffffff00)  # (type, max, filter, optimize?, netmask)
    cap1.setfilter(filter)
    cap2.setfilter(filter)
    return (cap1,cap2)

def process_packets1():
    global cap1, seq1, ack1, starttime, pktcount
    while True:
        _,p = cap1.next()	# exception?
        if halting: exit(0)
        if p == None or len(p) == 0:
             #print '.',
             continue;
        pktcount += 1
        if starttime == -1: 
             starttime = time.time()
             print 
             printstats()
        #print '.',
        (_,iphdr,tcphdr,data) = parsepacket(p)
	sport = int2(tcphdr, TCP_SRCPORT_OFFSET)
        dport = int2(tcphdr, TCP_DSTPORT_OFFSET)
        if dport == port1:             # get seq if dport in [port1,port2]
            seq1 = int4(tcphdr, TCP_SEQ_OFFSET) + len(data)
        elif sport == port1:
            ack1 = int4(tcphdr, TCP_ACK_OFFSET)

def process_packets2():
    global cap2, seq2, ack2, starttime, pktcount
    while True:
        _,p = cap2.next()	# exception?
        if halting: exit(0)
        if p == None or len(p) == 0:
             #print '.',
             continue;
        pktcount += 1
        if starttime == -1: 
             starttime = time.time()
             printstats()
        #print '.',
        (_,iphdr,tcphdr,data) = parsepacket(p)
	sport = int2(tcphdr, TCP_SRCPORT_OFFSET)
        dport = int2(tcphdr, TCP_DSTPORT_OFFSET)
        if dport == port2:             # get seq if dport in [port1,port2]
            seq2 = int4(tcphdr, TCP_SEQ_OFFSET) + len(data)
        elif sport == port2:
            ack2 = int4(tcphdr, TCP_ACK_OFFSET)

def parsepacket(p):
    ethhdr = p[0:14]
    p = p[14:]
    iphdrlen = (ord(p[0]) & 0x0f)*4
    iphdr = p[0:iphdrlen]
    p = p[iphdrlen:]
    tcphdrlen =  (0 + tcpheaderlen(p))*4
    tcphdr = p[0:tcphdrlen]
    #seqnum = int4(tcphdr, TCP_SEQ_OFFSET)
    #acknum = int4(tcphdr, TCP_ACK_OFFSET)
    #srcport= int2(tcphdr, TCP_SRCPORT_OFFSET)
    #dstport= int2(tcphdr, TCP_DSTPORT_OFFSET)
    p = p[tcphdrlen:]
    return (ethhdr, iphdr, tcphdr, p)

# started by whichever thread sees first packet
def printstats():
    global starttime, statcount, count, pktprev, repeats, halting  # repeats is global
    elapsed = time.time()-starttime
    if starttime != -1:
        print ('{}\t{}\t{}'.format(elapsed, seq1-ack1, seq2-ack2))
        print ('{}\t{}\t{}'.format(elapsed, seq1-ack1, seq2-ack2))
    if pktcount > 0 and pktcount == pktprev:	# quit when there's no new packets
        if repeats >= 10:
             halting=True
             exit(0)
        repeats+=1
    elif pktcount > 0:
       pktprev = pktcount
       repeats=0
       statcount +=1
    #nexttime = starttime + statcount * interval
    #inter = nexttime - time.time()
    inter = statcount * interval - elapsed
    if starttime > -1: assert inter > 0, "printstats: bad time!"
    t = threading.Timer(inter,printstats)
    t.start()


def tcpheaderlen(p):
    return (ord(p[TCP_DATAOFFSET]) >> 4)

# returns 4-byte integer from a python2 string p, from the designated location
def int4(p, offset):
    return  (((ord(p[offset])   & 0xff) << 24) |
             ((ord(p[offset+1]) & 0xff) << 16) |
             ((ord(p[offset+2]) & 0xff) <<  8) |
             ((ord(p[offset+3]) & 0xff)      ) )

# ditto but for 2-byte integer
def int2(p, offset):
    return  (((ord(p[offset])   & 0xff) << 8) |
             ((ord(p[offset+1]) & 0xff)     ) )

# takes 32-bit int and returns dotted-decimal string
def dd(ipv4num):
    b4 = (ipv4num & 0xff)
    ipv4num >>= 8
    b3 = (ipv4num & 0xff)
    ipv4num >>= 8
    b2 = (ipv4num & 0xff)
    ipv4num >>= 8
    b1 = (ipv4num & 0xff)
    ipv4num >>= 8
    return '{}.{}.{}.{}'.format(b1,b2,b3,b4)

# converts dotted-decimal ipv4 address to 32-bit integer
def dd_to_int(dd):
    ints = map(int, dd.split('.'))
    addr = 0
    for i in range(4):
        addr += ints[i]
        if i < 3: addr <<= 8
    return addr

(cap1,cap2) = setup()
th1 = threading.Thread(target=process_packets1, name="interface1")
th2 = threading.Thread(target=process_packets2, name="interface2")
th1.start()
th2.start()
#printstats()