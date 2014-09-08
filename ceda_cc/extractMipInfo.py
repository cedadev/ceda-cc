
import collections, glob, string
from fcc_utils2 import mipTableScan, snlist
from config_c4 import CC_CONFIG_DIR

ms = mipTableScan()
snc = snlist()

snl, snla = snc.gen_sn_list( )
NT_mip = collections.namedtuple( 'mip',['label','dir','pattern'] )
vlist = [
('uas',
"eastward_wind",
'Eastward Near-Surface Wind Speed',
'Eastward Near-Surface Wind',
'WRONG LONG NAME (*speed* included)'),
('vas',
"northward_wind",
'Northward Near-Surface Wind Speed',
'Northward Near-Surface Wind',
'WRONG LONG NAME (*speed* included)'),
("snc",
"surface_snow_area_fraction",
"Snow Area Fraction",
"Surface Snow Area Fraction",
"WRONG LONG NAME (*surface* omitted)"),
("prsn",
"snowfall_flux", 
"Solid Precipitation",
"Snowfall Flux",
"WRONG LONG NAME"),
("tntscpbl",
"tendency_of_air_temperature_due_to_stratiform_cloud_and_precipitation_and_boundary_layer_mixing",
"Tendency of Air Temperature due to Stratiform Cloud Condensation and Evaporation",
"Tendency of Air Temperature Due to Stratiform Cloud and Precipitation and Boundary Layer Mixing",
'WRONG LONG NAME'),
("tas",
"air_temperature",
"Air Temperature",
"Near-Surface Air Temperature",
'WRONG LONG NAME'),
("cfadDbze94",
"histogram_of_equivalent_reflectivity_factor_over_height_above_reference_ellipsoid",
"CloudSat Radar Reflectivity CFAD",
"CloudSat Radar Reflectivity",
"INCONSISTENT LONG NAME"),
("cfadLidarsr532",
"histogram_of_backscattering_ratio_over_height_above_reference_ellipsoid",
"CALIPSO Scattering Ratio CFAD",
"CALIPSO Scattering Ratio",
"INCONSISTENT LONG NAME"),
("cl",
"cloud_area_fraction_in_atmosphere_layer",
"Cloud Area Fraction",
"Cloud Area Fraction in Atmosphere Layer",
"INCONSISTENT LONG NAME"),
("clcalipso",
"cloud_area_fraction_in_atmosphere_layer",
"CALIPSO Cloud Fraction",
"CALIPSO Cloud Area Fraction",
'WRONG LONG NAME'),
("cltisccp",
"cloud_area_fraction",
"ISCCP Total Total Cloud Fraction",
"ISCCP Total Cloud Fraction",
'WRONG LONG NAME'),
("reffclwc",
"effective_radius_of_convective_cloud_liquid_water_particle",
"Convective Cloud Droplet Effective Radius",
"Hydrometeor Effective Radius of Convective Cloud Liquid Water",
'INCONSISTENT LONG NAMES'),
("reffclws",
"effective_radius_of_stratiform_cloud_liquid_water_particle",
'Stratiform Cloud Droplet Effective Radius',
'Hydrometeor Effective Radius of Stratiform Cloud Liquid Water',
'INCONSISTENT LONG NAMES' ) ]

