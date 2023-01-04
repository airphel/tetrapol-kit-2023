#!/usr/bin/python3

from gnuradio import blocks
from gnuradio import fft
from gnuradio import gr
import math
import numpy as np


def mk_rect_taps(ntaps):
    """Return taps for signal with rectangular spectrum shape with
    band width ntaps/2."""
    taps = - np.ones(ntaps, dtype=np.float32)
    taps[ntaps/4:ntaps*3/4] = 1.
    return taps

def mk_cos_taps(ntaps):
    """Return taps for signal with cosine like signal spectrum shape
    with band width ntaps/2."""
    taps = [np.cos((x - (ntaps - 1.)/2) / (ntaps - 1.) *  2*np.pi) for x in range(ntaps)]
    return taps


class signal_detector_base(gr.sync_block):
    """perform channel detection on input data.
    It expects log pwr FFT as input and emits list of detected channels.
    """

    def __init__(self, samp_rate, fft_size, signal_taps, threshold,
            max_overlap=0.25, center_freq=0):
        """Taps is vector of real numbers approximating the expected shape of
        signal. Inner taps should represent signal (positive numbers) and
        taps near edge should represent noise floor (negative numbers).
        Example of simple taps: (-2, -1, 0, 1, 2, 2, 1, 0, -1, -2).
        Threshold is id dB.
        Max_overlap specifies maximal overlap of two signals (in taps)."""
        gr.sync_block.__init__(
            self, "Signal Detector Base Class",
            in_sig = [(np.float32, fft_size) ],
            out_sig=None,
        )
        self.samp_rate = samp_rate
        self.fft_size = fft_size
        self.ch_spacing = int(len(signal_taps) * (1 - max_overlap))
        self.threshold = threshold
        self.freq_offs = center_freq - samp_rate / 2
        self.point_bw = samp_rate / fft_size
# normalize taps, have sum of negative taps == -1 and positive +1
        a = np.sum(np.abs(signal_taps))
        b = np.sum(signal_taps)
        p = 1 / ((a + b) / 2)
        n = 1 / ((a - b) / 2)
        self.taps = [x*p if x > 0 else x*n for x in signal_taps]
# amount of points dropped by np.correlate from each side of spectrum
        self.corr_padd = float(len(self.taps) - 1) / 2

    def signals_detected(self, signals, spectrum):
        "Should be overriden"
        raise NotImplementedError("Must be overrided")

    def work(self, input_items, output_items):
        for spectrum in input_items[0]:
            self.signals_detected(*self.work_(spectrum))
        return len(input_items[0])

    def work_(self, spectrum):
        corr = np.correlate(spectrum, self.taps)
        corr = [(corr[point_no], point_no) for point_no in range(len(corr))]
        corr.sort(reverse=True)
        signals = []
        for d in corr:
            if d[0] < self.threshold:
                break
            if [c for c in signals if abs(c[1] - d[1]) < self.ch_spacing]:
                continue
            signals.append(d)
        return ([
                {
                    'freq': (point_no + self.corr_padd) * self.point_bw + \
                            self.freq_offs,
                    'ssi': sig_strenght,
                } for sig_strenght, point_no in signals
            ], spectrum)


class signal_detector(gr.hier_block2):
    """Signal detection based on correlation of input signal spectrum and
    expected signal spectrum.

    You are supposed to reimplemen method signals_detected(signals, spectrum). This
    function is called each time new signal detection finishes.
    'signals' is list of dictionaries of detected signals, 'spectrum' contains
    log pwr FFT of input signal.
    """

    def __init__(self, samp_rate, decimation, signal_taps, max_overlap=0.25,
            threshold=4., fft_size=2048, center_freq=0):
        gr.hier_block2.__init__(
            self, "Channel Detector",
            gr.io_signature(1, 1, gr.sizeof_gr_complex),
            gr.io_signature(0, 0, 0),
        )

        ##################################################
        # Parameters
        ##################################################
        self.samp_rate = samp_rate
        self.decimation = decimation
        self.fft_size = fft_size
        self.center_freq = center_freq
        self.signals_detected_handler = None

        ##################################################
        # Blocks
        ##################################################
        self.fft = fft.fft_vcc(fft_size, True, (fft.window.blackmanharris(fft_size)), True, 1)
        self.stream_to_vect = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_size)
        self.log10 = blocks.nlog10_ff(10, fft_size, -10*math.log10(decimation))
        self.integrate = blocks.integrate_ff(decimation, fft_size)
        self.complex_to_mag_squared = blocks.complex_to_mag_squared(fft_size)
        self.sig_det = signal_detector_base(samp_rate, fft_size, signal_taps,
                threshold, max_overlap, center_freq=center_freq)

        ##################################################
        # Connections
        ##################################################
        self.connect((self, 0), (self.stream_to_vect, 0))
        self.connect((self.stream_to_vect, 0), (self.fft, 0))
        self.connect((self.fft, 0), (self.complex_to_mag_squared, 0))
        self.connect((self.complex_to_mag_squared, 0), (self.integrate, 0))
        self.connect((self.integrate, 0), (self.log10, 0))
        self.connect((self.log10, 0), (self.sig_det, 0))

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq

    def get_decimation(self):
        return self.decimation

    def get_fft_size(self):
        return self.fft_size

    def get_signals_detected_handler(self):
        return self.sig_det.signals_detected

    def set_signals_detected_handler(self, handler):
        self.sig_det.signals_detected = handler

    def get_samp_rate(self):
        return self.samp_rate

