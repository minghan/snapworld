import os
import sys
import random
import time

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
    os.system("rake cleanup; sleep 5")
    tb = time.time()
    os.system("timeout 20000s rake test")
    td = time.time() - tb
    print >> sys.stderr, "Took %f s" % td
    if td > 20000:
        for r in ["cpu_idle", "cpu_user", "cpu_wait", "cpu_inter", "cpu_system", "net_transmit", "net_receive", "disk_write", "disk_read"]:
            with open('%s.log' % r, 'a') as f:
                f.write("TIMEOUT\n")
                f.flush()
        with open('test.log', 'a') as o:
            data = "%d\t%d\t%d\t%d\t%d\t%s" % (var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange, "TIMEOUT")
            o.write(data + "\n")
            o.flush()
        print "TIMEOUT", var_range, var_drange
        os.system("sleep 5")
        return
    # If we don't timeout then continue to record statistics.
    os.system("grep \"\[master\]\" /afs/cs.stanford.edu/u/$USER/lfs/$USER/master.log > tmp.txt")
    fp = "ssh iln02 cat /afs/cs.stanford.edu/u/$USER/lfs/$USER/supervisors/9200/execute/supervisor-sh-9200.log | grep sys_stats |"
    for r in ["cpu_idle", "cpu_user", "cpu_wait", "cpu_inter", "cpu_system", "net_transmit", "net_receive", "disk_write", "disk_read"]:
        sys_cmd = " grep %s | awk '{print $9}' | perl -n -e '/(\d+)\)$/ && print \"$1\n\"' > %s.txt" % (r, r)
        sys_cmd = fp + sys_cmd
        print >> sys.stderr, sys_cmd
        os.system(sys_cmd)
        arr = []
        na = None
        with open('%s.txt' % r) as f:
            for l in f:
                arr.append(int(l.strip()))
        na = arr
        proc_arr = []
        for i, e in enumerate(na):
            if i == 0:
                proc_arr.append(0.0)
            else:
                proc_arr.append((na[i]-na[i-1])/5.0)
        os.system("rm %s.txt" % r)
        with open('%s.log' % r, 'a') as f:
            for e in proc_arr:
                f.write("%f " % e)
            f.write("\n")
            f.flush()
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
    var_node = int(sys.argv[2])
    prime = GenPrime(var_node)
    GenCandidate(var_node)
    candidate = filter(lambda x: x%5000 == 0, sorted(candidate))
    print candidate
    
    for var_range in candidate:
        for var_drange in candidate:
            var_gen_tasks = var_node / var_range
            var_stat_tasks = var_node / var_drange
            if (var_range <= 1000000 and var_drange <= 1600000):
                if (var_stat_tasks > 1000 or var_gen_tasks > 1000): continue
                print >> sys.stderr,  var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange
                GenConfigFile(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange)
                Run(var_node, var_range, var_stat_tasks, var_gen_tasks, var_drange)
    print "Test done!"

