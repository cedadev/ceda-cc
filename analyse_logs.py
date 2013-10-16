#!/usr/bin/env python

"""
analyse_logs.py
===============

Generates a summary of the logs (one-per-file) in a given directory.

Usage:
======

    analyse_logs.py <directory>

"""

# Standard Library imports
import sys, glob, os


def generateSummaryByErrorCode(dr):
    "Prints a summary of all files that detected a particular error."
    
    files = glob.glob('%s/*.txt' % dr)

    errors = {}

    for f in files:
        fname = os.path.split(f)[1].split("__qclog")[0] + ".nc"
        if fname.find("qcBatchLog") == 0: continue

        fin = open(f)
        fname

        for l in fin.readlines():

            if l.find('FAILED') != -1:
                bits = l.split(':')

                if len(bits) > 3:
                    code = bits[0]
                    msg = bits[3]

                    errors.setdefault((code, msg), [])
                    errors[(code, msg)].append(fname)

        fin.close()

    keys = errors.keys()
    keys.sort()

    for k in keys:
        files = errors[k]
        files.sort()
        print "CODE: %s (%d files)" % (k, len(files))
   
        for f in files: print "\t%s" % f



if __name__ == "__main__":

    dr = sys.argv[1]
    generateSummaryByErrorCode(dr)
