#!/usr/bin/python3
# generates exponentially random traffic
# sleep...send...sleep...send...

from socket import *
from sys import argv
import os
import time
import threading
import math
import random

#default_host = "localhost"
portnum = 5433
density = 0.01  	# fraction of bottleneck link used by this traffic
packetsize = 210	# consider larger than real telnet
BottleneckBW = 10	# mbps
# BottleneckBW = 0.2	# should yield mean spacing of 1.0 sec

def talk():
        if len(argv)>=1:
            seed = argv[1]
        if len(argv)>=2:
            host = argv[2]
        if len(argv)>=3:
            portnum = int(argv[3])
        if len(argv) >= 4:
            multiplier = float(argv[4])

        random.seed(seed)
        density = multiplier * random.randint(1, 5) * 0.01

        #global default_host, portnum, density, packetsize
        rhost = host
        print("Looking up address of " + rhost + "...", end="")
        try:
            dest = gethostbyname(rhost)
        except gaierror as mesg:
            errno,errstr=mesg.args
            print("\n   ", errstr);
            return;
        print("got it: " + dest)
        addr=(dest, portnum)
        s = socket()
        try:
            s.connect_ex(addr)
        except:
            print("connect to port ", portnum, " failed")
            return

        buf = bytearray(os.urandom(packetsize))

        meanspacing = spacing(BottleneckBW, density)

        rt = time.time()
        while True:
            rt = rt + rtime(meanspacing)
            time.sleep(max(0, rt - time.time()))
            try:             s.send(buf)
            except: return

def spacing(mbps, density):
    global packetsize
    # megabit/sec = kbit/ms
    # time to send 1:
    sizeKB = (packetsize+40.0)/1000
    timetosend = sizeKB*8.0/mbps	# in ms
    return timetosend/density/1000.0
        
# ms is the mean packet spacing in units of ms
def rtime(ms):
    x = random.random()
    return -math.log(x)*ms
                
talk()
