
import string, sys, glob

args = sys.argv[1:-1]
idir = sys.argv[-1]
ndisp = 2
while len(args) > 0:
  x = args.pop(0)
  if x == '-n':
    ndisp = int( args.pop(0) )

fl = glob.glob( '%s/*__qclog_*.txt' % idir )

ee = {}
print 'Summarising error reports from %s log file' % len(fl)
nne = 0
for f in fl:
  nef = 0
  for l in open(f).readlines():
    fn = string.split(f,'/')[-1]
    if string.find(l, 'FAILED') != -1 or string.find(l,'CDMSError:') != -1:
      nef += 1
      if string.find(l, 'FAILED') != -1:
         kb1 = 3
      else:
         kb1 = 1
      bits = string.split(l, ':' )
      if len(bits) > kb1:
        code = bits[0]
        msg = string.strip( string.join(bits[kb1:], ':' ) )
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
  if nef == 0:
    nne += 1

keys = ee.keys()
keys.sort()
def cmin(x,y):
  if x < 0:
    return y
  else:
    return min(x,y)

for k in keys:
  ks = ee[k][1].keys()
  if len(ks) == 1:
    print k,ee[k][0],ks[0]
    for i in range(cmin(ndisp,ee[k][0])):
      print '               ',ee[k][1][ks[0]][1][i]
  else:
    print k,ee[k][0]
    ks.sort()
    for k2 in ks:
      print '  --- ',k2,ee[k][1][k2][0]
      for i in range(cmin(ndisp,ee[k][1][k2][0])):
        print '               ',ee[k][1][k2][1][i]


print 'Number of files with no errors: %s' % nne



