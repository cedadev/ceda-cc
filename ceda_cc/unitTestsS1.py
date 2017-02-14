
import collections
import os.path as op
import logging, time, string
import utils_c4
import ceda_cc_config.config_c4 as config


#### set up log file ####
tstring2 = '%4.4i%2.2i%2.2i' % time.gmtime()[0:3]
testLogFile = '%s__qclog_%s.txt' % ('unitTests',tstring2)
log = logging.getLogger(testLogFile)
fHdlr = logging.FileHandler(testLogFile,mode='w')
fileFormatter = logging.Formatter('%(message)s')
fHdlr.setFormatter(fileFormatter)
log.addHandler(fHdlr)
log.setLevel(logging.INFO)

class dummy(object):

  def __init__(self):
     pass

p = dummy()
ps = dummy()
pcmip5 = dummy()
pccmi = dummy()
pcci = dummy()
for x in (p,ps,pcmip5,pccmi,pcci):
  x.log = log
  x.abortMessageCount = -1
  x.experimental = False
p.pcfg = config.projectConfig( "CORDEX" )
ps.pcfg = config.projectConfig( "SPECS" )
pcmip5.pcfg = config.projectConfig( "CMIP5" )
pccmi.pcfg = config.projectConfig( "CCMI" )
pcci.pcfg = config.projectConfig( "ESA-CCI" )

cfgd = { 'CORDEX':p, 'SPECS':ps, 'CMIP5':pcmip5, 'CCMI':pccmi, 'ESA-CCI':pcci }

fnlist = """CORDEX ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_day_20060101-20101231.nc True
CORDEX ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_fx.nc True  fixed
CORDEX ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_3hr_2006010100-2010123100.nc True
CORDEX ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_3hr_200601010030-201012310030.nc True
CORDEX ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_day_200601010030-201012310030.nc False
CMIP5 pr_3hr_HadGEM2-ES_historical_r2i1p1_196001010130-196412302230.nc True
CMIP5 pr_3hr_HadGEM2-ES_historical_r2i1p1.nc False
CCMI clivi_monthly_CESM1-CAM4Chem_refC1sd_r1i1p1_197501-197912.nc True
CCMI areacella_fixed_SOCOL3_refC1_r0i0p0.nc True
SPECS orog_fx_EC-EARTH3_seaIceClimInit_S19930501_r0i0p0.nc True fixed
SPECS tas_Amon_EC-EARTH3_seaIceClimInit_series2_S19930501_r1i1p1_199306-199306.nc False
SPECS tas_Amon_EC-EARTH3_seaIceClimInit_S19930501_r1i1p1_199306-199306.nc True
SPECS tas_Amon_EC-EARTH3_seaIceClimInit_S19930501_r1i1p1_199306-199305.nc False
ESA-CCI 20120101015548-ESACCI-L3U_GHRSST-SSTskin-AATSR-LT-v02.0-fv01.1.nc True CCIplus
ESA-CCI ESACCI-OC-L3S-OC_PRODUCTS-MERGED-1M_MONTHLY_4km_GEO_PML_OC4v6_QAA-200005-fv1.0.nc True CCIplus
ESA-CCI 20120101015548-ESACCI-L3U-GHRSST-SSTskin-AATSR-LT-v02.0-fv01.1.nc False
ESA-CCI 20120101015548-ESACCI-L3U_GHRSST-SSTskin-AATSR-LT-v02.0-fv.1.nc False"""
fntl = map( lambda x: tuple( string.split(x) ), string.split( fnlist, '\n' ) )
ee = collections.defaultdict( list )
for t in fntl:
  ee[t[0]].append( t[1:] )

cga = utils_c4.checkGlobalAttributes(parent=cfgd['ESA-CCI'])
module = 'checkFileName'
keys = ee.keys()
keys.sort()
kk = 0
for k in keys:
  c = utils_c4.checkFileName(parent=cfgd[k])
  for l in ee[k]:
    fn = l[0]
    isValid = l[1] == 'True'
    if len(l) > 2:
      chckFx = l[2] == 'fixed'
    else:
      chckFx = False
    kk += 1
    testId = '#01.%3.3i' % kk
    c.check( fn )
    passed = c.errorCount == 0
    if chckFx:
      passed &= c.isFixed
    ok = (isValid == passed)
    vstr = { True:'Valid', False:'Invalid' }[isValid]
    pstr = { True:'passed', False:'rejected' }[passed]
    if ok:
      print 'OK: [%s] %s: %s %s file name %s' % (testId,fn,vstr,k,pstr)
      if len(l) > 2 and l[2]  == 'CCIplus':
        cga.globalAts =  {'platform':'platform','sensor':'sensor', \
                'naming_authority':'org.ghrsst', 'id':'AATSR-ESACCI-L3U-v1', \
                'spatial_resolution':'1 km'}
        cga.varAts = { 'var':{ 'standard_name':'dummy'} }
        cga.var = 'var'
        cga.completed = True
        ee1 = cga.getDrs()
        if ee1['ecv'] in ['Sea Surface Temperature','Ocean Colour']:
          print 'OK: [%sb] %s: DRS dictionary generated (%s)' % (testId,fn,ee1['ecv'])
        else:
          print 'Failed: [%sb] %s: DRS dictionary not generated correctly (%s)' % (testId,fn,ee1['ecv'])
 
        if c.group == 'ESACCI':
          print 'OK: group ESACCI detected' 
        else:
          print 'Failed: group read as "%s" (not ESACCI) %s' % (c.group,fn)
        
    else:
      print 'Failed: [%s] %s: %s %s file name %s' % (testId,fn,vstr,k,pstr)

