#!/usr/bin/env python3

# Usage:
#
# Adjust the center frequency (-f) and gain (-g) according to your needs.


import sys
import math
from gnuradio import gr, eng_notation, blocks, filter, digital, analog, fft
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import osmosdr
import time
import threading
import subprocess
import string

# applies frequency translation, resampling and demodulation

class top_block(gr.top_block):
  def __init__(self):
    gr.top_block.__init__(self)

    symbolrate = 8000
    channel_bw = 12500

    taps_ch = 16

    options = get_options()

    chan0_freq = options.channel_0_freq
    self.rfgain = options.gain

    self.channels = [ int(ch) for ch in options.channels.split(',') if ch ]
    self.ch_freqs = [ ch * channel_bw + chan0_freq for ch in self.channels ]
    self.ch_freqs.extend(
            [ int(f) for f in options.channels_by_freq.split(',') if f ])
    while len(self.channels) < len(self.ch_freqs):
        self.channels.append(-1)

    if options.frequency is None:
        self.ifreq = (max(self.ch_freqs) + min(self.ch_freqs)) / 2 + 50000
        if (min(self.channels) + max(self.channels)) % 2:
            self.ifreq = self.ifreq - channel_bw / 2
    else:
        self.ifreq = options.frequency

    sys.stderr.write("freq: %d\n" % (self.ifreq))

    ch0 = (self.ifreq - chan0_freq ) / channel_bw
    n = options.sample_rate / channel_bw
    s = options.sample_rate / symbolrate / 2
    c = ''
    ntap = options.sample_rate / channel_bw * taps_ch - 1 
    for ch in range(0,len(self.channels)):
        c = c + '%i,'%((self.channels[ch] - ch0)%n)
    c=c[:-1]

    self.src = osmosdr.source(options.args)
    self.src.set_center_freq(self.ifreq)
    self.src.set_sample_rate(options.sample_rate)
    self.src.set_bandwidth(options.sample_rate)
    self.src.set_freq_corr(options.ppm, 0)

    fcl_args = ['./fcl', '-n', '%i'%n, '-s', '%i'%s, '-t', '2', '-c', '%s'%c, '-f', 'python3 ./fir.py %i 7900 %i rcos'%(options.sample_rate, ntap), '-o', '/dev/stdout']
    sys.stderr.write(' '.join(fcl_args)+'\n')
    self.fcl = subprocess.Popen(fcl_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    self.fcl_in = blocks.file_descriptor_sink(gr.sizeof_gr_complex*1, self.fcl.stdin.fileno())
    self.fcl_out = blocks.file_descriptor_source(gr.sizeof_gr_complex*1, self.fcl.stdout.fileno(), False)
    self.deinterleave = blocks.deinterleave(gr.sizeof_gr_complex*1, 1)

    self.connect((self.src, 0), (self.fcl_in, 0))
    self.connect((self.fcl_out, 0), (self.deinterleave, 0))

    if self.rfgain is None:
        self.src.set_gain_mode(True, 0)
        self.iagc = 1
        self.rfgain = 0
    else:
        self.iagc = 0
        self.src.set_gain_mode(True)
        self.src.set_gain_mode(False)
        self.src.set_gain(self.rfgain)
#        self.src.set_gain(30,"LNA")
#        self.src.set_gain(12,"TIA")
#        self.src.set_gain(16,"PGA")
#    self.src.set_antenna('LNAL')
#    self.src.set_bandwidth(50000000)


    # may differ from the requested rate
    sample_rate = int(self.src.get_sample_rate())
    sys.stderr.write("sample rate: %d\n" % (sample_rate))

    first_decim = int(options.sample_rate / symbolrate / 2)
    sys.stderr.write("decim: %d\n" % (first_decim))

    out_sample_rate=sample_rate/first_decim
    sys.stderr.write("output sample rate: %d\n" % (out_sample_rate))

    sps=out_sample_rate/symbolrate
    sys.stderr.write("samples per symbol: %d\n" % (sps))

    self.tuners = []
    self.afc_probes = []
    if len(self.channels) != 1:
        if options.output_file:
            if options.output_file.find('%%') == -1:
                raise ValueError('Output name template missing "%%".')
        elif options.output_pipe:
            if options.output_pipe.find('%%') == -1:
                raise ValueError('Output name template missing "%%".')
        else:
            raise ValueError('WTF')
    for ch in range(0,len(self.channels)):
        bw = (9200 + options.afc_ppm_threshold)/2
        taps = filter.firdes.low_pass(1.0, out_sample_rate, bw, bw*options.transition_width, fft.window.WIN_HANN)
        offset = self.ch_freqs[ch] - self.ifreq
        sys.stderr.write("channel[%d]: %d frequency=%d, offset=%d Hz\n" % (ch, self.channels[ch], self.ch_freqs[ch], offset))


        tuner = filter.freq_xlating_fir_filter_ccc(1, taps, offset, out_sample_rate)
        self.tuners.append(tuner)

        demod = digital.gmsk_demod(samples_per_symbol=sps)

        fname = self.channels[ch]
        if fname == -1:
            fname = self.ch_freqs[ch]
        if options.output_pipe is None:
            file = options.output_file.replace('%%', str(fname))
            output = blocks.file_sink(gr.sizeof_char, file)
        else:
            cmd = options.output_pipe.replace('%%', str(fname))
            pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)
            fd = pipe.stdin.fileno()
            output = blocks.file_descriptor_sink(gr.sizeof_char, fd)

        self.connect((self.deinterleave, ch), (tuner, 0))
        self.connect((tuner, 0), (demod, 0))
        self.connect((demod, 0), (output, 0))

        afc_decimation = 32000
        afc_demod = analog.quadrature_demod_cf(sample_rate/first_decim/(2*math.pi*afc_decimation))
        integrate = blocks.integrate_ff(afc_decimation)
        afc_probe = blocks.probe_signal_f()
        self.afc_probes.append(afc_probe)

        self.connect((tuner, 0), (afc_demod,0))
        self.connect((afc_demod, 0), (integrate,0))
        self.connect((integrate, 0), (afc_probe, 0))

    def _variable_function_probe_0_probe():
        while True:
            time.sleep(options.afc_period)
            for ch in range(0,len(self.channels)):
                err = self.afc_probes[ch].level()
                if abs(err) < options.afc_ppm_threshold:
                    continue
                freq = self.tuners[ch].center_freq() + err * options.afc_gain
                self.tuners[ch].set_center_freq(freq)
                if self.channels[ch] == -1:
                    sys.stderr.write("Freq %d freq err: %5.0f\tfreq: %f\n" % (self.ch_freqs[ch], err, freq))
                else:
                    sys.stderr.write("Chan %d freq err: %5.0f\tfreq: %f\n" % (self.channels[ch], err, freq))
            sys.stderr.write("\n")
    _variable_function_probe_0_thread = threading.Thread(target=_variable_function_probe_0_probe)
    _variable_function_probe_0_thread.daemon = True
    _variable_function_probe_0_thread.start()



