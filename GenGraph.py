import random
import os
import simplejson
import sys

import swlib

def TaskId(node,tsize):
    """
    return the task id for a node
    """

    return node/tsize

def GenGraph(sw):
    """
    generate the graph edges
    """

    # extract the stubs from the args
    # iterate through the input queue and add new items to the stub list

    taskname = sw.GetName()

    msglist = sw.GetMsgList()
    sw.flog.write("msglist " + str(msglist) + "\n")
    sw.flog.flush()

    stubs = []
    for item in msglist:
        msg = sw.GetMsg(item)

        l = simplejson.loads(msg)
        sw.flog.write("task %s, args %s\n" % (taskname, str(l)))
        sw.flog.flush()

        stubs.extend(l)

    #print taskname,stubs

    # randomize the items
    random.shuffle(stubs)
    #print taskname + "-r",stubs

    # get the pairs
    pairs = zip(stubs[::2], stubs[1::2])
    #print taskname,pairs

    # nodes in each task
    tsize = sw.GetRange()

    # get edges for a specific task
    edges = {}
    for pair in pairs:
        esrc = pair[0]
        edst = pair[1]

        # add the edge twice for both directions
        tdst = TaskId(esrc, tsize)
        if not edges.has_key(tdst):
            edges[tdst] = []
        l = [esrc, edst]
        edges[tdst].append(l)

        tdst = TaskId(edst, tsize)
        if not edges.has_key(tdst):
            edges[tdst] = []
        l = [edst, esrc]
        edges[tdst].append(l)

    #print taskname,edges

    for tdst, msgout in edges.iteritems():
        sw.flog.write("sending task %d, msg %s" % (tdst, str(msgout)) + "\n")
        sw.flog.flush()
        sw.Send(tdst, msgout)

def Worker(sw):
    GenGraph(sw)

if __name__ == '__main__':
    
    sw = swlib.SnapWorld()
    sw.Args(sys.argv)

    #flog = sys.stdout
    fname = "log-swwork-%s.txt" % (sw.GetName())
    flog = open(fname,"w")

    sw.SetLog(flog)
    sw.GetConfig()

    Worker(sw)

    flog.write("finished\n")
    flog.flush()

