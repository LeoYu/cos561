from socket import *
from sys import argv,exit
import sys
import threading
from select import *
import time



def listen():
    portnum = int(argv[1])
    start_time = float(argv[2])

    print 'start'
    sys.stdout.flush()
    ss = socket(AF_INET, SOCK_STREAM)
    ss.bind(('', portnum))            # INADDR_ANY = ''
    #time.sleep(max(0,start_time - time.time()-1)) # wake up 0.5 sec before the scheduled time 
    ss.listen(5)

    (cs, address) = ss.accept()


    print('accepted connections from {}:{} at time {}'.format(address, portnum, time.time()))
    sys.stdout.flush()
    #f.write('accepted connections\n')

    true_start_time = time.time()

    sset = [cs]

    while True:
        if sset == []: exit(0)
        sl,_,_ = select(sset, [], [])
        for s in sl:
             try:
                 mesg = s.recv(2048)
             except Exception as e:
                print('error: {} ({})'.format(e.errno, e.strerror))
             c = len(mesg)
             if c == 0: 
                 print('closing socket connected to {}'.format(address))
                 #f.write('closing socket connected to {}\n'.format(address1 if s==cs1 else address2))
                 sset.remove(cs)
                 if sset == []: exit(0)     # exit when no more open sockets
        
listen()