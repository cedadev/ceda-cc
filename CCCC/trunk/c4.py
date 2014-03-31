
# Standard library imports
import os, string, time, logging, sys, glob

# Third party imports

try:
  import cdms2
  withCdms = True
except:
  print 'Failed to import cdms2: will not be able to read NetCDF'
  withCdms = False

# Local imports
import utils_c4 as utils
import config_c4 as config

reload( utils )


#driving_model_ensemble_member = <CMIP5Ensemble_member>
#rcm_version_id = <RCMVersionID>                     

class fileMetadata:

  def __init__(self,dummy=False,attributeMappingsLog=None):
     
     self.dummy = dummy
     self.atMapLog = attributeMappingsLog
     if self.atMapLog == None:
       self.atMapLog = open( '/tmp/cccc_atMapLog.txt', 'a' )

  def close(self):
    self.atMapLog.close()

  def loadNc(self,fpath):
    self.fpath = fpath
    self.fn = string.split( fpath, '/' )[-1]
    self.fparts = string.split( self.fn[:-3], '_' )
    self.ga = {}
    self.va = {}
    self.da = {}
    if self.dummy:
      self.makeDummyFileImage()
      return
    self.nc = cdms2.open( fpath )
    for k in self.nc.attributes.keys():
      self.ga[k] = self.nc.attributes[k]
      if len( self.ga[k] ) == 1:
        self.ga[k] = self.ga[k][0]
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

  def makeDummyFileImage(self):
    for k in range(10):
      self.ga['ga%s' % k] =  str(k)
    for v in [self.fparts[0],]:
      self.va[v] = {}
      self.va[v]['standard_name'] = 's%s' % v
      self.va[v]['long_name'] = v
      self.va[v]['cell_methods'] = 'time: point'
      self.va[v]['units'] = '1'
      self.va[v]['_type'] = 'float32'

    for v in ['lat','lon','time']:
      self.da[v] = {}
      self.da[v]['_type'] = 'float64'
      self.da[v]['_data'] = range(5)
    dlist = ['lat','lon','time']
    svals = lambda p,q: map( lambda y,z: self.da[y].__setitem__(p, z), dlist, q )
    svals( 'standard_name', ['latitude', 'longitude','time'] )
    svals( 'long_name', ['latitude', 'longitude','time'] )
    svals( 'units', ['degrees_north', 'degrees_east','days since 19590101'] )

  def applyMap( self, mapList, globalAttributesInFn, log=None ):
    for m in mapList:
      if m[0] == 'am001':
        if m[1][0][0] == "@var":
          if m[1][0][1] in self.va.keys():
            this = self.va[m[1][0][1]]
            apThis = True
            for c in m[1][1:]:
              if c[0] not in this.keys():
                apThis = False
              elif c[1] != this[c[0]]:
                apThis = False
            if m[2][0] != '':
              targ = m[2][0]
            else:
              targ = m[1][-1][0]
            if apThis:
              if log != None:
                log.info( 'Setting %s to %s' % (targ,m[2][1]) )
              ##print 'Setting %s:%s to %s' % (m[1][0][1],targ,m[2][1])
              thisval = self.va[m[1][0][1]].get( targ, None )
              self.va[m[1][0][1]][targ] = m[2][1]
              self.atMapLog.write( '@var:"%s","%s","%s","%s","%s"\n' % (self.fpath, m[1][0][1], targ, thisval, m[2][1] ) )

        elif m[1][0][0] == "@ax":
          ##print 'checking dimension ',m[1][0][1], self.da.keys()
          if m[1][0][1] in self.da.keys():
            ##print 'checking dimension [2]',m[1][0][1]
            this = self.da[m[1][0][1]]
            apThis = True
            for c in m[1][1:]:
              if c[0] not in this.keys():
                apThis = False
              elif c[1] != this[c[0]]:
                apThis = False
            if m[2][0] != '':
              targ = m[2][0]
            else:
              targ = m[1][-1][0]
            if apThis:
              if log != None:
                log.info( 'Setting %s to %s' % (targ,m[2][1]) )
              ##print 'Setting %s:%s to %s' % (m[1][0][1],targ,m[2][1])
              thisval = self.va[m[1][0][1]].get( targ, None )
              self.da[m[1][0][1]][targ] = m[2][1]
              self.atMapLog.write( '@ax:"%s","%s","%s","%s","%s"\n' % (self.fpath, m[1][0][1], targ, thisval, m[2][1]) )
        elif m[1][0][0][0] != "@":
            this = self.ga
            apThis = True
            for c in m[1]:
              if c[0] not in this.keys():
                apThis = False
              elif c[1] != this[c[0]]:
                apThis = False
            if m[2][0] != '':
              targ = m[2][0]
            else:
              targ = m[1][-1][0]
            if apThis:
              if log != None:
                log.info( 'Setting %s to %s' % (targ,m[2][1]) )
              print 'Setting %s:%s to %s' % (m[1][0][1],targ,m[2][1])
              thisval = self.ga.get( targ, None )
              self.ga[targ] = m[2][1]
              self.atMapLog.write( '@:"%s","%s","%s","%s","%s"\n' % (self.fpath, 'ga', targ, thisval, m[2][1]) )
