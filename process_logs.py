def get_3d_plot(filename):
    v = []
    with open(filename) as f:
        for l in f:
            nodes, r, st, gt, dr, t = l.split()
            v.append((r,dr,t))
    with open('3d_%s' % filename, 'w') as f:
        for r, dr, t in v:
            f.write("%s %s %s\n" % (r, dr, t))
    print "Generated 3d_%s" % filename

get_3d_plot('test.log')
