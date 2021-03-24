
import collections, glob, string, re, json, sys
from .fcc_utils2 import mipTableScan, snlist, tupsort
from .ceda_cc_config.config_c4 import CC_CONFIG_DIR

def uniquify( ll ):
  ll.sort()
  l0 = [ll[0],]
  for l in ll[1:]:
    if l != l0[-1]:
      l0.append(l)
  return l0

heightRequired = ['tas','tasmax','tasmin','huss','sfcWind','sfcWindmax','wsgsmax','uas','vas']
cmip5_ignore = ['depth','depth_c','eta','nsigma','vertices_latitude','vertices_longitude','ztop','ptop','p0','z1','z2','href','k_c','a','a_bnds','ap','ap_bnds','b','b_bnds','sigma','sigma_bnds','zlev','zlev_bnds']
cmip5AxesAtts = ['axis', 'bounds_values', 'climatology', 'coords_attrib', 'formula', 'index_only', 'long_name', 'must_call_cmor_grid', 'must_have_bounds', 'out_name', 'positive', 'requested', 'requested_bounds', 'standard_name', 'stored_direction', 'tolerance', 'type', 'units', 'valid_max', 'valid_min', 'value', 'z_bounds_factors', 'z_factors']


NT_mip = collections.namedtuple( 'mip',['label','dir','pattern'] )
NT_var = collections.namedtuple( 'var',['name','sn','snStat','realm','units','longName','comment','mip'] )
NT_canvari = collections.namedtuple( 'canonicalVariation',['conditions','text', 'ref'] )
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


class helper:

  def __init__(self):
    self.applycv = True
    self.re1 = re.compile( '"(.*)"=="(.*)"' )

    self.cmip5Tables= ['CMIP5_3hr', 'CMIP5_6hrPlev', 'CMIP5_Amon', 'CMIP5_cfDay', 'CMIP5_cfOff', 'CMIP5_day', 'CMIP5_grids', 'CMIP5_Lmon', 'CMIP5_OImon', 'CMIP5_Oyr',
  'CMIP5_6hrLev', 'CMIP5_aero', ' CMIP5_cf3hr', 'CMIP5_cfMon', 'CMIP5_cfSites', 'CMIP5_fx', 'CMIP5_LImon', 'CMIP5_Oclim', 'CMIP5_Omon' ]
    self.cmip5DefPoint = ['CMIP5_3hr', 'CMIP5_6hrPlev', 'CMIP5_cfOff', 'CMIP5_6hrLev', ' CMIP5_cf3hr', 'CMIP5_cfSites' ]

    self.canonvar = [ NT_canvari( (('table','CMIP5_3hr'),), 'This is sampled synoptically.', '' ),
                      NT_canvari( (), 'The flux is computed as the mass divided by the area of the grid cell.', 'This is calculated as the convective mass flux divided by the area of the whole grid cell (not just the area of the cloud).' ),
            ]

    self.canonvar = []
    for l in open( 'config/canonicalVariations.txt' ).readlines():
      if l[0] != '#':
        ix = l.index(':')
        s = string.strip( l[ix:] )
        r = self.re1.findall( s )
        assert len(r) == 1, 'Cannot parse: %s' % s
        self.canonvar.append( NT_canvari( (), r[0][0], r[0][1] ) )

  def match(self,a,b):
      if type(a) == type( 'X' ) and type(b) == type( 'X' ):
        a0,b0 = [string.replace(x, '__ABSENT__','') for x in [a,b]]
        return string.strip( string.replace(a0, '  ', ' '), '"') == string.strip( string.replace(b0, '  ', ' '), '"')
      else:
        return a == b

  def checkCond( self, table, var, conditions ):
    val = True
    for ck, cv in conditions:
      if ck == 'table':
        val &= table == cv
      elif ck == 'var':
        val &= var == cv

    return val
        
      

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


