#!/usr/bin/env python

"""
summary.py
==========

Generates a summary of the logs (one-per-file) in a given directory.

Usage:
======

    summary.py <directory>

"""

# Standard Library imports
import sys, glob, os


def generateSummary(dr):
    "Generates a summary of logged outputs."

    files = glob.glob( '%s/*.txt' % dr )

    errors_by_ = {}

    """
    for f in files:
        fin = open(f)

        for l in fin.readlines():

            if l.find('FAILED') != -1:
                bits = l.split(':')

                if len(bits) > 3:
                    code = bits[0]
                    msg = bits[3]

                    errors.setdefault((code, msg), [])
                    errors[code, msg].append(

                    if errors[code][1] != msg:
                        print 'code %s occurs with multiple messages: %s, %s' % (code,errors[code][1],msg)
                    else:
                        print bits

         fin.close()

    keys = errors.keys()
    keys.sort()

    for k in keys:
        print k, errors[k]
    """

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
   
        if printFiles:
          for f in files: print "\t%s" % f
        elif printTwoFiles:
          for f in files[:min(2,len(files))]: 
            print "\t%s" % f



if __name__ == "__main__":

    printFiles = False
    printTwoFiles = True
    dr = sys.argv[1]
    generateSummaryByErrorCode(dr)
