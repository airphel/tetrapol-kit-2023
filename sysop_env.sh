# SysOp environment hack
# usage: . ./sysop_env.sh

export GNURADIO_HOME=/home/tomash/x/gnuradio/run/
export PYTHONPATH=$GNURADIO_HOME/lib/python3/dist-packages
export LD_LIBRARY_PATH=$GNURADIO_HOME/lib/
export GR_SCHEDULER=STS

./demod/demod.py -a "file=data/391.cfile,freq=391e6,rate=2e6,repeat=false,throttle=false" -s 2000000 -f 391000000 -t 916380 -o data/391916380.bit
