from fcc_utils2 import mipTableScan
from ceda_cc_config.config_c4 import CC_CONFIG_DIR
import re, os, string

ml = ['CORDEX_3h', 'CORDEX_6h', 'CORDEX_Aday', 'CORDEX_day', 'CORDEX_grids', 'CORDEX_mon' ]
ml = ['CORDEX_3h', 'CORDEX_6h', 'CORDEX_fx', 'CORDEX_day', 'CORDEX_mon', 'CORDEX_sem' ]
newMip = 'SPECS'
newMip = 'CORDEX'
newMip = 'CCMI'
ml2 = ['CMIP5_3hr', 'CMIP5_6hrPlev', 'CMIP5_Amon', 'CMIP5_cfDay', 'CMIP5_cfOff', 'CMIP5_day', 'CMIP5_grids', 'CMIP5_Lmon', 'CMIP5_OImon', 'CMIP5_Oyr',
       'CMIP5_6hrLev', 'CMIP5_aero', 'CMIP5_cf3hr', 'CMIP5_cfMon', 'CMIP5_cfSites', 'CMIP5_fx', 'CMIP5_LImon', 'CMIP5_Oclim', 'CMIP5_Omon'] 
ml2 = ['CMIP5_3hr', 'CMIP5_6hrPlev', 'CMIP5_Amon', 'CMIP5_cfDay', 'CMIP5_cfOff', 'CMIP5_day', 'CMIP5_grids', 'CMIP5_Lmon',
       'CMIP5_6hrLev', 'CMIP5_aero', 'CMIP5_cf3hr', 'CMIP5_cfMon', 'CMIP5_cfSites', 'CMIP5_fx', 'CMIP5_LImon'] 

cfsntab = 'cf/cf-standard-name-table.xml'
cordex_dkrz = 'CORDEX_variables_requirement_table_upgedated-1.csv'
cordex_dkrz = 'CORDEX_variables_requirement_table_all.csv'
cordex_dkrz_pat = 'cordex_dkrz/CORDEX_variables_requirement_table_%s.csv'
cordex_dkrz_pat = 'cordex_dkrz_oct/CORDEX_variables_requirement_table_%s.csv'
re_sn = re.compile( 'entry id="(.*)"' )
re_snax = re.compile( '</alias>' )
re_snar = re.compile( '<entry_id>(.*)<' )
re_sna = re.compile( 'alias id="(.*)"' )
##alias id="atmosphere_water_vapor_content"
##entry id="age_of_sea_ice"'
def gen_sn_list( pathn ):
  assert os.path.isfile( pathn ), '%s not found ' % pathn
  inAlias = False
  snl = []
  snla = []
  aliasses = {}
  for l in open(pathn).readlines():
    m = re_sn.findall(l )
    if len(m) > 0:
      for i in m:
        snl.append( i )
    m = re_sna.findall(l )
    if len(m) > 0:
      inAlias = True
      for i in m:
        snla.append( i )
    if inAlias:
      m = re_snax.findall(l )
      if len(m) > 0:
        inAlias = False
      else:
        m = re_snar.findall(l )
        if len(m) > 0:
          aliasses[snla[-1]] = m[0]
          assert len(m) == 1, 'Unexpected length of results, %s [%s]' % (str(m),l)
  ##<alias id="station_wmo_id">
    ##<entry_id>platform_id</entry_id>
  ##</alias>
  return (snl,snla,aliasses)

def tlist_to_dict( ll ):

   ee = {} 
   for l in ll:
     ee[l[0]] = ( l[1], l[2] )
   return ee