class mipCo:

  def __init__(self,mips,helper=None):
    self.vl0 = []
    self.al0 = []
    self.tl = []
    self.dl = []
    self.td = {}
    self.dd = {}
    self.helper = helper
    for mip in mips:
      self._scan(mip)

  def _scan(self,mip):
    
 ## dl = glob.glob( '%s%s' % (mip.dir,mip.pattern) )
    dl = glob.glob( '%s/%s%s' % (CC_CONFIG_DIR, mip.dir,mip.pattern) )
    dl.sort()
    for d in dl:
     if d[-5:] != 'grids':
      tab = string.split( d, '/')[-1]
      isoceanic = tab[:7] == "CMIP5_O"
      l2 = ms.scan_table( open( d ).readlines(), None, asDict=True, lax=True, tag="x", warn=True)
      l2k = []
      usedDims = []
      for k in list(l2.keys()):
        if k not in cmip5_ignore:
          l2k.append(k)
          if l2[k][0] != 'scalar':
            usedDims += l2[k][0]
      l2k.sort()
      usedDims.sort()
      usedDims = uniquify( usedDims )
      
      ##self.al0 += ms.adict.keys()
      self.vl0 += l2k
      self.tl.append( [tab,l2, l2k,isoceanic] )
      self.td[tab] = l2
      ##self.dd[tab] = ms.adict.copy()
      self.dd[tab] = {}
      for k in list(ms.adict.keys()):
        if k not in usedDims:
          print("WARNING[X1]: axis %s declared and not used in table %s" % (k,tab))
      for u in usedDims:
        if u in ms.adict:
           self.dd[tab][u] = ms.adict[u]
        else:
           print('WARNING[X2]: USED DIMENSION %s not in table %s' % (u,tab))
      ##self.dl.append( [tab, ms.adict.copy()] )
      self.dl.append( [tab, self.dd[tab].copy() ] )
      self.al0 += list(self.dd[tab].keys())

    self.vl0.sort()
    self.vl = []
    self.vl.append( self.vl0[0] )
    self.vdict = { self.vl[0]:[] }
    for v in self.vl0[1:]:
      if v != self.vl[-1]:
        self.vl.append(v)
        self.vdict[v] = []
    self.al0.sort()
    self.al = [self.al0[0],]
    self.adict = { self.al[0]:[] }
    for v in self.al0[1:]:
      if v != self.al[-1]:
        self.al.append(v)
        self.adict[v] = []

    for t in self.tl:
      for k in t[2]:
        self.vdict[k].append(t[0])

## create list of tables for each dimension.
    for a in self.dl:
      for k in list(a[1].keys()):
        self.adict[k].append(a[0])

    self.dims = list(self.adict.keys())
    self.dims.sort()
    self.vars = list(self.vdict.keys())
    self.vars.sort()
    ##for v in self.vars:
      ##l = self.vdict[v]
      ##l.sort()
##  print v, l, td[l[0]][v][1].get('standard_name','__NO_STANDARD_NAME__')

class runcheck1:
  def __init__( self, m, thisatts, isAxes=False):
    self.errors = []
    if not isAxes:
      vars = m.vars
      vdict = m.vdict
      td = m.td
      ix = 1
      xxx = ''
    else:
      vars = m.dims
      vdict = m.adict
      td = m.dd
      ix = 0
      xxx = 'dim: '

    self.ix = ix
    self.vars = vars
    self.vdict = vdict
# dictionary td[tab][var][ix][attribute]
    self.td = td
    vd2 = {}
    for v in vars:
     l = vdict[v]
     l.sort()
     if len(l) > 1:
       for att in thisatts:
        if att != "__name__":
       ##for att in ['standard_name','units']:
         if att == '__dimensions__':
           atl = [string.join( td[x][v][0] ) for x in l]
         else:
           atl = [td[x][v][ix].get(att,'__ABSENT__') for x in l]
         atl.sort()
         av = [atl[0],]
         for a in atl[1:]:
           if a != av[-1]:
             av.append(a)
         if att == 'standard_name':
           for a in av:
             if a not in snl and a not in snla:
               print("ERROR[A1]: ",xxx,"INVALID STANDARD NAME: ",a,v)
               self.errors.append( "INVALID STANDARD NAME: %s [%s]" % (a,v) )
         if len(av) > 1:
           ee = {}
   
           for a in [True,False]:
             ee[a] = []
   
           isol = []
           for x in l:
             a = td[x][v][ix].get(att,'__ABSENT__')
             try:
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
             except:
               print(att,v)
               raise
             isol.append((iso,x))
             if tt[0]:
               print('INFO[Y1]: Substituting ',v,a,tt)
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
                print(xxx,'E001: Multiple values : ',att,v,ee)
                for t in isol:
                  if t[0] == a:
                    tab = t[1]
                    if att in ['standard_name','long_name']:
                      print("E002",xxx,tab,td[tab][v][ix].get('standard_name','__ABSENT__'),td[tab][v][ix].get('long_name','__ABSENT__'))
                    else:
                      print("E003",xxx,tab,td[tab][v][ix].get(att,'__ABSENT__'))
                   
           if att == "standard_name":
             vd2[v] = (2,[ee[True],ee[False]] )
         else:
           if att == "standard_name":
             tt = snsubber.isFalseSn( v, av[0] )
             if tt[0]:
               print('INFO[A2]: Substituting ',v,av[0],tt)
               vd2[v] = (1, tt[1])
             else:
               vd2[v] = (1, av)
     elif len(l) == 1:
           tab = vdict[v][0]
           a = td[tab][v][ix].get('standard_name','__ABSENT__')
           tt = snsubber.isFalseSn( v, a )
           if tt[0]:
             print('INFO[A3]: Substituting ',v,a,tt)
             vd2[v] = (1, tt[1])
           else:
             vd2[v] = (1, a)
           ##print 'MULTIPLE VALUES: ',v,att,av
     else:
      print("WARNING[X4]: ",xxx, 'Zero length element: %s' % v)

  def chkDims( self, reqh=None):
    pass
   
