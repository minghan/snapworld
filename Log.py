import os
import sys
import random
input = open('tmp.txt', 'r')
st = ""
for dat in input:
    st = dat
st = st.split(" ")
output = open("test.log", "a")
try:
    output.write("%s\t%s\n" % (sys.argv[1], st[len(st) - 2]))
    output.flush()
finally:
    output.close()