class comp(object):

  def __init__(self, snl, snla=None, ec1=None,tag=None):
    self.id = 'comp'
    self.snl = snl
    self.snla = snla
    self.ec1 = ec1
    self.tag=tag


  def comp(self, e1, e2,checkCellMethods=False,tag=None ):
    self.tag=tag
    
    ##e1 = tlist_to_dict( t1 )
    ##e2 = tlist_to_dict( t2 )
    self.nn_sn = 0
    thisSnl = []

    checkAll = True
    keys = e1.keys()
    keys.sort()
    self.nn_var = len(keys)
    for k in keys:
      e0 = 0
      f2 = False
      f3 = False
      f4 = False
      if e1[k][1]['standard_name'] in [None,'None']:
        if e1[k][1].get('long_name',None) not in [None,'None']:
          print 'WARNING[A]: standard name for %s [%s] not set' % (k,e1[k][1].get('long_name') )
        else:
          print 'WARNING[A]: standard name for %s not set' % k
      else:
        if e1[k][1]['standard_name'] not in self.snl:
          if e1[k][1]['standard_name'] not in self.snla:
            print 'ERROR[0]: standard name %s for %s [%s] not in snl or snla' % (e1[k][1]['standard_name'], k, e1[k][2] )
          else:
            print 'WARNING: standard name %s for %s not in snl' % (e1[k][1]['standard_name'], k )
            if e1[k][1]['standard_name'] not in thisSnl:
               thisSnl.append( e1[k][1]['standard_name'] )
        else:
            if e1[k][1]['standard_name'] not in thisSnl:
               thisSnl.append( e1[k][1]['standard_name'] )

      if self.ec1 != None:
        if k not in self.ec1.keys():
          print 'ERROR[1]: variable %s [%s] not in CORDEX variable requirements list' % (k,e1[k][2])
          vrln = None
        else:
          vrln = self.ec1[k][1]
          if e1[k][1]['long_name'] != self.ec1[k][1]:
            f2 = True
          if checkCellMethods:  
            if e1[k][1]['cell_methods'] != self.ec1[k][3]:
              if not (e1[k][1]['cell_methods']=="None" and string.strip(self.ec1[k][3]) == "time:"):
                f3 = True
          if checkAll:  
            if (e1[k][1].has_key( 'positive' ) and self.ec1[k][4] == '') or ( (not e1[k][1].has_key( 'positive' )) and self.ec1[k][4] != ''):
                f4 = True
            elif e1[k][1].has_key( 'positive' ):
              if e1[k][1]['positive'] != self.ec1[k][4]:
                if not (e1[k][1]['positive']=="None" and string.strip(self.ec1[k][4]) == ""):
                  f4 = True
            if (e1[k][1].has_key( 'modeling_realm' ) and self.ec1[k][5] == '') or ( (not e1[k][1].has_key( 'modeling_realm' )) and self.ec1[k][5] != ''):
                f4 = True
            elif e1[k][1].has_key( 'modeling_realm' ):
              if e1[k][1]['modeling_realm'] != self.ec1[k][5]:
                if not (e1[k][1]['modeling_realm']=="None" and string.strip(self.ec1[k][5]) == ""):
                  f4 = True
        
      self.nn_sn = len(thisSnl)
      cks = ['units', 'long_name', 'standard_name']
      suppress4B = True
      if k in e2.keys():
        if e1[k][1] != e2[k][1]:
          ne1 = 0
          nmm = []
          for k2 in cks:
             if e1[k][1][k2] != e2[k][1][k2]:
                ne1 += 1
                nmm.append(k2)
          if ne1 > 0:
                v1 = map( lambda x: e1[k][1][x], nmm )
                v2 = map( lambda x: e2[k][1][x], nmm )
                ##if k == 'clivi':
                  ##print k, nmm, v1, v2
                  ##print snaliasses.keys()
                  ##print snaliasses.get(v1[0],'xxx')
                  ##print snaliasses.get(v2[0],'xxx')
                  ##raise
                weakmatch = False
                if nmm[0] == 'standard_name':
                  if snaliasses.get(v1[0],'xxx') == v2[0] or snaliasses.get(v2[0],'xxx') == v1[0]:
                    weakmatch = True
                if weakmatch:
                  print 'WARNING[4A*]: Anomaly between MIP tables: %s:: %s -- %s -- %s {%s} ' % (k, str(nmm), str(v1), str(v2), tag )
                else:
                  print 'ERROR[4A]: Anomaly between MIP tables: %s:: %s -- %s -- %s {%s} ' % (k, str(nmm), str(v1), str(v2), tag )
          else:
             if not suppress4B:
                print 'ERROR[4B]: Anomaly between MIP tables: %s:: %s -- %s [%s]' % (k, str(e1[k][1]), str( e2[k][1] ), vrln )
          e0 = 1
        else:
          ##print '%s OK -- %s -- %s' % (k,str(e1[k][1]), str( e2[k][1] ) )
          e0 = 2
      else:
        ##print '%s not in table 2' % k
        e0 = 3

      xxx = k
      if self.tag != None:
         xxx += '[%s]' % self.tag
      if self.ec1 != None:
        if f2 and (e0 == 2):
           print 'ERROR[2]: Difference between CORDEX/CMIP5 MIP tables and VR: %s:: %s [%s] --- %s' % (k,e1[k][1]['long_name'],e1[k][2], self.ec1[k][1])
        elif f2 and (e0 == 3):
           print 'ERROR[3]: Difference between CORDEX MIP tables and VR: %s:: %s [%s] --- %s' % (k,e1[k][1]['long_name'],e1[k][2], self.ec1[k][1])
        elif f2:
           print 'ERROR[5]: Difference between CORDEX MIP tables and VR %s: %s --- %s' % (xxx,e1[k][1]['long_name'], self.ec1[k][1])
        if f3:
           print 'ERROR[6]: Difference between CORDEX MIP tables and VR in cell_methods: %s:: %s --- %s' % (k,e1[k][1]['cell_methods'], self.ec1[k][3])
        if f4:
           print 'ERROR[7]: Difference between CORDEX MIP tables and VR in positive, realm: %s:: %s,%s --- %s' % (xxx,e1[k][1].get('positive','None'),e1[k][1].get('modeling_realm','None'), self.ec1[k][4:6])
        
