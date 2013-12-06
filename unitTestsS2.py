
import logging, time
import utils_c4
import config_c4 as config
from c4 import fileMetadata, dummy

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
  fmd = fileMetadata()
  fmd.loadNc( '/dummyPath/v1_day_a_b_1990-1991.nc', dummy=True)
except:
  print 'Failed to parse a simple dummy file path'
  raise
print 'OK: instantiated fileMetaData and parsed a simple dummy path'

p = dummy()
p.log = log
p.pcfg = config.projectConfig( "__dummy" )


module = 'checkFileName'
c = utils_c4.checkFileName(parent=p)

fn = 'v1_t1_a_b_20060101-20101231.nc'
testId = '#01.001'
c.check( fn )
if c.errorCount == 0:
  print 'Passed [%s] %s: valid file name' % (module,fn)
else:
  print 'Failed [%s] %s: valid file name' % (module,fn)