class typecheck1:
  def __init__( self, m, thisatts,helper=None):
    self.type2Atts = ['positive','comment', 'long_name', 'modeling_realm', 'out_name', 'standard_name', 'type', 'units', 'flag_meanings', 'flag_values']
    self.type3Atts = ['positive','long_name','modeling_realm', 'out_name', 'standard_name', 'type', 'units', 'flag_meanings', 'flag_values']
    self.type4Atts = ['positive','modeling_realm', 'out_name', 'standard_name', 'type', 'units', 'flag_meanings', 'flag_values']
    self.type2Atts = ['positive','comment', 'long_name', 'modeling_realm', 'out_name', 'standard_name', 'type', 'units']
    self.type3Atts = ['positive','long_name','modeling_realm', 'out_name', 'standard_name', 'type', 'units']
    self.type4Atts = ['positive','modeling_realm', 'standard_name', 'type', 'units']
    self.m = m
    vars = m.vars
    vdict = m.vdict
    self.helper=helper
    td = m.td
    vd2 = {}
    type1, type2, type3, type4, type5 = [[],[],[],[],[],] 
    vd2 = {}
    for v in vars:
     l = vdict[v]
     dl = [string.join( td[x][v][0] ) for x in l]
     vd2[v] = str( uniquify( dl ) )
    json.dump( vd2, open( 'mipInfo.json', 'w' ) )
    for v in vars:
     l = vdict[v]
     l.sort()
     if len(l) == 1: 
       type1.append(v)
     elif len(l) > 1:
       adict = {}
       for att in thisatts:
         if att == '__dimensions__':
           atl = [(string.join( td[x][v][0] ),x) for x in l]
         else:
           atl = [(td[x][v][1].get(att,'__ABSENT__'),x) for x in l]
         atl.sort( tupsort(0).cmp )
         a0 = atl[0][0]
         if a0 == None:
           a0 = ""
         av = [a0,]
         for a,tab in atl[1:]:
           if a == None:
             a = ""
           if a != av[-1]:
             if self.helper != None and self.helper.applycv:
               thisok=False
               pmatch = False
               for cond,src,targ in self.helper.canonvar:
                 if string.find(a,src) != -1 or  string.find(av[-1],src) != -1:
                   ##print 'Potential match ---- ',a
                   ##print src,'###',targ
                   ##print av[-1]
                   pmatch = True
                 if self.helper.checkCond( tab, v, cond ):
                   if self.helper.match(string.replace( a, src, targ ), av[-1]) or self.helper.match(string.replace( av[-1], src, targ ), a):
                     thisok = True
               if thisok:
                 print('INFO[typecheck]: conditional match found', tab, v)
               else:
                 if pmatch:
                   ##print '########### no matvh found'
                   pass
                 av.append(a)
             else:
               av.append(a)
         adict[att] = av
       
