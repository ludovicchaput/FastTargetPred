#!/usr/bin/env python3
# Script written in Python3


import sys, os, codecs

input_filename = sys.argv[1]
output_filename = os.path.splitext(input_filename)[0] + ".bfp"
output_listname = os.path.splitext(input_filename)[0] + ".id"

infile   = open(input_filename)
outlist  = open(output_listname, "w")
outfile  = open(output_filename, "wb")

# read 
line = infile.readline()
line = infile.readline()

while line:
	rawMolID = line.split(",")[0]
	MolID    = rawMolID.replace('"','')
	rawFP    = line.split("Ascending;",1)[1]
	raw2FP   = rawFP.replace('"\n','')

	lenid = len(MolID).to_bytes(1, byteorder='big', signed=True)
	outlist.write(MolID+"\n")
	outfile.write(lenid)
	outfile.write(codecs.encode(MolID, 'ascii'))
	outfile.write(codecs.decode(raw2FP, 'hex'))
	line     = infile.readline()
infile.close()
outlist.close()
