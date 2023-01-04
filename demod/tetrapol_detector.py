#!/usr/bin/python3
# -*- encoding: UTF-8 -*-
##################################################
# Gnuradio Python Flow Graph
# Title: TETRAPOL channel detector
# Description: Detect peaks in signal spectrum which might be TETRAPOL radio
#   channels
##################################################

from gnuradio import blocks
from gnuradio import gr
from gnuradio.eng_option import eng_option
from json import dumps
from optparse import OptionParser
from signal_detector import signal_detector, mk_cos_taps
import math
import osmosdr


class tetrapol_detector(gr.top_block):

    def __init__(self, in_url, samp_rate, channel_bw, freq=0, gain=None,
            fft_nbins=None, decimation=None, threshold=None,
            out_url='stdout://', rounds=-1, spectrum_out=None):
        gr.top_block.__init__(self, "RSTT Signal Detector")
        threshold = threshold or (4,6)

        if fft_nbins is None:
            # set FFT size to get 10 or more bins per channel
            fft_nbins = 10. * samp_rate / channel_bw
            fft_nbins = 2**int(math.ceil(math.log(fft_nbins, 2)))

        if decimation is None:
            # average samples for at least one second
            decimation = int(math.ceil(float(samp_rate) / fft_nbins))

        ntaps = int(2. * fft_nbins / samp_rate * channel_bw)

        if isinstance(threshold, (float, int)):
            threshold = (threshold, )

        self.in_url = in_url
        self.channel_bw = channel_bw
        self.samp_rate = samp_rate
        self.fft_nbins = fft_nbins
        self.decimation = decimation
        if spectrum_out:
            self.spectrum_out = open(spectrum_out, 'w')
        else:
            self.spectrum_out = None
        self.threshold_lo = min(threshold)
        self.threshold_hi = max(threshold)
        self.rounds = rounds
        self.freq = freq
        self.signals = []
