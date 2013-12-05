

import logging, time
import utils_c4
import config_c4 as config


#### set up log file ####
tstring2 = '%4.4i%2.2i%2.2i' % time.gmtime()[0:3]
testLogFile = '%s__qclog_%s.txt' % ('unitTests',tstring2)
log = logging.getLogger(testLogFile)
fHdlr = logging.FileHandler(testLogFile,mode='w')
fileFormatter = logging.Formatter('%(message)s')
fHdlr.setFormatter(fileFormatter)
log.addHandler(fHdlr)
log.setLevel(logging.INFO)

class dummy:

  def __init__(self):
     pass

p = dummy()
p.log = log
p.pcfg = config.projectConfig( "CORDEX" )


module = 'checkFileName'
c = utils_c4.checkFileName(parent=p)

fn = 'ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_day_20060101-20101231.nc'
testId = '#01.001'
c.check( fn )
if c.errorCount == 0:
  print 'Passed [%s] %s: valid file name' % (module,fn)
else:
  print 'Failed [%s] %s: valid file name' % (module,fn)

testId = '#01.002'
fn = 'ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_fx.nc'
c.check(fn)
if c.errorCount == 0 and c.isFixed:
  print 'Passed [%s] %s: valid file name' % (module,fn)
else:
  print 'Failed [%s] %s: valid file name' % (module,fn)

testId = '#01.003'
fn = 'ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_3hr_2006010100-2010123100.nc'
c.check(fn)
if c.errorCount == 0:
  print 'Passed [%s] %s: valid file name' % (module,fn)
else:
  print 'Failed [%s] %s: valid file name' % (module,fn)

testId = '#01.004'
fn = 'ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_3hr_200601010030-201012310030.nc'
c.check(fn)
if c.errorCount == 0:
  print 'Passed [%s] %s: valid file name' % (module,fn)
else:
  print 'Failed [%s] %s: valid file name' % (module,fn)

testId = '#01.005'
fn = 'ps_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_x1_day_200601010030-201012310030.nc'
c.check(fn)
if c.errorCount == 0:
  print 'Failed to detect bad file name: [%s] %s ' % (module,fn)
else:
  print 'OK -- detected bad file name: [%s] %s' % (module,fn)

c = utils_c4.checkStandardDims(parent=p)
module = 'checkStandardDims'
c.check( 'tas', 'day', {},{}, False )
if c.errorCount == 0:
  print 'Failed [%s]: failed to detect empty dictionaries' % module
else:
  print 'OK -- detected error in standard dims'

c = utils_c4.checkByVar(parent=p)
module = 'checkByVar (regex)'
c.check( norun=True )
import re
r1 = re.compile( c.pats['subd'][0] )
for x in ['200401010000','2004010100']:
  m = r1.match( x )
  if m:
     print 'OK -- passed [%s] %s for sub-daily data' % (module,x)
  else:
     print 'Failed to match correct sub-daily time range element [%s] %s' % (module,x)

for x in ['200401010040','2004010200']:
  m = r1.match( x )
  if not m:
     print 'OK -- correctly failed [%s] %s for sub-daily data' % (module,x)
  else:
     print 'Failed to detect bad sub-daily time range element [%s] %s' % (module,x)

r1 = re.compile( c.pats['sem'][0] )
for x in ['199012','199101']:
  m = r1.match( x )
  if m:
     print 'OK -- passed [%s] %s for seasonal data' % (module,x)
  else:
     print 'Failed to match correct seasonal time range element [%s] %s' % (module,x)

for x in ['199011','199112']:
  m = r1.match( x )
  if not m:
     print 'OK -- correctly failed [%s] %s for seasonal data' % (module,x)
  else:
     print 'Failed to detect bad seasonal time range element [%s] %s' % (module,x)

r1 = re.compile( c.pats['mon'][0] )
for x in ['199101']:
  m = r1.match( x )
  if m:
     print 'OK -- passed [%s] %s for daily data' % (module,x)
  else:
     print 'Failed to match correct daily time range element [%s] %s -- %s' % (module,x,c.pats['day'][0])


c = utils_c4.checkGrids(parent=p)
c.interpolatedGrids = config.interpolatedGrids

lat = map( lambda x: -46.25 + x*0.5, range(185) )
lon = map( lambda x: -25.25 + x*0.5, range(173) )
da = {'lat':{'_data':lat,'units':'degrees_north','long_name':'latitude','standard_name':'latitude','_type':'float64'}, 'lon':{'_data':lon,'units':'degrees_east','long_name':'longitude','standard_name':'longitude','_type':'float64'} }
c.check( 'tas','AFR-44i', da, {'tas':{} } )
if c.errorCount == 0:
  print 'OK -- passed a correct grid'
else:
  print 'Failed -- reported errors on correct grid'
lat = map( lambda x: -46.25 + x*0.5, range(180) )
lon = map( lambda x: -25.25 + x*0.5, range(172) )
da = {'lat':{'_data':lat,'units':'degrees_north','long_name':'latitude','standard_name':'latitude','_type':'float64'}, 'lon':{'_data':lon,'units':'degrees_east','long_name':'longitude','standard_name':'longitude','_type':'float64'} }
c.check( 'tas','AFR-44i', da, {'tas':{} } )
if c.errorCount == 0:
  print 'Failed -- passed a bad grid'
else:
  print 'OK -- detected a bad grid'
