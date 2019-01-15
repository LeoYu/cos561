from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch, Controller, RemoteController, DefaultController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from sys import argv
import numpy as np
import time,cmd,random,os.path, datetime

m =0
n =0
density = 10
lr = 0.0001
fix_choice = -1
max_thrpt = 1000

class RTopo(Topo):
    #def __init__(self, **kwargs):
    #global r
    def build(self, **_opts):     # special names?
        global m, n
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
            #self.addLink(dic[x], dic[y])
            self.addLink(dic[x], dic[y], bw = bw, delay = delay, queue = queue)


def main():
    global lr, density,fix_choice,max_thrpt
    if len(argv) >3:
        density = argv[3]
    if len(argv) > 4:
        fix_choice = int(argv[4])
    if len(argv) > 5:
        lr = float(argv[5])
    if len(argv) >6:
        max_thrpt = float(argv[6])
    timestamp =  datetime.datetime.fromtimestamp(time.time()).strftime('_%H_%M_%S')
    log = 'lr'+ str(lr) + 'alg' + str(fix_choice)+ timestamp+ '.log'

    rtopo = RTopo()
    net = Mininet(topo = rtopo,
                   link=TCLink,
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

    K = 3
    f = open(log, 'w')
    for i in range(K):
        f.write('0\n')
    f.write('@')
    f.close()
    request_file = "default.req"
    if len(argv)> 2:
        request_file = argv[2]
    f = open(request_file,'r')
    num = int(f.readline())
    cmd.Cmd('sudo rm sender.txt')
    for i in range(1,n+1):
        cmd.Cmd('sudo rm h{}.txt'.format(i))


    net.start()

    time.sleep(10)
    random.seed(7)
    for i in range(1,n+1):
        for j in range(1,n+1):
            if i!= j and random.random() > 0.9:
                host1 = 'h'+str(i)
                host2 = 'h'+ str(j)
                net[host2].cmd('sudo python2 ../receive.py {} {} 2>&1>>{}.txt&'.format(4000+i, 0, 'noise'+host2))
                net[host1].cmd('sudo python2 ../randomtraffic.py {} {} {} {} 2>&1 >> {}.txt&'.format(random.randint(1,100), net[host2].IP(), 4000+i, density, 'traffic'+host1))
    time.sleep(4)

    time0 = time.time()
    for i in range(num):
        starttime, host1, host2, portnum, packagesize = f.readline()[:-1].split()
        starttime = float(starttime) + time0 
        net[host2].cmd('sudo python2 ../receive.py {} {} 2>&1>>{}.txt &'.format(portnum, starttime, host2))
        net[host1].cmd('sudo python2 ../send.py {} {} {} {} {} {} {} {} 2>&1 >>sender{}.txt&'.format(packagesize,net[host2].IP(), portnum, starttime, lr, lr*max_thrpt, fix_choice, log, fix_choice))
    f.close()

    # hosts =[] 
    # for i in range(2,4):
    #     hosts.append('h'+str(i))
    # portnum = range(5000+2,5000+4)
    # schedule = np.array(range(2,4))+ time.time() #time 

    # #print(type(net['h1']))
    # for t in range(0,2):
    #     net[hosts[t]].cmd('python2 receive.py {} {} 2>&1>>{}.txt &'.format(portnum[t], schedule[t], hosts[t]))
    #     net['h1'].cmd('python2 send.py {} {} {} {} {} 2>&1 >>sender.txt&'.format(100,net[hosts[t]].IP(), portnum[t], schedule[t], 0.1))
    #     tprint net[hosts[t]].IP()
    while True:
        if os.path.isfile(str(num)+".kill"):
            cmd.Cmd('sudo rm *.kill')
            break
        else:
            time.sleep(0.5)
    net.stop()

setLogLevel('debug')
main()

"""
This leads to a queuing hierarchy on r with an htb node, 5:0, as the root qdisc. 
The class below it is 5:1. Below that is a netem qdisc with handle 10:, with delay 110.0ms.
We can change the limit (maximum queue capacity) with:

    tc qdisc change dev r-eth1 handle 10: netem limit 5 delay 110.0ms

"""
