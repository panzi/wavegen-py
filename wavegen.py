#!/usr/bin/env python

from __future__ import division

import sys
from struct import pack
import math
from math import pi

tau     = 2   * pi
pi_half = 0.5 * pi

if not hasattr(__builtins__,'xrange'):
	xrange = range

if hasattr(__builtins__,'unicode'):
	strtypes = (str, unicode)
else:
	strtypes = (str,)

def to_full_byte(bits):
	rem = bits % 8
	return bits if rem == 0 else bits + (8 - rem)

def square_wave(t):
	if t % tau < pi:
		return 1
	else:
		return -1

def triangle_wave(t):
	x = (t + pi_half) % tau
	if x < pi:
		return 2 * x / pi - 1
	else:
		return 3 - 2 * x / pi

def sawtooth_wave(t):
	return (t % tau) / pi - 1

def fadein(t,duration):
	if t < 0:
		return 0
	x = t / duration
	return min(x*x,1)

def fadeout(t,duration):
	if t > duration:
		return 0
	x = (t - duration) / duration
	return min(x*x,1)

def wavegen(stream,sample_rate,bits_per_sample,samples,wavefuncts,write_header=True):
	if sample_rate <= 0:
		raise ValueError("illegal sample rate")

	if bits_per_sample <= 0:
		raise ValueError("illegal number of bits per sample")

	if samples < 0:
		raise ValueError("illegal number of samples")

	channels = len(wavefuncts)

	if channels <= 0:
		raise ValueError("illegal number of channels")

	defs = dict((key,val) for key, val in math.__dict__.items() if not key.startswith('_'))
	defs['tau'] = tau
	defs['sq']  = square_wave
	defs['tri'] = triangle_wave
	defs['saw'] = sawtooth_wave
	defs['fadein']  = fadein
	defs['fadeout'] = fadeout
	wavefuncts = [
		eval('lambda t:'+wavefunct,defs) if isinstance(wavefunct,strtypes) else wavefunct
		for wavefunct in wavefuncts]

	ceil_bits_per_sample = to_full_byte(bits_per_sample)
	shift = ceil_bits_per_sample - bits_per_sample
	bytes_per_sample = ceil_bits_per_sample // 8
	block_align = channels * bytes_per_sample
	byte_rate = sample_rate * block_align
	data_size = block_align * samples
	fmt_size  = 16
	audio_format = 1 # PCM
	riff_size = 36 + data_size
	mid = 1 << (bits_per_sample - 1)
	max_volume = ~(~0 << (bits_per_sample - 1))

	if write_header:
		stream.write(pack('<4BI4B4BIHHIIHH4BI',
			ord('R'),ord('I'),ord('F'),ord('F'),riff_size,ord('W'),ord('A'),ord('V'),ord('E'),
			ord('f'),ord('m'),ord('t'),ord(' '),fmt_size,audio_format,channels,sample_rate,
			byte_rate,block_align,bits_per_sample,
			ord('d'),ord('a'),ord('t'),ord('a'),data_size))

	sample_fmt = 'B' * bytes_per_sample
	for sample in xrange(samples):
		t = sample / sample_rate
		for wavefunct in wavefuncts:
			vol = int(max_volume * wavefunct(t)) << shift
			if bits_per_sample <= 8:
				vol += mid
			stream.write(pack(sample_fmt, *[(vol >> (byte * 8)) & 0xFF
				for byte in xrange(bytes_per_sample)]))

def main(args):
	filename = args[0]
	sample_rate = int(args[1])
	bits_per_sample = int(args[2])
	samples = int(args[3])
	wavefuncts = args[4:]
	if filename == '-':
		wavegen(sys.stdout,sample_rate,bits_per_sample,samples,wavefuncts)
	else:
		with open(filename,'wb') as stream:
			wavegen(stream,sample_rate,bits_per_sample,samples,wavefuncts)

if __name__ == '__main__':
	main(sys.argv[1:])
