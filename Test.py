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
            if (len(line) > 0 and len(line.split()) > 1 and line.split()[0] == 'var'):
                line_arr = line.split()
                if (line_arr[0] == 'var' and line_arr[1] == 'nodes'):
                    line = "var    nodes     %s\n" % str(var_node)
                if (line_arr[0] == 'var' and line_arr[1] == 'range'):
                    line = "var    range     %s\n" % str(var_range)
                if (line_arr[0] == 'var' and line_arr[1] == 'stat_tasks'):
                    line = "var    stat_tasks     %s\n" % str(var_stat_tasks)
                if (line_arr[0] == 'var' and line_arr[1] == 'gen_tasks'):
                    line = "var    gen_tasks     %s\n" % str(var_gen_tasks)
                if (line_arr[0] == 'var' and line_arr[1] == 'drange'):
                    line = "var    drange     %s\n" % str(var_drange)
            config.write(line)
    finally:
        config.close()

def Run(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange):
    os.system("sleep 5")
    os.system("rake cleanup; rake test")
    os.system("grep \"\[master\]\" /afs/cs.stanford.edu/u/$USER/lfs/$USER/master.log > tmp.txt")
    input = open('tmp.txt', 'r')
    st = ""
    for dat in input:
        st = dat
    st = st.split(" ")
    output = open("test.log", "a")
    try:
        data = "%d\t%d\t%d\t%d\t%d\t%s" % (var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange, st[len(st) - 2])
        output.write(data + "\n")
        output.flush()
    finally:
        output.close()

if __name__ == '__main__':
    num = int(sys.argv[3])
    var_node = int(sys.argv[2])
    prime = GenPrime(var_node)
    GenCandidate(var_node)
    candidate = filter(lambda x: x%5000 == 0, sorted(candidate))
    print candidate
    
    for var_range in candidate:
        for var_drange in candidate:
            var_gen_tasks = var_node / var_range
            var_stat_tasks = var_node / var_drange
            if (var_range >= 20000 and var_drange >= 20000):
                if (num == 1):
                    print var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange
                print >> sys.stderr,  var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange
                GenConfigFile(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange)
                Run(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange)
    print "Test done!"

