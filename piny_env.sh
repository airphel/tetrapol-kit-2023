#!/bin/sh

./demod/tetrapol_rx.py -f 393e6 -p 37 -g 40 -s 2000000 -o ../tetrapol_samples/rec/channel%d.bits &

sleep 8
./demod/tetrapol_cli_pwr.py | head -n 30


echo './demod/tetrapol_cli_output_enabled.py open '
echo './demod/tetrapol_cli_auto_tune.py'
echo './demod/tetrapol_cli_pwr.py | head -n 30'
echo 'killall python2.7'
echo 'find ../tetrapol_samples/rec/ -size 0 -exec rm \{\} \;'
echo 'for f in ../tetrapol_samples/rec/channel*.bits; do echo $f; ./apps/tetrapol_dump -i $f; done | vimpager'
echo 'for f in ../tetrapol_samples/rec/channel*.bits; do cat $f | tr \001 1 >$f.oct; done'