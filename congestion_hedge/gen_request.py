from sys import argv
import random
N = 3
Q = 10
PL = 100
PR = 500
TL = 4
TR = 6
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
    t = t + random.uniform(TL, TR)
    file.write('{} h1 h{} {} {}\n'.format(t, h + 1, port[h] + 5400, random.randint(PL, PR)))
file.close()