
import sys

## callout to summary.py: if this option is selected, imports of libraries are not needed.
if __name__ == '__main__' and sys.argv[1] == '--sum':
      import summary
      summary.main()
      raise SystemExit(0)

# Standard library imports
import os, string, time, logging, sys, glob, pkgutil
import shutil
## pkgutil is used in file_utils
# Third party imports

## Local imports with 3rd party dependencies
#### netcdf --- currently only support for cmds2 -- re-arranged to facilitate support for alternative modules

import file_utils

from file_utils import fileMetadata, ncLib

# Local imports
import utils_c4 as utils
import config_c4 as config

reload( utils )

from xceptions import baseException

from fcc_utils2 import tupsort


#driving_model_ensemble_member = <CMIP5Ensemble_member>
#rcm_version_id = <RCMVersionID>                     

class dummy(object):
   pass

pathTmplDict = { 'CORDEX':'%(project)s/%(product)s/%(domain)s/%(institute)s/%(driving_model)s/%(experiment)s/%(ensemble)s/%(model)s/%(model_version)s/%(frequency)s/%(variable)s/files/%%(version)s/',   \
                 'SPECS':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(start_date)s/%(frequency)s/%(realm)s/%(table)s/%(variable)s/%(ensemble)s/files/%%(version)s/', \
                 'CMIP5':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(frequency)s/%(realm)s/%(table)s/%(ensemble)s/files/%%(version)s/%(variable)s/', \
                 '__def__':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(frequency)s/%(realm)s/%(variable)s/%(ensemble)s/files/%%(version)s/', \
               }

class recorder(object):

  def __init__(self,project,fileName,type='map',dummy=False):
    self.dummy = dummy
    self.file = fileName
    self.type = type
    self.pathTmpl = '%(project)s/%(product)s/%(domain)s/%(institute)s/%(driving_model)s/%(experiment)s/%(ensemble)s/%(model)s/%(model_version)s/%(frequency)s/%(variable)s/files/%%(version)s/'
    self.pathTmpl = pathTmplDict.get(project,pathTmplDict['__def__'])
    self.records = {}
    self.tidtupl = []

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
    assert type(drs) == type( {} ), '2nd user argument to method add should be a dictionary [%s]' % type(drs)
    tpath = self.pathTmpl % drs
    if not self.dummy:
      assert os.path.isfile( fpath ), 'File %s not found' % fpath
      fdate = time.ctime(os.path.getmtime(fpath))
      sz = os.stat(fpath).st_size
    else:
      fdate = "na"
      sz = 0
    record = '%s | OK | %s | modTime = %s | target = %s ' % (fpath,sz,fdate,tpath)
    fn = string.split( fpath, '/' )[-1]
    for k in ['creation_date','tracking_id']:
      if k in drs.keys():
        record += ' | %s = %s' % (k,drs[k])
        if k == 'tracking_id':
          self.tidtupl.append( (fn,drs[k]) )

    self.records[fn] = record
  
  def modify(self,fn,msg):
    assert fn in self.records.keys(),'Attempt to modify non-existent record %s, %s' % [fn,str(self.records.keys()[0:10])]
    if string.find( self.records[fn], '| OK |') == -1:
      ##print 'File %s already flagged with errors' % fn
      return
    s = string.replace( self.records[fn], '| OK |', '| %s |' % msg )
    ##print '--> ',s
    self.records[fn] = s

  def checktids(self):
## sort by tracking id
    self.tidtupl.sort( cmp=tupsort(k=1).cmp )
    nd = 0
    fnl = []
    for k in range(len(self.tidtupl)-1):
      if self.tidtupl[k][1] == self.tidtupl[k+1][1]:
        print 'Duplicate tracking_id: %s, %s:: %s' % (self.tidtupl[k][0],self.tidtupl[k+1][0],self.tidtupl[k][1])
        nd += 1
        if len(fnl) == 0 or fnl[-1] != self.tidtupl[k][0]:
          fnl.append( self.tidtupl[k][0])
        fnl.append( self.tidtupl[k+1][0])
    if nd == 0:
      print 'No duplicate tracking ids found in %s files' % len(self.tidtupl)
    else:
      print '%s duplicate tracking ids' % nd
      for f in fnl:
        self.modify( f, 'ERROR: duplicate tid' )

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

class checker(object):
  def __init__(self, pcfg, cls,reader,abortMessageCount=-1):
    self.info = dummy()
    self.info.pcfg = pcfg
    self.info.abortMessageCount = abortMessageCount
    self.calendar = 'None'
    self.ncReader = reader
    self.cfn = utils.checkFileName( parent=self.info,cls=cls)
    self.cga = utils.checkGlobalAttributes( parent=self.info,cls=cls)
    self.cgd = utils.checkStandardDims( parent=self.info,cls=cls)
    self.cgg = utils.checkGrids( parent=self.info,cls=cls)
    self.cls = cls

    # Define vocabs based on project
    ##self.vocabs = getVocabs(pcgf)
    self.vocabs = pcfg.vocabs

  def checkFile(self,fpath,log=None,attributeMappings=[]):
    self.calendar = 'None'
    self.info.log = log

    fn = string.split( fpath, '/' )[-1]

    if attributeMappings != []:
      self.ncReader.loadNc( fpath )
      self.ncReader.applyMap( attributeMappings, self.cfn.globalAttributesInFn, log=log )
      ncRed = True
      thisFn = self.ncReader.fn
    else:
      ncRed = False
      thisFn = fn

    self.cfn.check( thisFn )
    if not self.cfn.completed:
      self.completed = False
      return
    if not self.info.pcfg.project[:2] == '__':
      if not os.path.isfile( fpath ):
        print 'File %s not found [2]' % fpath
        self.completed = False
        return

    if not ncRed:
      ##print fpath
      self.ncReader.loadNc( fpath )
    self.ga = self.ncReader.ga
    self.va = self.ncReader.va
    self.da = self.ncReader.da

    if self.cfn.freq != None:
      vGroup = self.cfn.freq
    else:
      vGroup = self.info.pcfg.mipVocabVgmap.get(self.cfn.group,self.cfn.group)
    self.cga.check( self.ga, self.va, self.cfn.var, vGroup, self.vocabs, self.cfn.fnParts )
    if not self.cga.completed:
      self.completed = False
      return

    ##self.cgd.plevRequired = config.plevRequired
    ##self.cgd.plevValues = config.plevValues
    ##self.cgd.heightRequired = config.heightRequired
    ##self.cgd.heightValues = config.heightValues
    ##self.cgd.heightRange = config.heightRange
    self.cgd.check( self.cfn.var, self.cfn.freq, self.da, self.va, self.cga.isInstantaneous )
    self.calendar = self.cgd.calendar
    if not self.cgd.completed:
      self.completed = False
      return

    if self.info.pcfg.doCheckGrids:
      ##self.cgg.rotatedPoleGrids = config.rotatedPoleGrids
      ##self.cgg.interpolatedGrids = config.interpolatedGrids
      self.cgg.check( self.cfn.var, self.cfn.domain, self.da, self.va )
    
      if not self.cgg.completed:
        self.completed = False
        return
    self.completed = True
    self.drs = self.cga.getDrs()
    self.drs['project'] = self.info.pcfg.project
    self.errorCount = self.cfn.errorCount + self.cga.errorCount + self.cgd.errorCount + self.cgg.errorCount

class c4_init(object):

  def __init__(self,args=None):
    self.logByFile = True
    self.policyFileLogfileMode = 'w'
    self.policyBatchLogfileMode = 'np'
    if args==None:
       args = sys.argv[1:]
    nn = 0

    self.attributeMappingFile = None
    self.recordFile = 'Rec.txt'
    self.logDir = 'logs_02'
    self.errs = []
    
    # Set default project to "CORDEX"
    self.project = "CORDEX"
    self.holdExceptions = False
    forceLogOrg = None
    argsIn = args[:]

    # The --copy-config option must be the first argument if it is present.
    if args[0] == '--copy-config':
       if len(args) < 2:
         self.commandHints( argsIn )
       args.pop(0)
       dest_dir = args.pop(0)
       config.copy_config(dest_dir)
       print 'Configuration directory copied to %s.  Set CC_CONFIG_DIR to use this configuration.' % dest_dir
       print
       raise SystemExit(0)
    elif args[0] == '-h':
       print 'Help command not implemented yet'
       raise SystemExit(0)

    self.summarymode = args[0] == '--sum'
    if self.summarymode:
      return

    fltype = None
    argu = []
    while len(args) > 0:
      next = args.pop(0)
      if next == '-f':
        print '###########',args[0]
        flist = [args.pop(0),]
        self.logByFile = False
        fltype = '-f'
      elif next == '--log':
        x = args.pop(0)
        assert x in ['single','multi','s','m'], 'unrecognised logging option (--log): %s' % (x)
        if x in ['multi','m']:
           forceLogOrg = 'multi'
        elif x in ['single','s']:
           forceLogOrg = 'single'
      elif next == '--flfmode':
        lfmk = args.pop(0)
        assert lfmk in ['a','n','np','w','wo'], 'Unrecognised file logfile mode (--flfmode): %s' % lfmk
        self.policyFileLogfileMode = lfmk
      elif next == '--blfmode':
        lfmk = args.pop(0)
        assert lfmk in ['a','n','np','w','wo'], 'Unrecognised batch logfile mode (--blfmode): %s' % lfmk
        self.policyBatchLogfileMode = lfmk
      elif next == '-d':
        fdir = args.pop(0)
        flist = glob.glob( '%s/*.nc' % fdir  )
      elif next == '-D':
        flist  = []
        fdir = args.pop(0)
        for root, dirs, files in os.walk( fdir, followlinks=True ):
          for f in files:
            fpath = '%s/%s' % (root,f)
            if (os.path.isfile( fpath ) or os.path.islink( fpath )) and f[-3:] == '.nc':
              flist.append( fpath )
      elif next == '-R':
        self.recordFile = args.pop(0)
      elif next == '--ld':
        self.logDir = args.pop(0)
      elif next in ['--catchAllExceptions','--cae']:
        self.holdExceptions = True
      elif next == '--aMap':
        self.attributeMappingFile = args.pop(0)
        assert os.path.isfile( self.attributeMappingFile ), 'The token "--aMap" should be followed by the path or name of a file'
      elif next == "-p":
        self.project = args.pop(0)
      else:
       print 'Unused argument: %s' % next
       argu.append( next )
       nn+=1
    if nn != 0:
      print 'Unused arguments: ', argu
      self.commandHints( argsIn )

    if self.project == 'CMIP5' and fltype != '-f':
      fl0 = []
      for f in flist:
        if string.find( f, '/latest/' ) != -1:
          fl0.append(f)
      flist = fl0

    if forceLogOrg != None:
      if forceLogOrg == 'single':
        self.logByFile = False
      else:
        self.logByFile = True

    if self.project[:2] == '__':
       flist = []
       ss = 'abcdefgijk'
       ss = 'abcdefgijklmnopqrstuvwxyz'
       ss = 'abc'
       for i in range(10):
         v = 'v%s' % i
         for a in ss:
           for b in ss:
             flist.append( '%s_day_%s_%s_1900-1909.nc' % (v,a,b) )
    flist.sort()
    fnl = []
    for f in flist:
      fn = string.split(f, '/')[-1]
      fnl.append(fn)
    nd = 0
    dupl = []
    for k in range(len(fnl)-1):
      if fnl[k] == fnl[k-1]:
        nd += 1
        dupl.append( fnl[k] )
    self.dupDict = {}
    for f in dupl:
      self.dupDict[f] = 0
    if nd != 0:
      self.errs.append( 'Duplicate file names encountered: %s' % nd )
      self.errs.append( dupl )
    self.flist = flist
    self.fnl = fnl
    if not os.path.isdir(   self.logDir ):
       os.mkdir(   self.logDir )

    tstring1 = '%4.4i%2.2i%2.2i_%2.2i%2.2i%2.2i' % time.gmtime()[0:6]
    self.batchLogfile = '%s/qcBatchLog_%s.txt' % (  self.logDir,tstring1)
## default appending to myapp.log; mode='w' forces a new file (deleting old contents).
    self.logger = logging.getLogger('c4logger')
    if self.policyBatchLogfileMode in ['n','np']:
        assert not os.path.isfile( self.batchLogfile ), '%s exists and policy set to new file' % self.batchLogfile
    m = self.policyBatchLogfileMode[0]
    if m == 'n':
      m = 'w'
    if m == 'a':
      self.hdlr = logging.FileHandler(self.batchLogfile)
    else:
      self.hdlr = logging.FileHandler(self.batchLogfile,mode=m)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    self.hdlr.setFormatter(formatter)
    self.logger.setLevel(logging.INFO)
    self.logger.addHandler(self.hdlr)

    self.attributeMappings = []
    self.attributeMappingsLog = None
    if self.attributeMappingFile != None:
      for l in open( self.attributeMappingFile ).readlines():
        if l[0] != '#':
          bb = string.split( string.strip(l), '|' ) 
          assert len(bb) ==2, "Error in experimental module attributeMapping -- configuration line not scanned [%s]" % str(l)
          bits = string.split( bb[0], ';' )
          cl = []
          for b in bits:
            cl.append( string.split(b, '=' ) )
          self.attributeMappings.append( ('am001',cl, string.split(bb[1],'=') ) )
      self.attributeMappingsLog = open( 'attributeMappingsLog.txt', 'w' )

  def commandHints(self, args):
    if args[0] in ['-h','--sum']:
      print 'Arguments look OK'
    elif args[0] == '--copy-config':
      print 'Usage [configuration copy]: ceda_cc --copy-config <target directory path>'
    else:
      if not( '-f' in args or '-d' in args or '-D' in args):
        print 'No file or target directory specified'
        print """USAGE:
ceda_cc -p <project> [-f <NetCDF file>|-d <directory containing files>|-D <root of directory tree>] [other options]

With the "-D" option, all files in the directory tree beneath the given diretory will be checked. With the "-d" option, only files in the given directory will be checked.
"""
    raise SystemExit(0)
   

  def getFileLog( self, fn, flf=None ):
    if flf == None:
      tstring2 = '%4.4i%2.2i%2.2i' % time.gmtime()[0:3]
      if fn in self.dupDict.keys():
        tag = '__%2.2i' % self.dupDict[fn]
        self.dupDict[fn] += 1
      else:
        tag = ''
      self.fileLogfile = '%s/%s%s__qclog_%s.txt' % (self.logDir,fn[:-3],tag,tstring2)
      if self.policyFileLogfileMode in ['n','np']:
        assert not os.path.isfile( self.fileLogfile ), '%s exists and policy set to new file' % self.fileLogfile
      m = self.policyFileLogfileMode[0]
      if m == 'n':
        m = 'w'
    else:
      m = 'a'
      self.fileLogfile = flf

    self.fLogger = logging.getLogger('fileLog_%s_%s' % (fn,m))
    if m == 'a':
      self.fHdlr = logging.FileHandler(self.fileLogfile)
    else:
      self.fHdlr = logging.FileHandler(self.fileLogfile,mode=m)
    fileFormatter = logging.Formatter('%(message)s')
    self.fHdlr.setFormatter(fileFormatter)
    self.fLogger.addHandler(self.fHdlr)
    self.fLogger.setLevel(logging.INFO)
    return self.fLogger

  def closeFileLog(self):
    self.fLogger.removeHandler(self.fHdlr)
    self.fHdlr.close()
    if self.policyFileLogfileMode in ['wo','np']:
      os.popen( 'chmod %s %s;' % (444, self.fileLogfile) )

  def closeBatchLog(self):
    self.logger.removeHandler(self.hdlr)
    self.hdlr.close()
    if self.policyBatchLogfileMode in ['wo','np']:
      os.popen( 'chmod %s %s;' % (444, self.batchLogfile) )


class main(object):

  def __init__(self,args=None,abortMessageCount=-1,printInfo=False,monitorFileHandles = False):
    logDict = {}
    ecount = 0
    c4i = c4_init(args=args)
      
    isDummy  = c4i.project[:2] == '__'
    if (ncLib == None) and (not isDummy):
       raise baseException( 'Cannot proceed with non-dummy [%s] project without a netcdf API' % (c4i.project) )
    pcfg = config.projectConfig( c4i.project )
    ncReader = fileMetadata(dummy=isDummy, attributeMappingsLog=c4i.attributeMappingsLog)
    self.cc = checker(pcfg, c4i.project, ncReader,abortMessageCount=abortMessageCount)
    rec = recorder( c4i.project, c4i.recordFile, dummy=isDummy )
    if monitorFileHandles:
      self.monitor = utils.sysMonitor()
    else:
      self.monitor = None

    cal = None
    c4i.logger.info( 'Starting batch -- number of file: %s' % (len(c4i.flist)) )
    if len( c4i.errs ) > 0:
      for i in range(0,len( c4i.errs ), 2 ):
        c4i.logger.info( c4i.errs[i] )
  
    self.cc.info.amapListDraft = []
    cbv = utils.checkByVar( parent=self.cc.info,cls=c4i.project,monitor=self.monitor)
    cbv.impt( c4i.flist )
    if printInfo:
      print cbv.info

    fileLogOpen = False
    self.resList =  []
    stdoutsum = 2000
    npass = 0
    kf = 0
    for f in c4i.flist:
      kf += 1
      rv = False
      ec = None
      if monitorFileHandles:
        nofhStart = self.monitor.get_open_fds()
      fn = string.split(f,'/')[-1]
      c4i.logger.info( 'Starting: %s' % fn )
      try:
  ### need to have a unique name, otherwise get mixing of logs despite close statement below.
  ### if duplicate file names are present, this will be recorded in the main log, tag appended to file level log name (not yet tested).
        if c4i.logByFile:
          fLogger = c4i.getFileLog( fn )
          logDict[fn] = c4i.fileLogfile
          c4i.logger.info( 'Log file: %s' % c4i.fileLogfile )
          fileLogOpen = True
        else:
          fLogger = c4i.logger
  
        fLogger.info( 'Starting file %s' % fn )
## default appending to myapp.log; mode='w' forces a new file (deleting old contents).
        self.cc.checkFile( f, log=fLogger,attributeMappings=c4i.attributeMappings )

        if self.cc.completed:
          if cal not in (None, 'None') and self.cc.cgd.varGroup != "fx":
            if cal != self.cc.calendar:
              cal_change_err_msg = 'Error: change in calendar attribute %s --> %s' % (cal, self.cc.calendar)
              c4i.logger.info(cal_change_err_msg)
              fLogger.info(cal_change_err_msg)
              self.cc.errorCount += 1

          cal = self.cc.calendar
          ec = self.cc.errorCount
        rv =  ec == 0
        if rv:
          npass += 1
        self.resList.append( (rv,ec) )

        if c4i.logByFile:
          if self.cc.completed:
            fLogger.info( 'Done -- error count %s' % self.cc.errorCount )
          else:
            fLogger.info( 'Done -- checks not completed' )
          c4i.closeFileLog( )
          fileLogOpen = False

        if self.cc.completed:
          c4i.logger.info( 'Done -- error count %s' % self.cc.errorCount ) 
          ecount += self.cc.errorCount
          if self.cc.errorCount == 0:
            rec.add( f, self.cc.drs )
          else:
            rec.addErr( f, 'ERRORS FOUND | errorCount = %s' % self.cc.errorCount )
        else:
          ecount += 20
          c4i.logger.info( 'Done -- testing aborted because of severity of errors' )
          rec.addErr( f, 'ERRORS FOUND AND CHECKS ABORTED' )
      except:
        c4i.logger.error("Exception has occured" ,exc_info=1)
        if fileLogOpen:
          fLogger.error("C4.100.001: [exception]: FAILED:: Exception has occured" ,exc_info=1)
          c4i.closeFileLog( )
          fileLogOpen = False
        rec.addErr( f, 'ERROR: Exception' )
        if not c4i.holdExceptions:
          raise
      if stdoutsum > 0 and kf%stdoutsum == 0:
         print '%s files checked; %s passed this round' % (kf,npass)
      if monitorFileHandles:
        nofhEnd = self.monitor.get_open_fds()
        if nofhEnd > nofhStart:
           print 'Open file handles: %s --- %s' % (nofhStart, nofhEnd)
  
    self.cc.info.log = c4i.logger
    
    if c4i.project not in ['SPECS','CCMI','CMIP5']:
       cbv.c4i = c4i
       cbv.setLogDict( logDict )
       cbv.check( recorder=rec, calendar=self.cc.calendar)
       try:
         ecount += cbv.errorCount
       except:
         ecount = None
    ncReader.close()
    if type( self.cc.info.amapListDraft ) == type( [] ) and len(  self.cc.info.amapListDraft ) > 0:
      ll =  self.cc.info.amapListDraft
      ll.sort()
      oo = open( 'amapDraft.txt', 'w' )
      oo.write( ll[0] + '\n' )
      for i in range( 1,len(ll) ):
        if ll[i] != ll[i-1]:
          oo.write( ll[i] + '\n' )
      oo.close()
    if c4i.project in ['SPECS','CCMI','CMIP5']:
      rec.checktids()
    rec.dumpAll()
    if printInfo:
      print 'Error count %s' % ecount
    ##c4i.hdlr.close()
    c4i.closeBatchLog()
    self.ok = all( map( lambda x: x[0], self.resList ) )


   


def main_entry():
   """
   Wrapper around main() for use with setuptools.

   """
   main(printInfo=True)

if __name__ == '__main__':
  if sys.argv[1] == '--sum':
      import summary
      summary.main()
      raise SystemExit(0)
  main_entry()


##else:
  ##f1 = '/data/u10/cordex/AFR-44/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/day/clh/clh_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_day_19810101-19851231.nc'
  ##f2 = '/data/u10/cordex/AFR-44/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/sem/tas/tas_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_sem_200012-201011.nc'
  ##f3 = '/data/u10/cordex/AFR-44i/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/mon/tas/tas_AFR-44i_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_mon_199101-200012.nc'
  ##cc.checkFile( f3 )