def get_options():
    parser = OptionParser(option_class=eng_option)

    parser.add_option("-a", "--args", type="string", default="", help="gr-osmosdr device arguments")
    parser.add_option("-s", "--sample-rate", type="eng_float", default=1024000, help="receiver sample rate (default %default)")
    parser.add_option("-f", "--frequency", type="eng_float", default=None, help="receiver center frequency (default %default)")
    parser.add_option("-g", "--gain", type="eng_float", default=None, help="set receiver gain")
    parser.add_option("-c", "--channels", type="string", default="", help="channel numbers")
    parser.add_option("-p", "--ppm", dest="ppm", type="eng_float", default=eng_notation.num_to_str(0), help="Frequency correction")
    parser.add_option("-t", "--transition-width", type="eng_float", default=0.2, help="low pass transition width (default %default)")
    parser.add_option("-G", "--afc-gain", type="eng_float", default=1, help="afc gain (default %default)")
    parser.add_option("-P", "--afc-period", type="eng_float", default=4, help="afc period (default %default)")
    parser.add_option("-T", "--afc-ppm-threshold", type="eng_float", default=100, help="afc threshold (default %default)")
    parser.add_option("-o", "--output-file", type="string", default="channel%%.bits", help="specify the bit output file")
    parser.add_option("-O", "--output-pipe", type="string", default=None, help="specify shell pipe to send output")
    parser.add_option("-l", "--channels-by-freq", type="string", default="", help="Receive on specified frequencies")
    parser.add_option("-z", "--channel-0-freq", type="eng_float", default=358400000, help="Frequency of channel 0")
    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.print_help()
        raise SystemExit(1)

    return (options)

if __name__ == '__main__':
        tb = top_block()
        tb.start()
        tb.wait()
