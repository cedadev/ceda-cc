
import string, collections

defs = '/data/tmp/grib/grib_api/definitions/grib2/shortName.def'

ee = collections.defaultdict( list )
eee = {}
gg = collections.defaultdict( int )
gg2 = collections.defaultdict( int )
gg3 = collections.defaultdict( int )
kk = collections.defaultdict( int )

ll = []
l1 = None
for l in open( defs ).readlines():
  if l[0] != '#':
    if l[0] == "'":
      if l1 != None:
        ll.append(( l1,zz))
      l1 = [hp,]
      zz = {}
    else:
      bits = string.split( string.strip( l ) )
      if len( bits ) > 1:
        assert bits[1] == '=', 'Unexepected line: %s' % l
        zz[bits[0]]  = int(bits[2])
    l1.append( string.strip(l) )
  else:
    hp = string.strip( l )[1:]
ll.append( (l1,zz) )

for x,zz in ll:
  for k in zz.keys():
    kk[k] += 1
keys = kk.keys()
keys.sort()
kl = ['discipline','parameterCategory','parameterNumber','tag','comment']
for k in keys:
  print '%s [%s]' % (k,kk[k])
  if k not in kl:
    kl.append(k)
tmpl = ''
hdr = ''
for k in kl:
  tmpl += '%%(%s)s,' % k
  hdr += '%s,' % k
tmpl +=  '\n'
hdr +=  '\n'
for x,zz in ll:
  k = string.strip( string.split( x[1] )[0], "'" )
  k2 = '%(discipline)3.3i.%(parameterCategory)3.3i.%(parameterNumber)3.3i' % zz
  k3 = '%s:%s' % (k2,k)
  if k == '~':
    k3 = k2
  gg[k] += 1
  gg2[k2] += 1
  gg3[k3] += 1
  if gg[k] > 1:
    print 'Duplicate: %s [%s,%s::%s]'  % (k,x[0],str(x[1]),ee[k][0])
  if gg2[k2] > 1:
    print 'Duplicate: %s [%s,%s::%s,%s]'  % (k2,k,x[0],ee[k2][0],ee[k2][1][0])
  assert gg3[k3] == 1, 'DUPLICATE: %s'  % k3
  ee[k] = x
  ee[k2] = (k,x)
  eee[k3] = (k,x,zz)

keys = eee.keys()
keys.sort()
oo = open( 'grib2codes.csv', 'w' )
oo.write(hdr)
for k3 in keys:
  k,x,zz = eee[k3]
  ss = collections.defaultdict( str )
  for tk in zz.keys():
    ss[tk] = str(zz[tk])
  if k != '~':
    ss['tag'] = k
  ss['comment'] = x[0]
  oo.write( tmpl % ss )
oo.close()
