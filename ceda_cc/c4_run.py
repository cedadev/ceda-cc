"""ceda_cc
##########
Entry point for API.

USAGE
#####
c4_run.main( <argument list> )
"""
import sys
from ccinit import c4_init

testmain=False
## callout to summary.py: if this option is selected, imports of libraries are not needed.
if not testmain:
  if __name__ == '__main__':
   if len(sys.argv) > 1:
     if sys.argv[1] == '--sum':
        import summary
        summary.summariseLogs()
        raise SystemExit(0)
     elif sys.argv[1] == '-v':
        from versionConfig import version, versionComment
        print 'ceda-cc version %s [%s]' % (version,versionComment)
        raise SystemExit(0)
     elif sys.argv[1] == '--unitTest':
        print "Starting test suite 1"
        import unitTestsS1
        print "Starting test suite 2"
        import unitTestsS2
        print "Tests completed"
        raise SystemExit(0)
   else:
     print __doc__
     raise SystemExit(0)

# Standard library imports
import os, string, time, glob, pkgutil
import shutil
## pkgutil is used in file_utils
# Third party imports

## Local imports with 3rd party dependencies
#### netcdf --- currently only support for cmds2 -- re-arranged to facilitate support for alternative modules

import file_utils

from file_utils import fileMetadata, ncLib

# Local imports
import utils_c4 as utils
import ceda_cc_config.config_c4 as config

reload( utils )

from xceptions import baseException

from fcc_utils2 import tupsort


#driving_model_ensemble_member = <CMIP5Ensemble_member>
#rcm_version_id = <RCMVersionID>                     

class dummy(object):
  def __init__(self):
     self.experimental = None
     self.parent = None

pathTmplDict = { 'CORDEX':'%(project)s/%(product)s/%(domain)s/%(institute)s/%(driving_model)s/%(experiment)s/%(ensemble)s/%(model)s/%(model_version)s/%(frequency)s/%(variable)s/files/%%(version)s/',   \
                 'SPECS':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(start_date)s/%(frequency)s/%(realm)s/%(table)s/%(variable)s/%(ensemble)s/files/%%(version)s/', \
                 'CMIP5':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(frequency)s/%(realm)s/%(table)s/%(ensemble)s/files/%%(version)s/%(variable)s/', \
                 'CCMI':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(frequency)s/%(realm)s/%(table)s/%(ensemble)s/files/%%(version)s/%(variable)s/', \
                 'ESA-CCI':'%(level)s/%(platform)s/%(sensor)s/%(variable)s/', \
                 '__def__':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(frequency)s/%(realm)s/%(variable)s/%(ensemble)s/files/%%(version)s/', \
               }

## Core DRS: list of vocab names
## Path template: -- current version puts upper case in "project"
## Dataset template:  

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
    if len( self.tidtupl ) == 1:
      return
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
  def __init__(self, pcfg, cls,reader,abortMessageCount=-1,experimental=False):
    self.info = dummy()
    self.info.pcfg = pcfg
    self.info.fileIsFixed = None
    self.info.abortMessageCount = abortMessageCount
    self.info.experimental = experimental
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

  def checkFile(self,fpath,log=None,attributeMappings=[], getdrs=True):
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
    if not self.info.pcfg.projectV.id[:2] == '__':
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
    self.cgd.check( self.cfn.var, self.cfn.freq, self.da, self.va, self.cga.isInstantaneous, self.vocabs )
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
    if getdrs:
      self.drs = self.cga.getDrs()
      self.drs['project'] = self.info.pcfg.projectV.id
    self.errorCount = self.cfn.errorCount + self.cga.errorCount + self.cgd.errorCount + self.cgg.errorCount

class main(object):
  """Main entry point for execution.

     All compliance tests are completed in the instantiation of a "main" object. The object created will contain attributes with test results.
  """
  

  def __init__(self,args=None,abortMessageCount=-1,printInfo=False,monitorFileHandles = False,cmdl=None):
    logDict = {}
    ecount = 0
    c4i = c4_init(args=args)
    c4i.logger.info( 'Starting batch -- number of file: %s' % (len(c4i.flist)) )
    c4i.logger.info( 'Source: %s' % c4i.source )
    if cmdl != None:
      c4i.logger.info( 'Command: %s' % cmdl )
      
    isDummy  = c4i.project[:2] == '__'
    if (ncLib == None) and (not isDummy):
       raise baseException( 'Cannot proceed with non-dummy [%s] project without a netcdf API' % (c4i.project) )
    pcfg = config.projectConfig( c4i.project )
    assert pcfg.projectV.v == -1, 'Cannot handle anything other than latest version at present'
    ncReader = fileMetadata(dummy=isDummy, attributeMappingsLog=c4i.attributeMappingsLog,forceLib=c4i.forceNetcdfLib)
    c4i.logger.info( 'Python netcdf: %s' % ncReader.ncLib )
    self.cc = checker(pcfg, c4i.project, ncReader,abortMessageCount=abortMessageCount, experimental=c4i.experimental)
    rec = recorder( c4i.project, c4i.recordFile, dummy=isDummy )
    self.ncLib = ncLib

    # This list will record the drs dictionaries of all checked files for export to JSON
    drs_list = []

    if monitorFileHandles:
      self.monitor = utils.sysMonitor()
    else:
      self.monitor = None

    cal = None
    if len( c4i.errs ) > 0:
      for i in range(0,len( c4i.errs ), 2 ):
        c4i.logger.info( c4i.errs[i] )
  
    self.cc.info.amapListDraft = []
    cbv = utils.checkByVar( parent=self.cc.info,cls=c4i.project,monitor=self.monitor)
    if c4i.project not in ['ESA-CCI']:
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
        self.cc.checkFile( f, log=fLogger,attributeMappings=c4i.attributeMappings, getdrs=c4i.getdrs )

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
            drs_list.append({'path': f, 'drs': self.cc.drs})
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
    
    if c4i.project not in ['SPECS','CCMI','CMIP5','ESA-CCI']:
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

    #!TODO: the recorder class could export JSON if it recorded the full drs dictionaries.
    #       This lightweight solution re-uses the filename from the rec class and dumps
    #       JSON in a separate function.
    json_file = os.path.splitext(rec.file)[0] + '.json'
    dump_drs_list(drs_list, json_file)

    if printInfo:
      print 'Error count %s' % ecount
    ##c4i.hdlr.close()
    c4i.closeBatchLog()
    self.ok = all( map( lambda x: x[0], self.resList ) )


def dump_drs_list(drs_list, filename):
    import json
    fh = open(filename, 'a+')
    for drs in drs_list:
                fh.write(json.dumps(drs))
                fh.write('\n')
    fh.close()