## check for type 2
       tval = None
       ##if adict[ 'positive' ] == ['__ABSENT__']:
       if all( [len(adict[x]) == 1 for x in self.type2Atts]):
           tval = 2
       elif all( [len(adict[x]) == 1 for x in self.type3Atts]):
           tval = 3
       elif all( [len(adict[x]) == 1 for x in self.type4Atts]):
           tval = 4
       else:
           l = ['%s:%s, ' % (x,len(adict[x]) ) for x in self.type2Atts]
       if tval == 2:
         type2.append( v)
       elif tval == 3:
         type3.append( v)
       elif tval == 4:
         type4.append( v)
       else:
         type5.append(v)
    xx = float( len(vars) )
    print("INFO[XXX]", string.join( ['%s (%5.1f%%);' % (x,x/xx*100) for x in [len(type1), len(type2), len(type3), len(type4), len(type5)]] ))
    self.type1 = type1
    self.type2 = type2
    self.type3 = type3
    self.type4 = type4
    self.type5 = type5

  def exportHtml( self, typecode ):

    allAtts = ['__dimensions__', 'cell_methods', 'comment', 'long_name', 'modeling_realm', 'out_name', 'standard_name', 'type', 'units', 'valid_max', 'valid_min', 'positive', 'ok_max_mean_abs', 'ok_min_mean_abs', 'flag_meanings', 'flag_values']
    fixedType1Tmpl = """:%(standard_name)s [%(units)s]</h3>
        %(__dimensions__)s<br/>
        %(long_name)s<br/>
       realm: %(modeling_realm)s; out_name: %(out_name)s; type: %(type)s, <br/>
       cell_methods: %(cell_methods)s; comment: %(comment)s<br/>
"""
    fixedType2TmplA = """:%(standard_name)s [%(units)s]</h3>
        %(long_name)s<br/>
       realm: %(modeling_realm)s; out_name: %(out_name)s; type: %(type)s, <br/>
       comment: %(comment)s<br/>
"""
    fixedType2TmplB = "<li>%s [%s]: %s -- (%s,%s,%s,%s)</li>\n"
        
    fixedType3TmplA = """:%(standard_name)s [%(units)s]</h3>
       realm: %(modeling_realm)s; out_name: %(out_name)s; type: %(type)s <br/>
"""
    fixedType3TmplB = "<li>%s [%s]: %s: %s [%s]</li>\n"
    fixedType4TmplB = "<li>%s [%s]: %s [%s]</li>\n"
    fixedType5TmplA = """ [%(units)s]</h3>
       out_name: %(out_name)s; type: %(type)s <br/>
"""
    fixedType5TmplB = "<li>%s [%s]: %s, %s [%s]: %s, %s:: %s, %s</li>\n"
        
    if typecode == 1:
      oo = open( 'type1.html', 'w' )
      self.type1.sort()
      ee = {}
      for v in self.type1:
        tab = self.m.vdict[v][0]
        if tab not in ee:
          ee[tab] = []
        ee[tab].append( v )
      keys = list(ee.keys())
      keys.sort()
      for k in keys:
         oo.write( '<h2>Table %s</h2>\n' % k )
         for v in ee[k]:
            try:
              etmp = {}
              for a in allAtts:
                etmp[a] = self.m.td[k][v][1].get( a, 'unset' )
              etmp['__dimensions__'] = string.join( self.m.td[k][v][0] )
              oo.write( '<h3>' + v + (fixedType1Tmpl % etmp) )
            except:
              print(k, list(self.m.td[k][v][1].keys()))
              raise
      oo.close()
    elif typecode == 2:
      oo = open( 'type2.html', 'w' )
      self.type2.sort()
      oo.write( '<h2>Variables with fixed attributes</h2>\n' )
      for v in self.type2:
            l = self.m.vdict[v]
            etmp = {}
            for a in allAtts:
                etmp[a] = self.m.td[l[0]][v][1].get( a, 'unset' )
            oo.write( '<h3>' + v + (fixedType2TmplA % etmp) )
            oo.write( '<ul>\n' )
            for t in l:
              dims = string.join( self.m.td[t][v][0] )
              sa = tuple( [t,dims,] + [self.m.td[t][v][1].get( x, 'unset' ) for x in ['cell_methods','valid_max', 'valid_min', 'ok_max_mean_abs', 'ok_min_mean_abs']] )
              oo.write( fixedType2TmplB % sa )
            oo.write( '</ul>\n' )
      oo.close()
           
    elif typecode in [3,4,5]:
      oo = open( 'type%s.html' % typecode, 'w' )
      thistype,h2,al,tmplA,tmplB = { 3:(self.type3,"Variables with varying comment",['long_name','comment','cell_methods'], fixedType3TmplA, fixedType3TmplB),
                      4:(self.type4,"Variables with varying long_name",['long_name','cell_methods'],fixedType3TmplA, fixedType4TmplB),
                      5:(self.type5,"Remaining variables",['standard_name','long_name','out_name', 'modeling_realm','positive','type','units'],fixedType5TmplA, fixedType5TmplB) }[typecode]
 ##['positive','modeling_realm', 'out_name', 'standard_name', 'type', 'units']
      thistype.sort()
      oo.write( '<h2>%s</h2>\n' % h2 )
      for v in thistype:
            l = self.m.vdict[v]
            etmp = {}
            for a in allAtts:
                etmp[a] = self.m.td[l[0]][v][1].get( a, 'unset' )
            oo.write( '<h3>' + v + (tmplA % etmp) )
            oo.write( '<ul>\n' )
            for t in l:
              dims = string.join( self.m.td[t][v][0] )
              sa = tuple( [t,dims,] + [self.m.td[t][v][1].get( x, 'unset' ) for x in al] )
              oo.write( tmplB % sa )
            oo.write( '</ul>\n' )
      oo.close()
           
