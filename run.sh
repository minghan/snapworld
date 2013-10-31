#!/bin/sh
for a in `seq 447 841`
do
python Test.py snapw.config 1000000 $a
rake cleanup
rake test
grep "\[master\]" /afs/cs.stanford.edu/u/senwu/lfs/master.log > tmp.txt
python Log.py $a
echo $a
sleep 5
done
