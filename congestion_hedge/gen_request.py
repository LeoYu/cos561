from sys import argv
import random
N = 3
Q = 10
PL = 10000
PR = 20000
TL = 5
TR = 10
filename = 'default.req'
random.seed(11)

if len(argv) > 1:
    filename = argv[1]
file = open(filename, 'w')
file.write('{}\n'.format(Q))
port = [0] * N
t = 0
for i in range(Q):
    h = random.randint(1, N - 1)
    port[h] = (port[h] + 1) % 100
    t = t + random.randint(TL, TR)
    file.write('{} h1 h{} {} {}\n'.format(t, h + 1, port[h] + 5400, random.randint(PL, PR)))
file.close()