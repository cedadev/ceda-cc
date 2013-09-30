
import utils_c4 as utils
import config_c4 as config
import os, string, time
import logging

reload( utils )
import cdms2

vocabs = { 'variable':utils.mipVocab(), \
           'driving_experiment_name':utils.listControl( 'driving_experiment_name', config.validExperiment ), \
           'project_id':utils.listControl( 'project_id', ['CORDEX'] ), \
           'CORDEX_domain':utils.listControl( 'CORDEX_domain',  config.validCordexDomains ), \
           'driving_model_id':utils.listControl( 'driving_model_id',  config.validGcmNames ), \
           'driving_model_ensemble_member':utils.patternControl( 'driving_model_ensemble_member',  'r[0-9]+i[0-9]+p[0-9]+' ), \
           'rcm_version_id':utils.patternControl( 'rcm_version_id',  '[a-zA-Z0-9-]+' ), \
           'model_id':utils.listControl( 'model_id',  config.validRcmNames ), \
           'institute_id':utils.listControl( 'institute_id',  config.validInstNames ), \
           'frequency':utils.listControl( 'frequency', config.validCordexFrequecies ) }

#driving_model_ensemble_member = <CMIP5Ensemble_member>
#rcm_version_id = <RCMVersionID>                     

class dummy:
   pass

class recorder:

  def __init__(self,fileName,type='map'):
    self.file = fileName
    self.type = type
    self.pathTmpl = '%(project)s/%(product)s/%(domain)s/%(institute)s/%(driving_model)s/%(experiment)s/%(ensemble)s/%(model)s/%(model_version)s/%(frequency)s/%(variable)s/files/%%(version)s/'
    self.records = {}

  def open(self):
    if self.type == 'map':
      self.fh = open( self.file, 'a' )
    else:
      self.sh = shelve.open( self.file )

  def close(self):
    if self.type == 'map':
      self.fh.close()
    else:
      self.sh.close()

  def add(self,fpath,drs,safe=True):
    assert self.type == 'map','Can only do map files at present'
    assert os.path.isfile( fpath ), 'File %s not found' % fpath
    assert type(drs) == type( {} ), '2nd user argument to method add should be a dictionary [%s]' % type(drs)
    tpath = self.pathTmpl % drs
    fdate = time.ctime(os.path.getmtime(fpath))
    sz = os.stat(fpath).st_size
    record = '%s | OK | %s | modTime = %s | target = %s ' % (fpath,sz,fdate,tpath)
    for k in ['creation_date','tracking_id']:
      if k in drs.keys():
        record += ' | %s = %s' % (k,drs[k])

    fn = string.split( fpath, '/' )[-1]
    self.records[fn] = record
  
  def modify(self,fn,msg):
    assert fn in self.records.keys(),'Attempt to modify non-existent record %s, %s' % [fn,str(self.records.keys()[0:10])]
    if string.find( self.records[fn], '| OK |') == -1:
      print 'File %s already flagged with errors' % fn
      return
    s = string.replace( self.records[fn], '| OK |', '| %s |' % msg )
    print '--> ',s
    self.records[fn] = s

  def dumpAll(self,safe=True):
    keys = self.records.keys()
    keys.sort()
    for k in keys:
      self.dump( self.records[k], safe=safe )

  def dump( self, record, safe=True ):
    if safe:
      self.open()
    self.fh.write( record + '\n' )
    if safe:
      self.close()

  def addErr(self,fpath,reason,safe=True):
    record = '%s | %s' % (fpath, reason)
    fn = string.split( fpath, '/' )[-1]
    self.records[fn] = record

class checker:
  def __init__(self):
    self.info = dummy()
    self.calendar = 'None'
    self.cfn = utils.checkFileName(parent=self.info)
    self.cga = utils.checkGlobalAttributes(parent=self.info)
    self.cgd = utils.checkStandardDims(parent=self.info)
    self.cgg = utils.checkGrids(parent=self.info)

  def checkFile(self,fpath,log=None):
    self.calendar = 'None'
    self.info.log = log

    fn = string.split( fpath, '/' )[-1]
    self.cfn.check( fn )
    if not self.cfn.completed:
      self.completed = False
      return
    if not os.path.isfile( fpath ):
      print 'File %s not found' % fpath
      self.completed = False
      return

    self.nc = cdms2.open( fpath )
    self.ga = {}
    self.va = {}
    self.da = {}
    for k in self.nc.attributes.keys():
      self.ga[k] = self.nc.attributes[k]
    for v in self.nc.variables.keys():
      self.va[v] = {}
      for k in self.nc.variables[v].attributes.keys():
        self.va[v][k] = self.nc.variables[v].attributes[k]
      self.va[v]['_type'] = str( self.nc.variables[v].dtype )
      if v in ['plev','plev_bnds','height']:
        self.va[v]['_data'] = self.nc.variables[v].getValue().tolist()

    for v in self.nc.axes.keys():
      self.da[v] = {}
      for k in self.nc.axes[v].attributes.keys():
        self.da[v][k] = self.nc.axes[v].attributes[k]
      self.da[v]['_type'] = str( self.nc.axes[v].getValue().dtype )
      self.da[v]['_data'] = self.nc.axes[v].getValue().tolist()
      
    self.nc.close()

    self.cga.check( self.ga, self.va, self.cfn.var, self.cfn.freq, vocabs, self.cfn.fnParts )
    if not self.cga.completed:
      self.completed = False
      return

    self.cgd.plevRequired = config.plevRequired
    self.cgd.plevValues = config.plevValues
    self.cgd.heightRequired = config.heightRequired
    self.cgd.heightValues = config.heightValues
    self.cgd.check( self.cfn.var, self.cfn.freq, self.da, self.va, self.cga.isInstantaneous )
    self.calendar = self.cgd.calendar
    if not self.cgd.completed:
      self.completed = False
      return

    self.cgg.rotatedPoleGrids = config.rotatedPoleGrids
    self.cgg.interpolatedGrids = config.interpolatedGrids
    self.cgg.check( self.cfn.var, self.cfn.domain, self.da, self.va )
    
    if not self.cgg.completed:
      self.completed = False
      return
    self.completed = True
    self.drs = self.cga.getDrs()
    self.errorCount = self.cfn.errorCount + self.cga.errorCount + self.cgd.errorCount + self.cgg.errorCount