base=CC_CONFIG_DIR
print base
snl,snla, snaliasses = gen_sn_list( os.path.join(base, cfsntab) )
print 'Len snl = %s' % len(snl)

dkrz_cordex_version = 4
ec1 = {}
if newMip == 'CORDEX':
 if dkrz_cordex_version == 1:
  ll = open( os.path.join(base, cordex_dkrz) ).readlines()
  for l in ll[9:74]:
    bits = string.split( l, ',' )
    var = bits[1]
    ln = bits[13]
    sn = bits[14]
    if sn not in snl + snla:
      print 'ERROR: CORDEX DKRZ sn %s for %s not in snl/snla' % (sn, var)
    ec1[var] = ( sn,ln)
 elif dkrz_cordex_version == 2:
  for tab in ['3hr','6hr','day','mon','sem','fx']:
     ll = open( os.path.join(base, cordex_dkrz_pat % tab) ).readlines()
     for l in ll[3:]:
        bits = string.split( l, ',' )
        if (tab != 'fx' and len( bits ) != 7) or (tab == 'fx' and len( bits ) != 5):
          print 'cant safely parse %s [%s]' % (l,tab)
#1,sund,Duration of Sunshine,duration_of_sunshine,s,sum,
        var,ln,sn,units = bits[1:5]
        if tab != 'fx':
          cm,pos = bits[5:7]
        else:
          cm,pos = [None,None]
        if sn not in snl + snla:
           print 'ERROR: CORDEX DKRZ [%s] sn %s for %s not in snl/snla' % (tab,sn, var)
        ec1[var] = ( sn,ln,units,cm,pos)
 elif dkrz_cordex_version in [3,4]:
  eeee = {}
  eca = {}
  ll = open( os.path.join(base, cordex_dkrz_pat % 'all') ).readlines()
  for l in ll[2:]:
        bits = string.split( string.strip(l), ',' )
        if dkrz_cordex_version == 4:
          bits = map( lambda x: string.strip(x, '"' ), bits)
        if string.strip(bits[0]) == '':
           break
#1,sund,Duration of Sunshine,duration_of_sunshine,s,sum,
        var,units = bits[1:3]
        ln,sn,pos,realm   = bits[12:16]
        if sn not in snl + snla:
           print 'ERROR: CORDEX DKRZ [%s] sn %s for %s not in snl/snla' % ('all',sn, var)
        assert pos in ['','up','down'], 'Unexpected value for pos [%s] in %s' % (pos,l)
        eca[var] = ( units,ln,sn,pos,realm )

  for tab in ['3hr','6hr','day','mon','sem','fx']:
     ee  = {}
     ll = open( os.path.join(base, cordex_dkrz_pat % tab) ).readlines()
     for l in ll[2:]:
        bits = string.split( l, ',' )
        if dkrz_cordex_version == 4:
          bits = map( lambda x: string.strip(x, '"' ), bits)
        if string.strip(bits[0]) == '':
           break