##
              if targ in globalAttributesInFn:
                i = globalAttributesInFn.index(targ)
                thisval = self.fparts[ i ]
                self.fparts[ i ] = m[2][1]
                self.fn = string.join( self.fparts, '_' ) + '.nc'
                self.atMapLog.write( '@fn:"%s","%s","%s"\n' % (self.fpath, thisval, m[2][1]) )
        else:
          print 'Token %s not recognised' % m[1][0][0]


class dummy:
   pass


pathTmplDict = { 'CORDEX':'%(project)s/%(product)s/%(domain)s/%(institute)s/%(driving_model)s/%(experiment)s/%(ensemble)s/%(model)s/%(model_version)s/%(frequency)s/%(variable)s/files/%%(version)s/',   \
                 'SPECS':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s_%(series)s/%(start_date)s/%(frequency)s/%(realm)s/%(variable)s/%(ensemble)s/files/%%(version)s/', \
                 '__def__':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(frequency)s/%(realm)s/%(variable)s/%(ensemble)s/files/%%(version)s/', \
               }

class recorder:

  def __init__(self,project,fileName,type='map',dummy=False):
    self.dummy = dummy
    self.file = fileName
    self.type = type
    self.pathTmpl = '%(project)s/%(product)s/%(domain)s/%(institute)s/%(driving_model)s/%(experiment)s/%(ensemble)s/%(model)s/%(model_version)s/%(frequency)s/%(variable)s/files/%%(version)s/'
    self.pathTmpl = pathTmplDict.get(project,pathTmplDict['__def__'])
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
    for k in ['creation_date','tracking_id']:
      if k in drs.keys():
        record += ' | %s = %s' % (k,drs[k])

    fn = string.split( fpath, '/' )[-1]
    self.records[fn] = record
  
  def modify(self,fn,msg):
    assert fn in self.records.keys(),'Attempt to modify non-existent record %s, %s' % [fn,str(self.records.keys()[0:10])]
    if string.find( self.records[fn], '| OK |') == -1:
      ##print 'File %s already flagged with errors' % fn
      return
    s = string.replace( self.records[fn], '| OK |', '| %s |' % msg )
    ##print '--> ',s
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

class c4_init:

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
    
    # Set default project to "CORDEX"
    self.project = "CORDEX"
    self.holdExceptions = False
    forceLogOrg = None

    while len(args) > 0:
      next = args.pop(0)
      if next == '-f':
        flist = [args.pop(0),]
        self.logByFile = False
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
        for root, dirs, files in os.walk( fdir ):
          for f in files:
            fpath = '%s/%s' % (root,f)
            if os.path.isfile( fpath ) and f[-3:] == '.nc':
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
       nn+=1
    assert nn==0, 'Aborting because of unused arguments'

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

  def getFileLog( self, fn, flf=None ):
    if flf == None:
      tstring2 = '%4.4i%2.2i%2.2i' % time.gmtime()[0:3]
      self.fileLogfile = '%s/%s__qclog_%s.txt' % (self.logDir,fn[:-3],tstring2)
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


class main:

  def __init__(self,args=None,abortMessageCount=-1,printInfo=False,monitorFileHandles = False):
    logDict = {}
    ecount = 0
    c4i = c4_init(args=args)
    isDummy  = c4i.project[:2] == '__'
    if (not withCdms) and isDummy:
       print withCdms, c4i.project
       print 'Cannot proceed with non-dummy project without cdms'
       raise
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
  
    self.cc.info.amapListDraft = []
    cbv = utils.checkByVar( parent=self.cc.info,cls=c4i.project,monitor=self.monitor)
    cbv.impt( c4i.flist )
    if printInfo:
      print cbv.info

    fileLogOpen = False
    self.resList =  []
    for f in c4i.flist:
      rv = False
      ec = None
      if monitorFileHandles:
        nofhStart = self.monitor.get_open_fds()
      fn = string.split(f,'/')[-1]
      c4i.logger.info( 'Starting: %s' % fn )
      try:
  ### need to have a unique name, otherwise get mixing of logs despite close statement below.
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
          fLogger.error("xxxxxx: FAILED:: Exception has occured" ,exc_info=1)
          c4i.closeFileLog( )
          fileLogOpen = False
        rec.addErr( f, 'ERROR: Exception' )
        if not c4i.holdExceptions:
          raise
      if monitorFileHandles:
        nofhEnd = self.monitor.get_open_fds()
        if nofhEnd > nofhStart:
           print 'Open file handles: %s --- %s' % (nofhStart, nofhEnd)
  
    self.cc.info.log = c4i.logger
    
    if c4i.project not in ['SPECS','CCMI']:
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
    rec.dumpAll()
    if printInfo:
      print 'Error count %s' % ecount
    ##c4i.hdlr.close()
    c4i.closeBatchLog()
    self.ok = all( map( lambda x: x[0], self.resList ) )
if __name__ == '__main__':
  main(printInfo=True)


##else:
  ##f1 = '/data/u10/cordex/AFR-44/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/day/clh/clh_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_day_19810101-19851231.nc'
  ##f2 = '/data/u10/cordex/AFR-44/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/sem/tas/tas_AFR-44_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_sem_200012-201011.nc'
  ##f3 = '/data/u10/cordex/AFR-44i/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/mon/tas/tas_AFR-44i_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_mon_199101-200012.nc'
  ##cc.checkFile( f3 )
