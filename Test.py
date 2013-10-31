import os
import sys
import random


prime = []

var_node = 0
var_range = 0
var_stat_tasks = 0
var_gen_tasks = 0
var_drange = 0

candidate = []

def Search(base, coun, x, y):
    if (x >= len(base)):
        candidate.append(y)
        return
    for i in range(0, coun[x] + 1):
        Search(base, coun, x + 1, y * (base[x] ** i))

def GenCandidate(x):
    base = []
    coun = []
    for i in range(len(prime)):
        if (prime[i] > x):
            break
        if ((x / prime[i]) * prime[i] == x):
            base.append(prime[i])
            coun.append(0)
            while ((x / prime[i]) * prime[i] == x):
                coun[len(coun) - 1] += 1
                x /= prime[i]
    Search(base, coun, 0, 1)


def GenPrime(x):
    ret = []
    b = []
    for i in range(x + 1):
        b.append(True)
    b[0] = False
    b[1] = False
    for i in range(x + 1):
        if (b[i] == True):
            ret.append(i)
            j = 2
            while (j * i <= x):
                b[j * i] = False
                j += 1
    return ret

def GenConfigFile(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange):
    config = open(sys.argv[1], 'r')
    dat = []
    try:
        for line in config:
            dat.append(line)
    finally:
        config.close()
    config = open(sys.argv[1], 'w')
    try:
        for line in dat:
            line = line.strip(" ").strip("\t")
            if (len(line) > 0):
                if (line[0] != '#' and line.find("var") >= 0 and line.find("node") >= 0):
                    line = line.replace(''.join(x for x in line if x.isdigit()), str(var_node))
                if (line[0] != '#' and line.find("var") >= 0 and line.find("range") >= 0):
                    line = line.replace(''.join(x for x in line if x.isdigit()), str(var_range))
                if (line[0] != '#' and line.find("var") >= 0 and line.find("stat_tasks") >= 0):
                    line = line.replace(''.join(x for x in line if x.isdigit()), str(var_stat_tasks))
                if (line[0] != '#' and line.find("var") >= 0 and line.find("gen_tasks") >= 0):
                    line = line.replace(''.join(x for x in line if x.isdigit()), str(var_gen_tasks))
                if (line[0] != '#' and line.find("var") >= 0 and line.find("drange") >= 0):
                    line = line.replace(''.join(x for x in line if x.isdigit()), str(var_drange))
            config.write(line)
    finally:
        config.close()

def Run(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange):
    #    os.system("rake cleanup; rake test")
    os.system("grep \"\[master\]\" /afs/cs.stanford.edu/u/senwu/lfs/master.log > tmp.txt")
    input = open('tmp.txt', 'r')
    st = ""
    for dat in input:
        st = dat
    st = st.split(" ")
    output = open("test.log", "a")
    try:
        output.write("%d\t%d\t%d\t%d\t%d\t%s" % (var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange, st[len(st) - 2]))
        output.flush()
    finally:
        output.close()

if __name__ == '__main__':
    num = int(sys.argv[3])
    var_node = int(sys.argv[2])
    prime = GenPrime(var_node)
    GenCandidate(var_node)
    candidate = sorted(candidate)
    print candidate
    
    for var_range in candidate:
        for var_stat_tasks in candidate:
            var_gen_tasks = var_node / var_range
            var_drange = var_node / var_stat_tasks
            if (var_range >= 100 and var_drange >= 100):
                if (num == 1):
                    print var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange
                GenConfigFile(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange)
                num -= 1
            if num == 0:
                exit(0)
    #            Run(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange)
    print "Test done!"