class snsub:

  def __init__(self):
    pass

  def isFalseSn(self,var,sn):
    if sn == 'mole_concentration_of_molecular_oxygen_in_sea_water':
      return (True,'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'INVALID STANDARD NAME')
    elif var == 'rldscs' and sn == 'downwelling_longwave_flux_in_air_assuming_clear_sky':
      return (True,'surface_downwelling_longwave_flux_in_air_assuming_clear_sky','WRONG STANDARD NAME (should be surface)' )
    elif var == 'clisccp' and sn == 'cloud_area_fraction_in_atmosphere_layer':
      return (True, 'isccp_cloud_area_fraction', 'WRONG STANDARD NAME (should be isccp)' )
    return (False,'no match','')

  def isFalseLn(self,var,ln):
    for tt in vlist:
       if var == tt[0] and ln == tt[2]:
         return (True, tt[3], tt[4] )
    return (False,'no match','')

snsubber = snsub()

mips = ( NT_mip( 'cmip5','cmip5_vocabs/mip/', 'CMIP5_*' ),
         NT_mip( 'ccmi', 'ccmi_vocabs/mip/', 'CCMI1_*')  )

cmip5_ignore = ['pfull','phalf','depth','depth_c','eta','nsigma','vertices_latitude','vertices_longitude','ztop','ptop','p0','z1','z2','href','k_c','a','a_bnds','ap','ap_bnds','b','b_bnds','sigma','sigma_bnds','zlev','zlev_bnds','zfull','zhalf']

vl0 = []
tl = []
td = {}

for mip in mips:
 ## dl = glob.glob( '%s%s' % (mip.dir,mip.pattern) )
  dl = glob.glob( '%s/%s%s' % (CC_CONFIG_DIR, mip.dir,mip.pattern) )
  dl.sort()
  for d in dl:
    tab = string.split( d, '/')[-1]
    isoceanic = tab[:7] == "CMIP5_O"
    l2 = ms.scan_table( open( d ).readlines(), None, asDict=True, lax=True, tag="x", warn=True)
    l2k = []
    for k in l2.keys():
      if k not in cmip5_ignore:
        l2k.append(k)
    l2k.sort()
    vl0 += l2k
    tl.append( [tab,l2, l2k,isoceanic] )
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
##  print v, l, td[l[0]][v][1].get('standard_name','__NO_STANDARD_NAME__')

vd2 = {}
for v in vars:
  l = vdict[v]
  l.sort()
  if len(l) > 1:
    for att in ['standard_name','units','long_name']:
    ##for att in ['standard_name','units']:
      atl = map( lambda x: td[x][v][1].get(att,'__ABSENT__'), l )
      atl.sort()
      av = [atl[0],]
      for a in atl[1:]:
        if a != av[-1]:
          av.append(a)
      if att == 'standard_name':
        for a in av:
          if a not in snl and a not in snla:
            print "INVALID STANDARD NAME: ",a
      if len(av) > 1:
        ee = {}

        for a in [True,False]:
          ee[a] = []

        isol = []
        for x in l:
          a = td[x][v][1].get(att,'__ABSENT__')
          if att == 'standard_name' or ( att == 'long_name' and vd2[v][0] == 2):
            iso = x[:7] == 'CMIP5_O'
            tt = snsubber.isFalseSn( v, a )
          elif att == 'long_name':
            tt = snsubber.isFalseLn( v, a )
            dims = td[x][v][0]
            iso = 'depth0m' in dims
          else:
            iso = False
            tt = (False,)
      ##    iso = False
          isol.append((iso,x))
          if tt[0]:
            print 'Substituting ',v,a,tt
            ee[iso].append( tt[1] )
          else:
            ee[iso].append( a )

        for a in [True,False]:
          ok = True
          if len(ee[a]) > 1 :
            for x in ee[a][1:]:
              if x != ee[a][0]:
                ok = False

          if not ok:
             print 'Multiple values : ',att,v
             for t in isol:
               if t[0] == a:
                 tab = t[1]
                 print tab,td[tab][v][1].get('standard_name','__ABSENT__'),td[tab][v][1].get('long_name','__ABSENT__')
                
        if att == "standard_name":
          vd2[v] = (2,[ee[True],ee[False]] )
      else:
        if att == "standard_name":
          tt = snsubber.isFalseSn( v, av[0] )
          if tt[0]:
            print 'Substituting ',v,av[0],tt
            vd2[v] = (1, tt[1])
          else:
            vd2[v] = (1, av)
  elif len(l) == 1:
        tab = vdict[v][0]
        a = td[tab][v][1].get('standard_name','__ABSENT__')
        tt = snsubber.isFalseSn( v, a )
        if tt[0]:
          print 'Substituting ',v,a,tt
          vd2[v] = (1, tt[1])
        else:
          vd2[v] = (1, a)
        ##print 'MULTIPLE VALUES: ',v,att,av
  else:
   print 'Zero length element: %s' % v
   



