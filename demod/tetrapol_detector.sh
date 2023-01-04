#!/bin/sh

# Center frequency of tunner
FREQ=393e6

# RX Gain
GAIN=30.4

# Channels processed in paralel, accustome to your CPU speed
MAX_CHANNELS=8

# Scan results and channel recordings are stored here
OUT_DIR=tmp

# SDR sample rate, accustom to your SDR device
SAMP_RATE=2400000

# Length of channel RX records in seconds, use 0 for infinity
TIMEOUT=30

# File where is stored list of TETRAPOL channel candidates
CHANNELS_FILE=channels.json

# TETRAPOL channel band width, 12500 or 10000
CH_BW=12500


if ! [ -d "${OUT_DIR}" ]; then
    echo "OUT_DIR (${OUT_DIR}) does not exist"
    exit 1
fi

echo "Detecting TETRAPOL channels"
python3 tetrapol_detector.py \
    -f ${FREQ} \
    -B ${CH_BW} \
    -g ${GAIN} \
    -i osmo-sdr:// \
    -o "${OUT_DIR}/${CHANNELS_FILE}"  \
    -r 1 \
    -s ${SAMP_RATE}

FREQS=`grep freq tmp/channels.json  | sed -e 's/.*freq": //' -e 's/\\..*//' | head -n ${MAX_CHANNELS} | tr \\\\012 ,`

echo "Receiving selected TETRAPOL channels"
timeout ${TIMEOUT} \
    python3 demod.py \
        -g ${GAIN} \
        -s ${SAMP_RATE} \
        -B ${CH_BW} \
        -o ${OUT_DIR}/channel%%.bits \
        -l "${FREQS}"

for f in `echo "${FREQS}" | tr , ' '`; do
    ../build/apps/tetrapol_dump -t CCH -i ${OUT_DIR}/channel${f}.bits \
            >${OUT_DIR}/cch_${f}.json 2>${OUT_DIR}/cch_${f}.log
    ../build/apps/tetrapol_dump -t TCH -i ${OUT_DIR}/channel${f}.bits \
            >${OUT_DIR}/tch_${f}.json 2>${OUT_DIR}/tch_${f}.log
done