class run(object):

  def __init__(self):
    pass

  def  run(self):
    self.m = mipCo( mips )  
    self.json()
    al = []
    for k0 in list(self.m.dd.keys()):
      for k1 in list(self.m.dd[k0].keys()):
        al += list(self.m.dd[k0][k1][0].keys())
    ald = uniquify( al )
    ald.sort()
    i = ald.index('standard_name')
    ald.pop(i)
    ald = ['standard_name', ] + ald
    self.ald = ald

    return self.m,ald

  def getTupList(self):
    vl = []
    keys = list(self.m.vdict.keys())
    keys.sort()
    for k in keys:
      for t in self.m.vdict[k]:
  ##NT_var = collections.namedtuple( 'mip',['name','sn','snStat','realm','units','longName','comment'] )
        sn, r, units, ln, c = [self.m.td[t][k][1].get(x,None) for x in ['standard_name','modeling_realm','units','long_name','comment']] 
        mipid = string.split(t,'_')[0]
        if c == '':
          c = None
        v = NT_var( k, sn, 'exists', r, units, ln, c,mipid )
        vl.append(v)
    self.tupList = vl
    return vl

  def compTupList(self):
    tl1 = uniquify(self.tupList)
    tl2 = [tl1[0],]
###  these lines comment on all differences of variables with the same name, including differences in comments.
    for t in tl1[1:]:
      if t[:7] == tl2[-1][:7]:
        pass
      elif t[:3] == tl2[-1][:3] and t[4:6] == tl2[-1][4:6]:
        if (t.mip == 'CMIP5' and tl2[-1].mip == 'CCMI1') or (t.mip == 'CCMI1' and tl2[-1].mip == 'CMIP5'):
          tl2[-1] = t
        else:
          print('What to do??')
          print(tl2[-1])
          print(t)
      else:
        tl2.append(t)
    return tl1, tl2

  def runchecks(self):
    self.v = runcheck1( self.m, self.ald, isAxes=False )
## check consistency of dimension
    self.r2 = runcheck1( self.m, self.ald, isAxes=True )
    return self.v, self.r2

  def json(self):
    keys = list(self.m.adict.keys())
    keys.sort()
    fh = open( 'axes_json.txt', 'w' )
    for k in keys:
      ee = self.m.dd[self.m.adict[k][0]][k][0]
      ee["__name__"] = k
      fh.write( json.dumps( ee ) + '\n' )
    fh.close()

ms = mipTableScan()
print(ms.al)
snc = snlist()
snl, snla = snc.gen_sn_list( )
snsubber = snsub()

mips = { "cmip5":NT_mip( 'cmip5','cmip5_vocabs/mip/', 'CMIP5_*' ),
"ccmi":NT_mip( 'ccmi', 'ccmi_vocabs/mip/', 'CCMI1_*'),
"pmip":NT_mip( 'pmip', 'pmip3_vocabs/mip/', 'PMIP3_*'),
"cordex":NT_mip( 'cordex', 'cordex_vocabs/mip/', 'CORDEX_*'),
"specs":NT_mip( 'specs', 'specs_vocabs/mip/', 'SPECS_*') }

mipl = ['specs']
mipl = ['cordex','cmip5']
mipl = list(mips.keys())
mips = [mips[x] for x in mipl]
r = run()

m,ald = r.run()

tl = r.getTupList()
tl1,tl2 = r.compTupList()
v,r2 = r.runchecks()

allatts = ms.al
thisatts = ['standard_name','units','long_name','__dimensions__']
## need to have standard name first.
for a in allatts:
  if a not in thisatts:
    thisatts.append(a)

h = helper()
s = typecheck1( m, thisatts, helper=h)
s.exportHtml( 1 )
s.exportHtml( 2 )
s.exportHtml( 3 )
s.exportHtml( 4 )
s.exportHtml( 5 )

import collections
ee = collections.defaultdict( int )
## e.m.td['CMIP5_6hrPlev']['va'][1].keys()
for k1 in list(m.td.keys()):
  for k2 in list(m.td[k1].keys()):
    for k3 in list(m.td[k1][k2][1].keys()):
      ee[k3] += 1
