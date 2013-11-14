
import string, sys, glob

idir = sys.argv[1]

fl = glob.glob( '%s/*.txt' % idir )

ee = {}
for f in fl:
  for l in open(f).readlines():
    if string.find(l, 'FAILED') != -1:
      bits = string.split(l, ':' )
      if len(bits) > 3:
        code = bits[0]
        msg = bits[3]
        if code not in ee.keys():
          ee[code] = [0,msg]
        ee[code][0] += 1
        if ee[code][1] != msg:
          print 'code %s occurs with multiple messages: %s, %s' % (code,ee[code][1],msg)
      else:
        print bits

keys = ee.keys()
keys.sort()
for k in keys:
  print k,ee[k]




