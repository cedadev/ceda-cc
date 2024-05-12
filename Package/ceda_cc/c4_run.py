"""ceda_cc
##########
Entry point for API.

USAGE
#####
c4_run.main( <argument list> )
"""
import sys
from ceda_cc.ccinit import c4_init

testmain=False
## callout to summary.py: if this option is selected, imports of libraries are not needed.
if not testmain:
  if __name__ == '__main__':
   if len(sys.argv) > 1:
     if sys.argv[1] == '--sum':
        from . import summary
        summary.summariseLogs()
        raise SystemExit(0)
     elif sys.argv[1] == '-v':
        from .versionConfig import version, versionComment
        print('ceda-cc version %s [%s]' % (version,versionComment))
        raise SystemExit(0)
     elif sys.argv[1] == '--unitTest':
        print("Starting test suite 1")
        from . import unitTestsS1
        print("Starting test suite 2")
        from . import unitTestsS2
        print("Tests completed")
        raise SystemExit(0)
   else:
     print(__doc__)
     raise SystemExit(0)

# Standard library imports
import os, time, glob, pkgutil
import shutil
## pkgutil is used in file_utils
# Third party imports

## Local imports with 3rd party dependencies
#### netcdf --- currently only support for cmds2 -- re-arranged to facilitate support for alternative modules

import ceda_cc.file_utils

from ceda_cc.file_utils import fileMetadata, ncLib

# Local imports
import ceda_cc.utils_c4 as utils
from ceda_cc.ceda_cc_config import config_c4 as config

##reload( utils )

from ceda_cc.xceptions import baseException

from ceda_cc.fcc_utils2 import tupsort


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
                 'ccmi2022':'%(mip_era)s/%(activity_id)s/%(institution_id)s/%(source_id)s/%(experiment_id)s/%(variant_label)s/%(table_id)s/%(realm)s/files/%%(version)s/%(variable)s/', \
                 'snapsi':'%(mip_era)s/%(activity_id)s/%(institution_id)s/%(source_id)s/%(experiment_id)s/%(variant_label)s/%(table_id)s/%(realm)s/files/%%(version)s/%(variable)s/', \
                 'ramip':'%(project)s/%(institute)s/%(source_id)s/%(experiment)s/%(variant_label)s/%(table)s/%(variable)s/%(grid_id)s/%(version)s/', \
                 'esa-cci':'%(level)s/%(platform)s/%(sensor)s/%(variable)s/', \
                 '__def__':'%(project)s/%(product)s/%(institute)s/%(model)s/%(experiment)s/%(frequency)s/%(realm)s/%(variable)s/%(ensemble)s/files/%%(version)s/', \
               }

## core drs: list of vocab names
## path template: -- current version puts upper case in "project"
## dataset template:  