class c4_init:

  def __init__(self):
    self.logByFile = True
    args = sys.argv[1:]
    nn = 0

    self.recordFile = 'Rec.txt'
    self.logDir = 'logs_02'
    while len(args) > 0:
      next = args.pop(0)
      if next == '-f':
        flist = [args.pop(0),]
        self.logByFile = False
      elif next == '-d':
        import glob
        fdir = args.pop(0)
        flist = glob.glob( '%s/*.nc' % fdir  )
      elif next == '-D':
        flist  = []
        fdir = args.pop(0)
        for root, dirs, files in os.walk( fdir ):
          for f in files:
            fpath = '%s/%s' % (root,f)
            if os.path.isfile( fpath ) and f[-3:] == '.nc':
              flist.append( fpath )
      elif next == '-R':
        self.recordFile = args.pop(0)
      elif next == '--ld':
        self.logDir = args.pop(0)
      else:
       print 'Unused argument: %s' % next
       nn+=1
    assert nn==0, 'Aborting because of unused arguments'

    flist.sort()
    fnl = []
    nd = 0
    for f in flist:
      fn = string.split(f, '/')[-1]
      if fn in fnl:
        print 'ERROR: file name duplicated %s' % fn
        nd += 0
      else:
        fnl.append(fn)
    assert nd == 0, 'Duplicate file names encountered'
    self.flist = flist
    self.fnl = fnl
    if not os.path.isdir(   self.logDir ):
       os.mkdir(   self.logDir )

    tstring1 = '%4.4i%2.2i%2.2i_%2.2i%2.2i%2.2i' % time.gmtime()[0:6]
    batchLogFile = '%s/qcBatchLog_%s.txt' % (  self.logDir,tstring1)
## default appending to myapp.log; mode='w' forces a new file (deleting old contents).
    self.logger = logging.getLogger('c4logger')
    self.hdlr = logging.FileHandler(batchLogFile,mode='w')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    self.hdlr.setFormatter(formatter)
    self.logger.setLevel(logging.INFO)
    self.logger.addHandler(self.hdlr)


  def getFileLog( self, fn ):
    tstring2 = '%4.4i%2.2i%2.2i' % time.gmtime()[0:3]
    self.fileLogFile = '%s/%s__qclog_%s.txt' % (self.logDir,fn[:-3],tstring2)
    fLogger = logging.getLogger('fileLog_%s' % fn)
    self.fHdlr = logging.FileHandler(self.fileLogFile,mode='w')
    fileFormatter = logging.Formatter('%(message)s')
    self.fHdlr.setFormatter(fileFormatter)
    fLogger.addHandler(self.fHdlr)
    fLogger.setLevel(logging.INFO)
    return fLogger

  def closeFileLog(self):
    self.fHdlr.close()

cc = checker()

cal = None

if __name__ == '__main__':
  import sys
  c4i = c4_init()
  rec = recorder( c4i.recordFile )

  c4i.logger.info( 'Starting batch -- number of file: %s' % (len(c4i.flist)) )

  cbv = utils.checkByVar( parent=cc.info)
  cbv.impt( c4i.flist )

  for f in c4i.flist:
    fn = string.split(f,'/')[-1]
    c4i.logger.info( 'Starting: %s' % fn )
    try:
### need to have a unique name, otherwise get mixing of logs despite close statement below.
      if c4i.logByFile:
        fLogger = c4i.getFileLog( fn )
        c4i.logger.info( 'Log file: %s' % c4i.fileLogFile )
      else:
        fLogger = c4i.logger

      fLogger.info( 'Starting file %s' % fn )
## default appending to myapp.log; mode='w' forces a new file (deleting old contents).
      cc.checkFile( f, log=fLogger )
      if c4i.logByFile:
        c4i.closeFileLog( )

      if cc.completed:
        if cal != None:
          if cal != cc.calendar:
            c4i.logger.info( 'Error: change in calendar attribute %s --> %s' % (cal, cc.calendar) )
            cc.errorCount += 1
        cal = cc.calendar
        c4i.logger.info( 'Done -- error count %s' % cc.errorCount ) 
        if cc.errorCount == 0:
          rec.add( f, cc.drs )
        else:
          rec.addErr( f, 'ERRORS FOUND | errorCount = %s' % cc.errorCount )
      else:
        c4i.logger.info( 'Done -- testing aborted because of severity of errors' )
        rec.addErr( f, 'ERRORS FOUND AND CHECKS ABORTED' )
    except:
      c4i.logger.info( 'Exception caught' )
      rec.addErr( f, 'ERROR: Exception' )
      raise

  cc.info.log = c4i.logger
  cbv.check( recorder=rec, calendar=cc.calendar)
  rec.dumpAll()
  c4i.hdlr.close()
else:
  f1 = '/data/u10/cordex/AFR-44/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/day/clh/clh_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_day_19810101-19851231.nc'
  f2 = '/data/u10/cordex/AFR-44/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/sem/tas/tas_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_sem_200012-201011.nc'
  f3 = '/data/u10/cordex/AFR-44i/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/mon/tas/tas_AFR-44i_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_mon_199101-200012.nc'
  cc.checkFile( f3 )
