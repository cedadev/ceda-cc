
import logging, time
import utils_c4
import config_c4 as config
from c4 import fileMetadata, dummy, main
from xceptions import *

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
  print 'Failed to parse a simple dummy file path'
  raise baseException( 'Failed to parse a simple dummy file path' )
print 'OK: instantiated fileMetaData and parsed a simple dummy path'

p = dummy()
p.log = log
p.abortMessageCount = -1
p.pcfg = config.projectConfig( "__dummy" )


module = 'checkFileName'
c = utils_c4.checkFileName(parent=p)

fn = 'v1_t1_a_b_20060101-20101231.nc'
testId = '#10.001'
c.check( fn )
if c.errorCount == 0:
  print 'OK [%s] %s: valid file name with project=__dummy' % (module,fn)
else:
  print 'Failed [%s] %s: valid file name' % (module,fn)


testId = '#11.001'
try:
  m = main( args=['-p', '__dummy'], monitorFileHandles=True )
  print 'OK [%s]: dummy run completed without exception' % testId
except:
  print 'Failed [%s]: dummy run triggered exception' % testId
  raise baseException( 'Failed [%s]: dummy run triggered exception' % testId )

testId = '#11.002'
if m.monitor.fhCountMax < 10:
  print 'OK [%s]: fhCountMax = %s' % ( testId, m.monitor.fhCountMax )
else:
  print 'Failed [%s]: fhCountMax = %s' % ( testId, m.monitor.fhCountMax )

testId = '#11.003'
try:
  m = main( args=['-p', '__dummy'], abortMessageCount=10 )
  print 'Failed [%s]: did not trigger exception' % testId
except:
  print 'OK [%s]: attempt to trigger exception successful' % testId
