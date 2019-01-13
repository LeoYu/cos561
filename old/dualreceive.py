#!/usr/bin/python3

from socket import *
from sys import argv,exit,stderr
import threading
from select import *
import time

portnum1 = 5430		# h1 sends to this
portnum2 = 5431
count1 = 0
count2 = 0
prev1 = 0
prev2 = 0
repeats = 0
interval = 0.1
halting = False
# interval = 1
starttime = 0
statcount = 0	# number of times printstats has been called
thresh_increment =  2000000	# in bytes
print_thresh = thresh_increment
# If the following is True, printstats() prints the number of bytes since the start. 
# If the following is False, printstats() prints the number of bytes received
# since the previous call. If True, printed bytecounts are cumulative.
PRINT_CUMULATIVE = True		

def listen():
    global portnum1, portnum2, count1, count2, starttime, print_thresh
    if len(argv) > 1:
        rhost = argv[1]
    if len(argv) > 2:
        cong_algorithm = argv[2]

    ss1 = socket(AF_INET, SOCK_STREAM)
    ss1.bind(('', portnum1))			# INADDR_ANY = ''
    ss1.listen(5)

    ss2 = socket(AF_INET, SOCK_STREAM)
    ss2.bind(('', portnum2))			# INADDR_ANY = ''
    ss2.listen(5)

    (cs1, address1) = ss1.accept()
    cs2 = 0
    (cs2, address2) = ss2.accept()

    print('accepted connections', file=stderr)

    count1 = count2 = 0

    starttime = time.time()
    printstats()		# first call

    sset = [cs1, cs2]

    while True:
        if sset == []: exit(0)
        sl,_,_ = select(sset, [], [])
        for s in sl:
             try:
                 mesg = s.recv(2048)
             except Exception as e:
                  print('error: {} ({})'.format(e.errno, e.strerror), file=stderr)
             c = len(mesg)
             if c == 0: 
                 print('closing socket connected to {}'.format(address1 if s==cs1 else address2), file=stderr)
                 if s==cs1: sset.remove(cs1)
                 else: sset.remove(cs2)
                 if sset == []: exit(0)		# exit when no more open sockets
             if s == cs1:   count1 += c
             elif s == cs2: count2 += c
             else: print ("something is not right:", c)
             if halting: exit(0)
             if count1+count2 > print_thresh:
                 print_thresh += thresh_increment;
                 print('dualreceive: data total is {}'.format(count1+count2), file=stderr)
        

def printstats():
    global count1, count2, prev1, prev2, interval, repeats, halting, starttime, statcount
    elapsed = time.time()-starttime
    if PRINT_CUMULATIVE:
        print ('{}\t{}\t{}'.format(elapsed, count1, count2))
    else:
        print ('{}\t{}\t{}'.format(elapsed, count1-prev1, count2-prev2))
    if (count1,count2) == (prev1,prev2):	# quit when there's no change in stats
        if repeats >= 10:
             halting=True
             exit(0)
        repeats+=1
    else:
       (prev1,prev2) = (count1,count2)
       repeats=0
    statcount +=1
    #nexttime = starttime + statcount * interval
    #inter = nexttime - time.time()
    inter = statcount * interval - elapsed
    assert inter > 0, "printstats: bad time!"
    t = threading.Timer(inter,printstats)
    t.start()
    
        
listen()