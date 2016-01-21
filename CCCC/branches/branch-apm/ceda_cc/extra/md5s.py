#!/usr/bin/python

import sys, os, string

fpath = sys.argv[1]

fn = string.split(fpath,'/')[-1]
fns = string.split( fn, '.' )[0]
sdir = string.replace( fpath, fn, '' )


os.popen( '(cd %s;md5sum %s) > md5s/%s.md5sum' % (sdir, fn, fns) ).readlines()