class recorder(object):

  def __init__(self,project,filename,type='map',dummy=false):
    self.dummy = dummy
    self.file = filename
    self.type = type
    self.pathtmpl = '%(project)s/%(product)s/%(domain)s/%(institute)s/%(driving_model)s/%(experiment)s/%(ensemble)s/%(model)s/%(model_version)s/%(frequency)s/%(variable)s/files/%%(version)s/'
    self.pathtmpl = pathtmpldict.get(project,pathtmpldict['__def__'])
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

  def add(self,fpath,drs,safe=true):
    assert self.type == 'map','can only do map files at present'
    assert type(drs) == type( {} ), '2nd user argument to method add should be a dictionary [%s]' % type(drs)
    tpath = self.pathtmpl % drs
    if not self.dummy:
      assert os.path.isfile( fpath ), 'file %s not found' % fpath
      fdate = time.ctime(os.path.getmtime(fpath))
      sz = os.stat(fpath).st_size
    else:
      fdate = "na"
      sz = 0
    record = '%s | ok | %s | modtime = %s | target = %s ' % (fpath,sz,fdate,tpath)
    fn = fpath.split( '/' )[-1]
    for k in ['creation_date','tracking_id']:
      if k in list(drs.keys()):
        record += ' | %s = %s' % (k,drs[k])
        if k == 'tracking_id':
          self.tidtupl.append( (fn,drs[k]) )

    self.records[fn] = record
  
  def modify(self,fn,msg):
    assert fn in list(self.records.keys()),'attempt to modify non-existent record %s, %s' % [fn,str(list(self.records.keys())[0:10])]
    if self.records[fn].find( '| ok |') == -1:
      ##print 'file %s already flagged with errors' % fn
      return
    s = self.records[fn].replace( '| ok |', '| %s |' % msg )
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
        print('duplicate tracking_id: %s, %s:: %s' % (self.tidtupl[k][0],self.tidtupl[k+1][0],self.tidtupl[k][1]))
        nd += 1
        if len(fnl) == 0 or fnl[-1] != self.tidtupl[k][0]:
          fnl.append( self.tidtupl[k][0])
        fnl.append( self.tidtupl[k+1][0])
    if nd == 0:
      print('no duplicate tracking ids found in %s files' % len(self.tidtupl))
    else:
      print('%s duplicate tracking ids' % nd)
      for f in fnl:
        self.modify( f, 'error: duplicate tid' )

  def dumpall(self,safe=true):
    keys = list(self.records.keys())
    keys.sort()
    for k in keys:
      self.dump( self.records[k], safe=safe )

  def dump( self, record, safe=true ):
    if safe:
      self.open()
    self.fh.write( record + '\n' )
    if safe:
      self.close()

  def adderr(self,fpath,reason,safe=true):
    record = '%s | %s' % (fpath, reason)
    fn = fpath.split( '/' )[-1]
    self.records[fn] = record

class checker(object):
  def __init__(self, pcfg, cls,reader,abortmessagecount=-1,experimental=false):
    self.info = dummy()
    self.info.pcfg = pcfg
    self.info.fileisfixed = none
    self.info.abortmessagecount = abortmessagecount
    self.info.experimental = experimental
    self.calendar = 'none'
    self.ncreader = reader
    self.cfn = utils.checkfilename( parent=self.info,cls=cls)
    self.cga = utils.checkglobalattributes( parent=self.info,cls=cls)
    self.cgd = utils.checkstandarddims( parent=self.info,cls=cls)
    self.cgg = utils.checkgrids( parent=self.info,cls=cls)
    self.cls = cls

    # define vocabs based on project
    ##self.vocabs = getvocabs(pcgf)
    self.vocabs = pcfg.vocabs

  def checkfile(self,fpath,log=none,attributemappings=[], getdrs=true):
    self.calendar = 'none'
    self.info.log = log

    fn = fpath.split( '/' )[-1]

    if attributemappings != []:
      self.ncreader.loadnc( fpath )
      self.ncreader.applymap( attributemappings, self.cfn.globalattributesinfn, log=log )
      ncred = true
      thisfn = self.ncreader.fn
    else:
      ncred = false
      thisfn = fn

    self.cfn.check( thisfn )
    if not self.cfn.completed:
      self.completed = false
      return
    if not self.info.pcfg.projectv.id[:2] == '__':
      if not os.path.isfile( fpath ):
        print('file %s not found [2]' % fpath)
        self.completed = false
        return

    self.info.fntimetuples = self.cfn.fntimetuples

    if not ncred:
      ##print fpath
      self.ncreader.loadnc( fpath )
    self.ga = self.ncreader.ga
    self.va = self.ncreader.va
    self.da = self.ncreader.da

    if self.cfn.freq is not none:
      vgroup = self.cfn.freq
    else:
      vgroup = self.info.pcfg.mipvocabvgmap.get(self.cfn.group,self.cfn.group)
    self.cga.check( self.ga, self.va, self.cfn.var, vgroup, self.vocabs, self.cfn.fnparts )
    if not self.cga.completed:
      self.completed = false
      return

    ##self.cgd.plevrequired = config.plevrequired
    ##self.cgd.plevvalues = config.plevvalues
    ##self.cgd.heightrequired = config.heightrequired
    ##self.cgd.heightvalues = config.heightvalues
    ##self.cgd.heightrange = config.heightrange
    self.cgd.check( self.cfn.var, self.cfn.freq, self.da, self.va, self.cga.isinstantaneous, self.vocabs, self.cfn.fnparts )
    self.calendar = self.cgd.calendar
    if not self.cgd.completed:
      self.completed = false
      return

    if self.info.pcfg.docheckgrids:
      ##self.cgg.rotatedpolegrids = config.rotatedpolegrids
      ##self.cgg.interpolatedgrids = config.interpolatedgrids
      self.cgg.check( self.cfn.var, self.cfn.domain, self.da, self.va )
    
      if not self.cgg.completed:
        self.completed = false
        return
    self.completed = true
    if getdrs:
      self.drs = self.cga.getdrs()
      self.drs['project'] = self.info.pcfg.projectv.id
    self.errorcount = self.cfn.errorcount + self.cga.errorcount + self.cgd.errorcount + self.cgg.errorcount

