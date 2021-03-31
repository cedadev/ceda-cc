import logging, time, os, sys
import ceda_cc.utils_c4 as utils_c4
from ceda_cc.ceda_cc_config import config_c4 as config
from ceda_cc.c4_run import fileMetadata, dummy, Main
from ceda_cc.xceptions import *

from ceda_cc.file_utils import installedSupportedNetcdf

#### set up log file ####
tstring2 = '%4.4i%2.2i%2.2i' % time.gmtime()[0:3]
testLogFile = '%s__qclog_%s.txt' % ('unitTestsS2',tstring2)
log = logging.getLogger(testLogFile)
fHdlr = logging.FileHandler(testLogFile,mode='w')
fileFormatter = logging.Formatter('%(message)s')
fHdlr.setFormatter(fileFormatter)
log.addHandler(fHdlr)
log.setLevel(logging.INFO)

try:
  fmd = fileMetadata(dummy=True)
  fmd.loadNc( '/dummyPath/v1_day_a_b_1990-1991.nc')
except:
  print('Failed to parse a simple dummy file path')
  raise baseException( 'Failed to parse a simple dummy file path' )
print('OK: instantiated fileMetaData and parsed a simple dummy path')

p = dummy()
p.log = log
p.abortMessageCount = -1
p.pcfg = config.ProjectConfig( "__dummy" )


module = 'checkFileName'
c = utils_c4.checkFileName(parent=p)

fn = 'v1_t1_a_b_20060101-20101231.nc'
testId = '#10.001'
c.check( fn )
if c.errorCount == 0:
  print('OK: [%s] %s: valid file name with project=__dummy' % (module,fn))
else:
  print('Failed [%s] %s: valid file name' % (module,fn))

if sys.version_info >= (2,7):
  ## monitoting file handles uses a "subprocess" method which is not available in python 2.6
  testId = '#11.001'
  try:
    m = Main( args=['-p', '__dummy'], monitorFileHandles=True )
    m.run()
    print('OK: [%s]: dummy run completed without exception' % testId)
  except:
    print('Failed [%s]: dummy run triggered exception' % testId)
    raise
    raise baseException( 'Failed [%s]: dummy run triggered exception' % testId )

  testId = '#11.002'
  if m.monitor.fhCountMax < 15:
    print('OK: [%s]: fhCountMax = %s' % ( testId, m.monitor.fhCountMax ))
  else:
    print('Failed [%s]: fhCountMax = %s' % ( testId, m.monitor.fhCountMax ))

testId = '#11.003'
try:
  m = Main( args=['-p', '__dummy'], abortMessageCount=10 )
  m.run()
  print('Failed [%s]: did not trigger exception' % testId)
except:
  print('OK: [%s]: attempt to trigger exception successful' % testId)


extras = [
( '/data/work/cmip5/output1/pr_20110323/pr_3hr_HadGEM2-ES_historical_r2i1p1_200501010130-200512302230.nc', 'CMIP5', 0 ),
('/data/work/cmip5/output1/pr_20110323/pr_3hr_HadGEM2-ES_historical_r2i1p1_200001010130-200412302230.nc', 'CMIP5', 0 ) ]


kt = 0
for e in extras:
  kt += 1
  if os.path.isfile( e[0] ):
    if 'cdms2' in installedSupportedNetcdf:
      testId = '#20.%3.3i' % kt
      m = Main( args=['-p', e[1], '-f', e[0], '--force-cdms2','--ld', 'ld_test1' ], abortMessageCount=10 )
      m.run()
      if m.ok:
         print('OK: [%s]: successfully checked test file with cdms2' % testId)
      else:
         print('Failed [%s]: incorrect test results' % testId)

    testId = '#21.%3.3i' % kt
    m = Main( args=['-p', e[1], '-f', e[0], '--force-ncq','--ld', 'ld_test2' ], abortMessageCount=10 )
    m.run()
    if m.ok:
       print('OK: [%s]: successfully checked test file with ncq3' % testId)
    else:
       print('Failed [%s]: incorrect test results' % testId)

    if 'netCDF4' in installedSupportedNetcdf:
      testId = '#22.%3.3i' % kt
      m = Main( args=['-p', e[1], '-f', e[0], '--force-pync4','--ld', 'ld_test3' ], abortMessageCount=10 )
      m.run()
      if m.ok:
         print('OK: [%s]: successfully checked test file with python NetCDF4' % testId)
      else:
         print('Failed [%s]: incorrect test results' % testId)

    if 'Scientific' in installedSupportedNetcdf:
      testId = '#23.%3.3i' % kt
      m = Main( args=['-p', e[1], '-f', e[0], '--force-scientific','--ld', 'ld_test4' ], abortMessageCount=10 )
      m.run()
      if m.ok:
         print('OK: [%s]: successfully checked test file with python Scientific' % testId)
      else:
         print('Failed [%s]: incorrect test results' % testId)
      
    