# TODO: parametrize
        self.ttl = 1

        args = in_url.split('://', 1)
        if len(args) == 2:
            prefix, args = args
        else:
            prefix, args = "", args[0]
        if prefix == 'osmo-sdr':
            self.src = osmosdr.source( args="numchan=1 " + args )
            self.src.set_sample_rate(samp_rate)
            self.src.set_center_freq(freq, 0)
            if gain is None:
                self.src.set_gain_mode(True, 0)
            else:
                self.src.set_gain_mode(False)
                self.src.set_gain(gain)
                #self.src.set_if_gain(37)
        elif prefix == 'file' or prefix == "":
            self.src = blocks.file_source(gr.sizeof_gr_complex, args, False)
        elif prefix == 'udp':
            host, port = args.split(':', 1)
            self.src = blocks.udp_source(gr.sizeof_gr_complex, host, int(port), 65536, True)
        else:
            raise ValueError('Unsupported schema: "%s"' % in_url)

        self.signal_detector = signal_detector(samp_rate, decimation,
                mk_cos_taps(ntaps), threshold=self.threshold_lo, fft_size=fft_nbins,
                center_freq=freq)
        self.signal_detector.set_signals_detected_handler(self.on_signals_detected)

        self.connect((self.src, 0), (self.signal_detector, 0))

        args = out_url.split('://')
        if len(args) == 2:
            prefix, args = args
        else:
            prefix, args = "", args[0]
        if prefix == "file" or prefix == "":
            self.emit_signals = self._emit_signals_file
            self._out = open(args, 'w')
        elif prefix == "stdout":
            self.emit_signals = self._emit_signals_stdout
        else:
            raise ValueError('Unsupported schma: "%s"' % out_url)

    def on_signals_detected(self, signals, spectrum):
        if self.spectrum_out:
            spectrum = ', '.join([str(s) for s in spectrum])
            self.spectrum_out.write(spectrum + "\n")
            self.spectrum_out.flush()
        if self.rounds > 0:
            self.rounds -= 1
        for sig in self.signals:
            sig['ttl'] -= 1
        for sig_det in signals:
            sig_det['ttl'] = self.ttl
            is_new = True
            for sig_old in self.signals:
                if abs(sig_old['freq'] - sig_det['freq']) < self.channel_bw / 2:
                    is_new = False
                    break
            sig_det['new'] = is_new
        signals = [s for s in signals if s['ssi'] >= self.threshold_hi]
        self.signals = [sig for sig in self.signals if sig['ttl'] != 0]
        for sig_old in self.signals:
            missing = True
            for sig_det in signals:
                if abs(sig_old['freq'] - sig_det['freq']) < self.channel_bw / 2:
                    missing = False
            if missing:
                signals.append(sig_old)
        self.signals = signals
        self.emit_signals(signals)
        if self.rounds == 0:
            self.do_exit()

    def _signals2str(self, signals):
        return "[\n%s\n]" % ",\n".join([dumps(s) for s in signals])

    def _emit_signals_file(self, signals):
        self._out.write(self._signals2str(signals))
        self._out.flush()

    def _emit_signals_stdout(self, signals):
        print(self._signals2str(signals))

    def get_in_url(self):
        return self.in_url

    def get_channel_bw(self):
        return self.channel_bw

    def get_samp_rate(self):
        return self.samp_rate

    def get_fft_nbins(self):
        return self.fft_nbins

    def get_decimation(self):
        return self.decimation

    def get_spectrum_out(self):
        raise NotImplemented("TODO")

    def get_threshold(self):
        return (self.threshold_lo, self.threshold_hi)

    def get_rounds(self):
        return self.rounds

    def get_freq(self):
        return self.freq

    def get_ttl(self):
        return self.ttl

    def do_exit(self):
        self.stop()

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option("-b", "--bins", dest="fft_nbins", type="intx",
        help="Number of bins for signal spectrum analysis.")
    parser.add_option("-B", "--channel_bw", dest="channel_bw", type="intx",
        default=12500, help="Channel band width [Hz] (10kHz or 12.5kHz)")
    parser.add_option("-d", "--decimation", dest="decimation", type="intx",
        help="How much FFT result average for one detection run.")
    parser.add_option("-f", "--frequency", dest="freq", type=float, default=0,
        help="Set signal center freqency (can be used also for file input)")
    parser.add_option("-g", "--gain", dest="gain", type=float, default=None,
        help="RF gain")
    parser.add_option("-i", "--input", dest="in_url", type="string",
        help="URL of input (osmo-sdr://<ARGS> | file:// | udp://<HOST>:<PORT>)")
    parser.add_option("-o", "--output", dest="out_url", type="string", default='stdout://',
        help="URL to send detected channels (stdout:// | file://<PATH>)")
    parser.add_option("-p", "--spectrum-out", dest="spectrum_out",
        help="Write signal power spectrum into CSV file",)
    parser.add_option("-r", "--rounds", dest="rounds", type="intx", default=-1,
        help="Exit after N signal detections passes [default=-1 (infinity)]")
    parser.add_option("-s", "--samp-rate", dest="samp_rate", type="intx",
        help="Input sample rate.")
    parser.add_option("-t", "--threshold", dest="threshold", default="4:6",
        help="Detection threshold: <dB> | <dB_lo>:<dB_hi>")
    (options, args) = parser.parse_args()
    threshold = options.threshold.split(':')
    threshold = [float(t) for t in threshold]
    if len(threshold) == 1:
        threshold = threshold[0]
    tb = tetrapol_detector(
            in_url = options.in_url,
            channel_bw = options.channel_bw,
            samp_rate = options.samp_rate,
            freq = options.freq,
            gain = options.gain,
            fft_nbins = options.fft_nbins,
            decimation = options.decimation,
            threshold = threshold,
            out_url = options.out_url,
            rounds = options.rounds,
            spectrum_out = options.spectrum_out)
    tb.start()
    tb.wait()