c = utils_c4.checkStandardDims(parent=p)
module = 'checkStandardDims'
## note last argument is "vocabs", but only used in "experimental" mode
c.check( 'tas', 'day', {},{}, False, None )
if c.errorCount == 0:
  print 'Failed [%s]: failed to detect empty dictionaries' % module
else:
  print 'OK: -- detected error in standard dims'

c = utils_c4.checkByVar(parent=p)
module = 'checkByVar (regex)'
c.check( norun=True )
import re
r1 = re.compile( c.pats['subd'][0] )
for x in ['200401010000','2004010100']:
  m = r1.match( x )
  if m:
     print 'OK: -- passed [%s] %s for sub-daily data' % (module,x)
  else:
     print 'Failed to match correct sub-daily time range element [%s] %s' % (module,x)

for x in ['200401010040','2004010200']:
  m = r1.match( x )
  if not m:
     print 'OK: -- correctly failed [%s] %s for sub-daily data' % (module,x)
  else:
     print 'Failed to detect bad sub-daily time range element [%s] %s' % (module,x)

r1 = re.compile( c.pats['sem'][0] )
for x in ['199012','199101']:
  m = r1.match( x )
  if m:
     print 'OK: -- passed [%s] %s for seasonal data' % (module,x)
  else:
     print 'Failed to match correct seasonal time range element [%s] %s' % (module,x)

for x in ['199011','199112']:
  m = r1.match( x )
  if not m:
     print 'OK: -- correctly failed [%s] %s for seasonal data' % (module,x)
  else:
     print 'Failed to detect bad seasonal time range element [%s] %s' % (module,x)

r1 = re.compile( c.pats['mon'][0] )
for x in ['199101']:
  m = r1.match( x )
  if m:
     print 'OK: -- passed [%s] %s for daily data' % (module,x)
  else:
     print 'Failed to match correct daily time range element [%s] %s -- %s' % (module,x,c.pats['day'][0])


c = utils_c4.checkGrids(parent=p)
c.interpolatedGrids = config.interpolatedGrids

lat = map( lambda x: -46.25 + x*0.5, range(185) )
lon = map( lambda x: -25.25 + x*0.5, range(173) )
da = {'lat':{'_data':lat,'units':'degrees_north','long_name':'latitude','standard_name':'latitude','_type':'float64'}, 'lon':{'_data':lon,'units':'degrees_east','long_name':'longitude','standard_name':'longitude','_type':'float64'} }
c.check( 'tas','AFR-44i', da, {'tas':{} } )
if c.errorCount == 0:
  print 'OK: -- passed a correct grid'
else:
  print 'Failed -- reported errors on correct grid'
lat = map( lambda x: -46.25 + x*0.5, range(180) )
lon = map( lambda x: -25.25 + x*0.5, range(172) )
da = {'lat':{'_data':lat,'units':'degrees_north','long_name':'latitude','standard_name':'latitude','_type':'float64'}, 'lon':{'_data':lon,'units':'degrees_east','long_name':'longitude','standard_name':'longitude','_type':'float64'} }
c.check( 'tas','AFR-44i', da, {'tas':{} } )
if c.errorCount == 0:
  print 'Failed -- passed a bad grid'
else:
  print 'OK: -- detected a bad grid'

##ii = open( op.join(config.CC_CONFIG_DIR, 'specs_vocabs/globalAtsSample001.txt') )
def readSampleGa( ifile ):
  ii = open( op.join(config.CC_CONFIG_DIR, ifile) )
  fn = string.strip( ii.readline() )
  res = string.strip( ii.readline() )
  ga = {}
  for l in ii.readlines():
    bits = string.split( string.strip(l) )
    if bits[1] == '@int':
      ga[bits[0]] = int( bits[2] )
    else:
      ga[bits[0]] = string.join( bits[1:] )
  return res, fn, ga

