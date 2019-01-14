
from sys import argv
import sys
import numpy as np
import time
import fcntl,socket
import os

cong_alg_map = {0: 'reno', 
				1: 'cubic',
				2: 'vegas'}
def send():
	if len(argv)>=1:
		blockcount = int(argv[1])
	if len(argv)>=2:
		host = argv[2]
	if len(argv)>=3:
		portnum = int(argv[3])
	if len(argv)>=4:
		start_time = float(argv[4])
	if len(argv)>=5:
		lr = float(argv[5])


	time.sleep(max(0,-time.time()+start_time))
	f =open('history.txt','r')
	while True:
		try:
			fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
			break
		except IOError as e:
		# raise on unrelated IOErrors
			if e.errno != errno.EAGAIN:
				raise
			else:
				time.sleep(0.1)
	i = 0
	history = np.zeros(3)            	
	for line in f:
		history[i] = float(line)
		i = i+1
	fcntl.flock(f, fcntl.LOCK_UN)
	f.close()

	score = history
	score = score - np.min(score)
	score = np.exp(lr*score)
	score = score *1.0/ sum(score)
	choice = int(np.random.choice(range(0,3), 1, p=score))

	cong_alg = cong_alg_map[choice]

	print("Looking up address of " + host + "...")
	sys.stdout.flush()
	try:
		dest = socket.gethostbyname(host)
	except socket.gaierror as mesg:
		errno,errstr=mesg.args
		print("\n   " + errstr);
		return;
	print("got it: " + dest)
	addr=(dest, portnum)
	print addr
	s = socket.socket()
	print cong_alg
	sys.stdout.flush()
	#IPPROTO_TCP = 6        	# defined in /usr/include/netinet/in.h
	TCP_CONGESTION = 13 	# defined in /usr/include/netinet/tcp.h
	#cong = bytes(cong_alg, 'ascii')
	cong = cong_alg
	try:
	   s.setsockopt(socket.IPPROTO_TCP, TCP_CONGESTION, cong)
	except OSError as mesg:
		errno, errstr = mesg.args
		print ('congestion mechanism {} not available: {}'.format(cong_algorithm, errstr))
		return
	num_attepmt = 0
	res=s.connect_ex(addr)
	while res!=0 and num_attepmt <= 10: 
		print "connect to port ", portnum, " failed"
		time.sleep(0.1)
		res=s.connect_ex(addr)
		num_attepmt = num_attepmt +1
		return

	buf = bytearray(os.urandom(1000))
	true_start_time = time.time()
	for i in range(blockcount):
		s.send(buf)
	s.close()
	duration = time.time()-true_start_time
	throughput = blockcount*1.0/duration  # KB/s
	print('total time: {} seconds'.format(duration))

	history[choice] = history[choice] + throughput/score[choice]

	f = open('history.txt','w')
	while True:
		try:
			fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
			break
		except IOError as e:
			# raise on unrelated IOErrors
			if e.errno != errno.EAGAIN:
				raise
			else:
				time.sleep(0.1)
	for x in history:
		f.write('{}\n'.format(x))
	fcntl.flock(f, fcntl.LOCK_UN)
	f.close()

send()



