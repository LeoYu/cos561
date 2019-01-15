from sys import argv
import random
N = 15
M = 10
K = 15
C = 1
BWL = 20
BWR = 40
DL = 10
DR = 20
filename = 'default.topo'
random.seed(11)

def findSet(i):
    if f[i] == i:
        return i
    else:
        f[i] = findSet(f[i])
        return f[i]

if len(argv) > 1:
    filename = argv[1]
file = open(filename, 'w')
file.write('{} {} {} {}\n'.format(N + C - 1, M, K + N + C - 1, 100))
for i in range(N + C - 1):
    file.write('h{}\n'.format(i + 1))
for i in range(M):
    file.write('s{}\n'.format(i + 1))

while True:
    f = range(M)
    dic = {}
    edgex = []
    edgey = []
    for i in range(K):
        x = random.randint(0, M - 1)
        y = random.randint(0, M - 1)
        while (x == y or (x,y) in dic):
            x = random.randint(0, M - 1)
            y = random.randint(0, M - 1)
        dic[(x,y)] = 1
        edgex.append(x)
        edgey.append(y)
        if x < y:
            f[y] = x
        else:
            f[x] = y
    connect = True
    for i in range(M):
        if findSet(i) != 0:
            connect = False
            break
    if connect:
        break

for i in range(K):
    file.write('s{} s{} {} {}ms\n'.format(edgex[i] + 1, edgey[i] + 1, random.randint(BWL, BWR), random.randint(DL, DR)))

for i in range(N):
    if i > 0:
        file.write('h{} s{} {} {}ms\n'.format(i + C, random.randint(1, M), 80, 5))

for i in range(C):
        file.write('h{} s{} {} {}ms\n'.format(i + 1, 1, 80, 5))
file.close()