gafile = 'specs_vocabs/globalAtsSample001.txt'
res, fn, ga = readSampleGa( gafile )

testId = '#04.001'
## switch to project = SPECS
c = utils_c4.checkFileName(parent=ps)
c.check( fn )
if c.errorCount == 0:
  print 'OK: [%s] %s: valid file name' % (module,fn)
else:
  print 'Failed [%s] %s: valid file name' % (module,fn)

## note test is done on string'ed values.
va = { "tas":{ "_type":"float32", "standard_name":"air_temperature", 'long_name':'Air Temperature', 'units':'K', 'cell_methods':'time: mean'} }

testId = '#04.002'
cga = utils_c4.checkGlobalAttributes( parent=ps,cls='SPECS')
cga.check( ga, va, "tas", "day", ps.pcfg.vocabs, c.fnParts )
if cga.errorCount == 0:
  print 'OK: [%s]: global attributes check (%s)' % (testId,gafile)
else:
  print 'Failed [%s]: global attributes check (%s)' % (testId,gafile)

gafile = 'specs_vocabs/globalAtsSample002.txt'
res, fn, ga = readSampleGa( gafile )
testId = '#04.003'
## switch to project = SPECS
c = utils_c4.checkFileName(parent=ps)
c.check( fn )
if c.errorCount == 0:
  print 'OK: [%s] %s: valid file name' % (testId,fn)
else:
  print 'Failed [%s] %s: valid file name' % (testId,fn)

## note test is done on string'ed values.

va = { "tas":{ "_type":"float32", "standard_name":"air_temperature", 'long_name':'Air Temperature', 'units':'K', 'cell_methods':'time: mean'} }

testId = '#04.004'
cga = utils_c4.checkGlobalAttributes( parent=ps,cls='SPECS')
cga.check( ga, va, "tas", "day", ps.pcfg.vocabs, c.fnParts )
if cga.errorCount == 0:
  print 'Failed: [%s]: passed bad global attributes (%s)' % (testId,gafile)
else:
  print 'OK: [%s]: detected bad global attributes (%s)' % (testId,gafile)

gafile = 'esacci_vocabs/sampleGlobalAts.txt'
res, fn, ga = readSampleGa( gafile )
testId = '#04.005'
## switch to project = ESA-CCI
c = utils_c4.checkFileName(parent=pcci)
c.check( fn )
if c.errorCount == 0:
  print 'OK: [%s] %s: valid file name' % (testId,fn)
else:
  print 'Failed [%s] %s: valid file name' % (testId,fn)

## note test is done on string'ed values.

va = { "burned_area":{ "_type":"float32", "standard_name":"burned_area"} }

testId = '#04.004'
cga = utils_c4.checkGlobalAttributes( parent=pcci,cls='ESA-CCI')
cga.check( ga, va, "burned_area", "ESACCI", pcci.pcfg.vocabs, c.fnParts )
if cga.errorCount == 0:
  print 'Failed: [%s]: passed bad global attributes (%s)' % (testId,gafile)
else:
  print 'OK: [%s]: detected bad global attributes (%s)' % (testId,gafile)

ls = utils_c4.listControl('test',['a','b','c1','c2'],split=True,splitVal=',',enumeration=True)
testId = '#05.001'
res = ls.essplit.findall( 'a, b, c<1,2>')
if res == ['a', 'b', 'c<1,2>']:
  print 'OK: [%s] Split of list with enumeration passed' % (testId)
else:
  print 'Failed: [%s] Split of list with enumeration failed %s' % (testId,str(res))

testId = '#05.002'
res = ls.check( 'a, c<1,2>' )
if res:
  print 'OK: [%s] Valid value passed' % (testId)
else:
  print 'Failed: [%s] valid value rejected %s' % (testId,str(res))

testId = '#05.003'
res = ls.check( 'a, c<1,3>' )
if res:
  print 'Failed: [%s] Invalid value passed' % (testId)
else:
  print 'OK: [%s] Invalid value rejected %s' % (testId,str(res))


testId = '#06.001'
pc = utils_c4.patternControl( 'pattern test', 'ISO8601 duration', cls='ISO' )
res = pc.check( 'P1Z' )
if res:
  print 'Failed: [%s] Invalid value passed' % (testId)
else:
  print 'OK: [%s] Invalid value rejected %s' % (testId,str(res))
res = pc.check( 'P1W' )
if res:
  print 'OK: [%s] Valid value passed' % (testId)
else:
  print 'Failed: [%s] Valid value rejected %s' % (testId,str(res))