class main(object):
  """main entry point for execution.

     all compliance tests are completed in the execution of the "main.run()" method. test results are aggregated in a number of attributes.
  """
  

  def __init__(self,args=none,abortmessagecount=-1,monitorfilehandles = false,cmdl=none):
    """instantiation sets up logging, imports the package configuration, and creates a checker instance.
       a monitor to check on open file handles is created if required (this was needed to deal with accumulation of zombie file handles in an earlier version) """

    self.logdict = {}
    self.monitorfilehandles = monitorfilehandles
    c4i = c4_init(args=args)
    self.c4i = c4i
    c4i.logger.info( 'starting batch -- number of file: %s' % (len(c4i.flist)) )
    c4i.logger.info( 'source: %s' % c4i.source )
    if cmdl is not none:
      c4i.logger.info( 'command: %s' % cmdl )
      
    isdummy  = c4i.project[:2] == '__'
    if (nclib is none) and (not isdummy):
       raise baseexception( 'cannot proceed with non-dummy [%s] project without a netcdf api' % (c4i.project) )
    pcfg = config.projectconfig( c4i.project )
    assert pcfg.projectv.v == -1, 'cannot handle anything other than latest version at present'
    self.ncreader = filemetadata(dummy=isdummy, attributemappingslog=c4i.attributemappingslog,forcelib=c4i.forcenetcdflib)
    c4i.logger.info( 'python netcdf: %s' % self.ncreader.nclib )
    self.cc = checker(pcfg, c4i.project, self.ncreader,abortmessagecount=abortmessagecount, experimental=c4i.experimental)
    self.rec = recorder( c4i.project, c4i.recordfile, dummy=isdummy )
    self.nclib = nclib

    # this list will record the drs dictionaries of all checked files for export to json

    if monitorfilehandles:
      self.monitor = utils.sysmonitor()
    else:
      self.monitor = none

    if len( c4i.errs ) > 0:
      for i in range(0,len( c4i.errs ), 2 ):
        c4i.logger.info( c4i.errs[i] )
  
    self.cc.info.amaplistdraft = []

  def run(self, printinfo=false):
    drs_list = []
    cal = none
    ecount = 0
    filelogopen = false
    self.reslist =  []
    stdoutsum = 2000
    cbv = utils.checkbyvar( parent=self.cc.info,cls=self.c4i.project,monitor=self.monitor)
    if self.c4i.project not in ['esa-cci']:
      cbv.impt( self.c4i.flist )
      if printinfo:
        print(cbv.info)
    npass = 0
    kf = 0
    for f in self.c4i.flist:
      kf += 1
      rv = false
      ec = none
      if self.monitorfilehandles:
        nofhstart = self.monitor.get_open_fds()
      fn = f.split('/')[-1]
      self.c4i.logger.info( 'starting: %s' % fn )
      try:
  ### need to have a unique name, otherwise get mixing of logs despite close statement below.
  ### if duplicate file names are present, this will be recorded in the main log, tag appended to file level log name (not yet tested).
        if self.c4i.logbyfile:
          flogger = self.c4i.getfilelog( fn )
          self.logdict[fn] = self.c4i.filelogfile
          self.c4i.logger.info( 'log file: %s' % self.c4i.filelogfile )
          filelogopen = true
        else:
          flogger = self.c4i.logger
  
        flogger.info( 'starting file %s' % fn )
