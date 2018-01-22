#!/usr/bin/env python3
    #indent size

AUTHOR = "Jonah Haney"
VERSION = "2018.1.21"

import sys
import argparse
from PIL import Image

files = []
colors = []

parser = argparse.ArgumentParser()
command = parser.add_mutually_exclusive_group(required = True)

parser.add_argument("f", metavar = "<image>", help = "Specify image file(s) to operate on")
command.add_argument("-w", metavar = "<text>", help = "Write watermark (text)", default = None)
command.add_argument("-W", metavar = "<file>", help = "Write watermark from file", default = None)
command.add_argument("-r", help = "Read watermark (one file only)", action = "store_true", default = False)
parser.add_argument("-o", metavar = "<file>", help = "Specify output file (write to stdout if none)", default = sys.stdout.buffer)
parser.add_argument("-R", help = "Use Red byte", action = "store_true", default = False)
parser.add_argument("-G", help = "Use Green byte", action = "store_true", default = False)
parser.add_argument("-B", help = "Use Blue byte", action = "store_true", default = False)
parser.add_argument("-V", help = "Read/Write Vertically", action = "store_true", default = False)

args = parser.parse_args()

# Print message to stderr
def log(*args):
	for arg in args:
		sys.stderr.write(arg)
	sys.stderr.write("\n")

#Exit with an exit message (to stderr) and de-allocate all file resources
def terminate(exit_message):
	if exit_message != None:
		log(exit_message)
	for f in files:
		try:
			f.close()
		except:
			log("Failed to close file: ", f.name)
	sys.stderr.flush()
	quit()

# Open a file, use this in place of open()
def fopen(file_name, mode):
	f = None
	try:
		if mode == None:
			f = open(file_name)
		else:
			f = open(file_name, mode)
		files.append(f)
		return f
	except:
		log("Could not open file ", file_name)
		return None

# Open an image using fopen
def fimage(file_name, mode):
	try:
		i = Image.open(fopen(file_name, mode))
		files.append(i)
		return i
	except:
		log(file_name, " not recognized as image file")
		return None

# Manage arguments
orig = fimage(args.f, "rb")
fmt = orig.format
orig = orig.convert("RGB")
outf = args.o
mark = []

if orig == None:
	terminate(None)

if outf != sys.stdout.buffer:
	outf = fopen(args.o, "wb")

if args.w != None:
	_mark = bytes([ord(args.w[i]) for i in range(len(args.w))])
	for c in _mark:
		for i in range(8):
			mark.append((int(c) & (0b10000000 >> i)) >> 7 - i)

elif args.W != None:
	_mark = fopen(args.W, "rb").read()
	for c in _mark:
		for i in range(8):
			mark.append((int(c) & (0b10000000 >> i)) >> 7 - i)


if not (args.R or args.G or args.B):
	colors = [0, 1, 2]
else:
	if args.R:
		colors.append(0)
	if args.G:
		colors.append(1)
	if args.B:
		colors.append(2)

b = []
w, h = orig.size
if args.V:
	w^=h; h^=w; w^=h # Swap h & w

# Retrieve watermark
if args.r:
	for y in range(h):
		for x in range(w):
			if args.V:
				x^=y; y^=x; x^=y # Swap x & y
			for c in colors:
				b.append(str(orig.getpixel((x,y))[c] & 1))
	if len(b) % 8 != 0:
		b = b[:-(len(b) % 8)]
	b = ''.join(b)
	for i in range(0, len(b), 8):
		outf.write(bytes([int(b[i:i+8], 2)]))

# TODO Write watermark
else:
	i = 0
	flag = False
	for y in range(h):
		for x in range(w):
			if args.V:
				x^=y; y^=x; x^=y # Swap x & y
			pix = list(orig.getpixel((x,y)))
			for c in colors:
				pix[c] = (pix[c] & 0b11111110) | mark[i]
				i += 1
				if i == len(mark):
					i = 0
					flag = True
			orig.putpixel((x,y), (*pix,))
	
	if outf == sys.stdout.buffer:
		tmp_name = ".tmp." + fmt
		orig.save(tmp_name)
		outf.write(fopen(tmp_name, "rb").read())
	else:
		orig.save(args.o)

	if not flag:
		log("Success. NOTE: image too small to store entire watermark")
	else:
		log("Success.")