#1,sund,Duration of Sunshine,duration_of_sunshine,s,sum,
        var,cm = bits[1:3]
        cm = 'time: ' + cm
        units,ln,sn,pos,realm = eca[var] 
        ec1[var] = ( sn,ln,units,cm,pos,realm)
        ee[var] = ( sn,ln,units,cm,pos,realm)
     eeee[tab] = ee

if newMip == 'SPECS':
  newMipDir = 'specs_vocabs/mip/'
  mpat = 'SPECS_%s'
  ml = ['SPECS_Amon', 'SPECS_fx', 'SPECS_Lmon', 'SPECS_Omon', 'SPECS_6hrLev', 'SPECS_day', 'SPECS_OImon']
elif newMip == 'CCMI':
  ml = ['CCMI1_Amon_v2_complete']
  ml = ['CCMI1_annual_comp-v3.txt', 'CCMI1_daily_comp-v3.txt', 'CCMI1_fixed_comp-v2.txt', 'CCMI1_hourly_comp-v3.txt', 'CCMI1_monthly_comp-v3.txt']
  ml = ['CCMI1_satdaily', 'CCMI1_annual', 'CCMI1_daily', 'CCMI1_fixed', 'CCMI1_hourly', 'CCMI1_monthly']
  mpat = 'CCMI1_%s_v1_complete'
  newMipDir = 'ccmi1-cmor-tables/Tables/'
  newMipDir = 'ccmi_vocabs/mip/'
elif newMip == 'CORDEX':
  newMipDir = 'cordex_vocabs/mip/'
  mpat = 'CORDEX_%s'

def validate( t,cc ):
  if t == 'all':
    l1 = {}
    l2 = {}
    for m in ml:
      print 'base: ',base
      l1 = ms.scan_table( open( os.path.join(base, newMipDir + m) ).readlines(), None, asDict=True, appendTo=l1, lax=True, tag=m, project=newMip)
    ms.nn_tab = len(ml)
    for m in ml2:
      l2 = ms.scan_table( open( os.path.join(base, 'cmip5_vocabs/mip/' + m) ).readlines(), None, asDict=True, appendTo=l2, lax=True, tag=m, warn=False)
    ms.nn_tab2 = len(ml2)
    ccm = False
    tag = " vs. cmip5"
  else:
    l2 = {}
    for m in ml2:
      l2 = ms.scan_table( open( os.path.join(base, 'cmip5_vocabs/mip/' + m) ).readlines(), None, asDict=True, appendTo=l2, lax=True, tag=m, warn=False)
    k = { '3hr':'3h', '6hr':'6h' }.get( t,t )
    l1 = ms.scan_table( open( os.path.join(base, newMipDir + mpat % k) ).readlines(), None, asDict=True, project=newMip)
    ccm = True
    tag = t
  cc.comp( l1, l2, checkCellMethods=ccm, tag=tag )

tlist = ['3hr','6hr','day','mon','sem','fx']
tlist = ['Amon']
tlist = ['Amon', 'fx', 'Lmon', 'Omon', '6hrLev', 'day', 'OImon']
doAll = True
if doAll:
    ms = mipTableScan()
    ec1 = None
    c = comp( snl,snla=snla, ec1=ec1)
    validate('all',c)
    print """Number of tables=%s\nNumber of variables=%s\nNumber of standard names=%s\n""" % (ms.nn_tab,c.nn_var,c.nn_sn)
    print ms.al
else:
  for tab in tlist:
    ms = mipTableScan()
    print 'Validating table %s ' % tab
    if newMip in ['CCMI','SPECS']:
      ec1 = None
    else:
      ec1=eeee[tab]
      print eeee[tab].keys()
    c = comp( snl,snla=snla, ec1=ec1)
    validate(tab,c)
