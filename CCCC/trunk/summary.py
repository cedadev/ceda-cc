
import string, sys, glob

idir = sys.argv[1]

fl = glob.glob( '%s/*.txt' % idir )

ee = {}
for f in fl:
  for l in open(f).readlines():
    fn = string.split(f,'/')[-1]
    if string.find(l, 'FAILED') != -1:
      bits = string.split(l, ':' )
      if len(bits) > 3:
        code = bits[0]
        msg = string.strip( string.join(bits[3:], ':' ) )
        if code not in ee.keys():
          ee[code] = [0,{msg:[0,[]]}]
        elif msg not in ee[code][1].keys():
          ee[code][1][msg] = [0,[]]
        ee[code][0] += 1
        ee[code][1][msg][0] += 1
        if ee[code][1][msg][0] < 10:
          ee[code][1][msg][1].append(fn)
      else:
        print bits

keys = ee.keys()
keys.sort()
for k in keys:
  ks = ee[k][1].keys()
  if len(ks) == 1:
    print k,ee[k][0],ks[0]
    for i in range(min(2,ee[k][0])):
      print '               ',ee[k][1][ks[0]][1][i]
  else:
    print k,ee[k][0]
    ks.sort()
    for k2 in ks:
      print '  --- ',k2,ee[k][1][k2][0]
      for i in range(min(2,ee[k][1][k2][0])):
        print '               ',ee[k][1][k2][1][i]