## default appending to myapp.log; mode='w' forces a new file (deleting old contents).
        self.cc.checkfile( f, log=flogger,attributemappings=self.c4i.attributemappings, getdrs=self.c4i.getdrs )

        if self.cc.completed:
          if cal not in (none, 'none') and self.cc.cgd.vargroup != "fx":
            if cal != self.cc.calendar:
              cal_change_err_msg = 'error: change in calendar attribute %s --> %s' % (cal, self.cc.calendar)
              self.c4i.logger.info(cal_change_err_msg)
              flogger.info(cal_change_err_msg)
              self.cc.errorcount += 1

          cal = self.cc.calendar
          ec = self.cc.errorcount
        rv =  ec == 0
        if rv:
          npass += 1
        self.reslist.append( (rv,ec) )

        if self.c4i.logbyfile:
          if self.cc.completed:
            flogger.info( 'done -- error count %s' % self.cc.errorcount )
          else:
            flogger.info( 'done -- checks not completed' )
          self.c4i.closefilelog( )
          filelogopen = false

        if self.cc.completed:
          self.c4i.logger.info( 'done -- error count %s' % self.cc.errorcount ) 
          ecount += self.cc.errorcount
          if self.cc.errorcount == 0:
            self.rec.add( f, self.cc.drs )
            drs_list.append({'path': f, 'drs': self.cc.drs})
          else:
            self.rec.adderr( f, 'errors found | errorcount = %s' % self.cc.errorcount )
        else:
          ecount += 20
          self.c4i.logger.info( 'done -- testing aborted because of severity of errors' )
          self.rec.adderr( f, 'errors found and checks aborted' )
      except:
        self.c4i.logger.error("exception has occured" ,exc_info=1)
        if filelogopen:
          flogger.error("c4.100.001: [exception]: failed:: exception has occured" ,exc_info=1)
          self.c4i.closefilelog( )
          filelogopen = false
        self.rec.adderr( f, 'error: exception' )
        if not self.c4i.holdexceptions:
          raise
      if stdoutsum > 0 and kf%stdoutsum == 0:
         print('%s files checked; %s passed this round' % (kf,npass))
      if self.monitorfilehandles:
        nofhend = self.monitor.get_open_fds()
        if nofhend > nofhstart:
           print('open file handles: %s --- %s' % (nofhstart, nofhend))
  
    self.cc.info.log = self.c4i.logger
    
    if self.c4i.project not in ['specs','ccmi','snapsi','ramip','ccmi2022', 'CMIP5','ESA-CCI']:
       cbv.c4i = self.c4i
       cbv.setLogDict( self.logDict )
       cbv.check( recorder=self.rec, calendar=self.cc.calendar)
       try:
         ecount += cbv.errorCount
       except:
         ecount = None
    self.ncReader.close()
    if type( self.cc.info.amapListDraft ) == type( [] ) and len(  self.cc.info.amapListDraft ) > 0:
      ll =  self.cc.info.amapListDraft
      ll.sort()
      oo = open( 'amapDraft.txt', 'w' )
      oo.write( ll[0] + '\n' )
      for i in range( 1,len(ll) ):
        if ll[i] != ll[i-1]:
          oo.write( ll[i] + '\n' )
      oo.close()
    if self.c4i.project in ['SPECS','CCMI','CMIP5']:
      self.rec.checktids()
    self.rec.dumpAll()

    #!TODO: the recorder class could export JSON if it recorded the full drs dictionaries.
    #       This lightweight solution re-uses the filename from the rec class and dumps
    #       JSON in a separate function.
    json_file = os.path.splitext(self.rec.file)[0] + '.json'
    dump_drs_list(drs_list, json_file)

    if printInfo:
      print('Error count %s' % ecount)
    ##c4i.hdlr.close()
    self.c4i.closeBatchLog()
    self.ok = all( [x[0] for x in self.resList] )


def dump_drs_list(drs_list, filename):
    import json
    fh = open(filename, 'a+')
    for drs in drs_list:
                fh.write(json.dumps(drs))
                fh.write('\n')
    fh.close()
