
import collections, glob, string
from fcc_utils2 import mipTableScan
from config_c4 import CC_CONFIG_DIR

ms = mipTableScan()

NT_mip = collections.namedtuple( 'mip',['label','dir','pattern'] )

mips = ( NT_mip( 'cmip5','cmip5_vocabs/mip/', 'CMIP5_*' ), )

cmip5_ignore = ['depth','depth_c','eta','nsigma','vertices_latitude','vertices_longitude','ztop','ptop','p0','z1','z2','href','k_c','a','a_bnds','ap','ap_bnds','b','b_bnds','sigma','sigma_bnds','zlev','zlev_bnds','zfull','zhalf']

vl0 = []
for mip in mips:
  dl = glob.glob( '%s/%s%s' % (CC_CONFIG_DIR, mip.dir,mip.pattern) )
  dl.sort()
  tl = []
  td = {}
  for d in dl:
    tab = string.split( d, '/')[-1]
    l2 = ms.scan_table( open( d ).readlines(), None, asDict=True, lax=True, tag="x", warn=True)
    l2k = []
    for k in l2.keys():
      if k not in cmip5_ignore:
        l2k.append(k)
    l2k.sort()
    vl0 += l2k
    tl.append( [tab,l2, l2k] )
    td[tab] = l2

vl0.sort()
vl = []
vl.append( vl0[0] )
vdict = { vl[0]:[] }
for v in vl0[1:]:
  if v != vl[-1]:
    vl.append(v)
    vdict[v] = []

for t in tl:
  print t[0],t[2]
  for k in t[2]:
    vdict[k].append(t[0])

vars = vdict.keys()
vars.sort()
for v in vars:
  l = vdict[v]
  l.sort()
  print v, l, td[l[0]][v][1].get('standard_name','__NO_STANDARD_NAME__')

