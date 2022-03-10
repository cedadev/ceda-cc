"""A set of classes running checks and providing utilities to support checks"""
import re, os, sys, traceback, ctypes, collections, importlib

def strmm3( mm ):
  return '; '.join( ['%s="%s" [correct: "%s"]' % x for x in mm] )

from ceda_cc.xceptions import *

re_dlr01 = re.compile( 'MERGED-DLR_1M-[0-9]{8}-fv0100.nc$' )

class timeInt(object):

   vc = {'gregorian':0, 'standard':0, 'proleptic_gregorian':0, 'noleap':1, '365_day':1, 'all_leap':2, '366_day':2, '360_day':3, 'julian':0, 'none':None}
   mnmx = [ (365,366),(365,365),(366,366),(360,360) ]
   mmnmmx = [ (28,31),(28,31),(29,31),(30,30) ]
   def __init__(self,cal='proleptic_gregorian',dpymn=None, dpymx=None,dpmmn=None,dpmmx=None,tol=1.e-6):
     self.tol = tol
     if cal not in self.vc or cal is None:
       assert dpymx is not None and dpymn is not None, 'If standard calendar is not use, dpymn and dpymx must be set'
       assert dpmmx is not None and dpmmn is not None, 'If standard calendar is not use, dpmmn and dpmmx must be set'
       self.dpymn = dpymn - tol
       self.dpymx = dpymx + tol
       self.dpmmn = dpmmn - tol
       self.dpmmx = dpmmx + tol
     else:
       self.dpymn = self.mnmx[self.vc[cal]][0] - tol
       self.dpymx = self.mnmx[self.vc[cal]][1] + tol
       self.dpmmn = self.mmnmmx[self.vc[cal]][0] - tol
       self.dpmmx = self.mmnmmx[self.vc[cal]][1] + tol
     self.map = { 'yr':'P1Y','monClim':'P1M','mon':'P1M','day':'P1D','6hr':'P6H','3hr':'P3H', '1hr':'P1H'}
     self.nd = { 'x':'y' }

   def setUnit(self,u):
     if u not in ['days','months','years']:
         print('Time unit %s not supported' % u)
         self.u = None
     else:
         self.u = u

   def chk(self,v,u,f):
      if f not in self.map:
         return (0,'No frequency check available for f = %s' % f )
      if u not in ['days']:
         return (0,'No frequency check available for units = %s' % u )
      x = self.map(f)
      if x == 'P1Y':
        return (v > self.dpymn) and (v < self.dpymx)
      elif x == 'P1M':
        return (v > self.dpmmn) and (v < self.dpmmx)
      elif x == 'P1D':
        return (v > 1.-self.tol) and (v < 1.+self.tol)
      elif x == 'P6H':
        return (v > 0.25-self.tol) and (v < 0.25+self.tol)
      elif x == 'P3H':
        return (v > 0.125-self.tol) and (v < 0.125+self.tol)
      

class reportSection(object):

  def __init__(self,id,cls,parent=None, description=None):
    self.id = id
    self.cls = cls
    self.parent = parent
    self.description = description
    self.records = []
    self.subsections = []
    self.closed = False
    self.npass = 0
    self.fail = 0
    self.auditDone = True

  def addSubSection( self, id, cls, description=None):
    assert not self.closed, 'Attempt to add sub-section to closed report section'
    self.subsections.append( reportSection(id, cls, parent=self, description=description )  )
    self.auditDone = False
    return self.subsections[-1]

  def addRecord( self, id, cls, res, msg ):
    assert not self.closed, 'Attempt to add record to closed report section'
    self.records.append( (id, cls, res, msg) )
    self.auditDone = False

  def close(self):
    self.closed = True

  def reopen(self):
    self.closed = False

  def audit(self):
    if self.auditDone:
      return
    self.closed = True
    self.fail = 0
    self.npass = 0
    for ss in self.subsections:
      ss.audit()
      self.fail += ss.fail
      self.npass += ss.npass

    for r in self.records:
      if r[2]:
        self.npass += 1
      else:
        self.fail += 1

class checkSeq(object):
  def __init__(self):
    pass

  def check(self,x):
    d = [x[i+1] - x[i] for i in range(len(x)-1)]
    self.delt = sum(d)/len(d)
    self.dmx = max(d)
    self.dmn = min(d)
    return self.dmx - self.dmn < abs(self.delt)*1.e-4

cs = checkSeq()

class CheckBase(object):
  """Base class for checks, containing a set of standard methods for managing operation of checks and logging of results"""

  def  __init__(self,cls="CORDEX",reportPass=True,parent=None,monitor=None):
    """Creat class instance: set defaults, link arguments to instance, create a range of compiled regular expressions"""
    self.cls = cls
    self.project = cls
    self.abortMessageCount = parent.abortMessageCount
    self.monitor = monitor
    self.re_isInt = re.compile( '[0-9]+' )
    self.errorCount = 0
    self.passCount = 0
    self.missingValue = 1.e20
    self.missingValue = ctypes.c_float(1.00000002004e+20).value
    from ceda_cc.file_utils import ncLib
    if ncLib == 'netCDF4':
      import numpy
      self.missingValue = numpy.float32(self.missingValue)
    self.parent = parent
    self.reportPass=reportPass
    self.pcfg = parent.pcfg
################################
    self.requiredGlobalAttributes = self.pcfg.requiredGlobalAttributes
    self.controlledGlobalAttributes = self.pcfg.controlledGlobalAttributes
    self.globalAttributesInFn = self.pcfg.globalAttributesInFn
    self.requiredVarAttributes = self.pcfg.requiredVarAttributes
    self.drsMappings = self.pcfg.drsMappings
#######################################
    self.checks = ()
    self.plugins = ()
    self.agents = ()
    self.messageCount = 0

## call init method defined in implementing class 
    self.init()

## call initPlugs method to initialise any plugins defined by init
    self.__initPlugs__()

    if not hasattr( self.parent, 'amapListDraft' ):
      self.parent.amapListDraft = []

  def isInt(self,x):
    """Check that a string is a representation of an integer"""
    return self.re_isInt.match( x ) is not None

  def logMessage(self, msg, error=False ):
    """Log messages and count messages"""
    self.messageCount += 1
    assert self.abortMessageCount < 0 or self.abortMessageCount > self.messageCount, 'Raising error [TESTX01], perhaps for testing'
    if self.parent is not None and self.parent.log is not None:
       if error:
         self.parent.log.error( msg )
       else:
         self.parent.log.info( msg )
    else:
       print(msg)

    doThis = True
    if self.appendLogfile[0] is not None and doThis:
      if self.monitor is not None:
         nofh0 = self.monitor.get_open_fds()
      xlog = self.c4i.getFileLog( self.appendLogfile[1], flf=self.appendLogfile[0] )
      if error:
         xlog.error( msg )
      else:
         xlog.info( msg )
      self.c4i.closeFileLog()
      if self.monitor is not None:
         nofh9 = self.monitor.get_open_fds()
         if nofh9 > nofh0:
           print('Leaking file handles [1]: %s --- %s' % (nofh0, nofh9))

  def log_exception( self, msg):
    """Logging of exceptions -- putting trace information in log files"""
    if self.parent is not None and self.parent.log is not None:
        self.parent.log.error("Exception has occured" ,exc_info=1)
    else:
        traceback.print_exc(file=sys.stdout)

  def log_error( self, msg ):
    """Create an error log message and call logMessage; count errors;"""
    self.lastError = msg
    self.errorCount += 1
    self.logMessage( '%s.%s: FAILED:: %s' % (self.id,self.getCheckId(),msg), error=True )

  def log_pass( self ):
    """Create a pass log message and call logMessage; count passes;"""
    self.passCount = True
    if self.reportPass:
      self.logMessage(  '%s.%s: OK' % (self.id,self.getCheckId()) )

  def log_abort( self ):
    self.completed = False
    self.logMessage(   '%s.%s: ABORTED:: Errors too severe to complete further checks in this module' % (self.id,'xxx') )
    raise abortChecks

  def status(self):
    return '%s.%s' % (self.id,self.getCheckId())

  def getCheckId(self,full=True):
    if type( self.checkId ) == type( 'x' ):
      return self.checkId
    else:
      if full:
        return '%s: [%s]' % self.checkId
      else:
        return self.checkId[0]

  def test(self,res,msg,abort=False,part=False,appendLogfile=(None,None)):
    """Handle test results. 
      :param res: [True/False] result of test;
      :param msg: Message describing the test;
      :param abort: {optional} Set True if checks should be aborted when test fails;
      :param part: {optional} Set True if this is a component of a test (logging of pass suppressed);
      :param appendLogfile: {optional} Allows results to be appended to pre-existing log file;
    """
    self.appendLogfile = appendLogfile
    if res:
      if not part:
         self.log_pass()
    else:
      self.log_error(msg)
      if abort:
        self.log_abort()
    return res


  def __initPlugs__(self):
    if len( self.plugins ) > 0:
      l = []
      for p in self.plugins:
        mod = importlib.import_module( 'plugins.%s' % p )
        agent = mod.checker(self)
        l.append(agent)
      self.agents = tuple( l )

  def runChecks(self):
    """Run all the checks registered in this instance (in self.checks) and handle exceptions"""

    try:
      for c in self.checks:
        c()  # run check
      for agent in self.agents:
        agent.run() # run check
      self.completed = True
    except abortChecks:
      ## error logging done before raising this exception
      return
    except:
      self.log_exception( 'Exception caught by runChecks' )
      raise loggedException
    
class checkFileName(CheckBase):
  """Check basic syntax of file names (i.e. checks properties of the text string, it does not attempt to access the file).
Inherits :class:`CheckBase` class. Checks are run by the :meth:`check` method."""

  def init(self):
    self.id = 'C4.001'
    self.checkId = 'unset'
    self.isFixed = False
    self.step = 'Initialised'
    self.checks = (self.do_check_fn,self.do_check_fnextra)
    self.re_c1 = re.compile( '^[0-9]*$' )
    self.fnDict = {}
    self.fnTimeTuples = None
####

  def check(self,fn):
    """Initiate checks: manage arguments and then call *runChecks* (inherited from CheckBase class).
  Arguments: fn: file name: the file name to be checked."""
    self.errorCount = 0
    assert type(fn) in [type('x'),type('x')], '1st argument to "check" method of checkGrids shound be a string variable name (not %s)' % type(fn)
    self.fn = fn
    self.fnsep = self.pcfg.fNameSep

    self.runChecks()
    self.parent.fnDict = self.fnDict
###
  def do_check_fn(self):
    """Basic file name checks:
       (1) Check suffix;
       (1b) [for ESA-CCI files] check presence of "ESACCI" and identify file naming convention;
       (2) Split file name into components and check number of such components;
       (3) Additional specialist checks for ESA-CCI, CORDEX, CMIP-type (for the time range).
    """
    fn = self.fn
    self.errorCount = 0
    self.completed = False

## check basic parsing of file name
    self.checkId = ('001','parse_filename')
    self.test( fn[-3:] == '.nc', 'File name ending ".nc" expected', abort=True, part=True )
    bits = fn[:-3].split( self.fnsep )

    self.fnParts = bits[:]
    if self.pcfg.domainIndex is not None:
      self.domain = self.fnParts[self.pcfg.domainIndex]
    else:
      self.domain = None


    if self.pcfg.projectV.id in ['ESA-CCI']:
      self.test( 'ESACCI' in bits[:2] or 'ESA' == bits[0], 'File name not a valid ESA-CCI file name: %s' % fn, abort=True )
      if bits[0] == 'ESA':
        self.esaFnId = 2
      elif bits[0] == 'ESACCI':
        self.esaFnId = 1
      else:
        self.esaFnId = 0
        bb = bits[2].split( '_' )
        self.test( bits[2][0] == 'L' and len(bb) == 2, 'Cannot parse ESA-CCI file name: %s' % fn, abort=True )
        bits = bits[:2] + bb + bits[3:]
        self.fnParts = bits[:]
        
      self.pcfg.setEsaCciFNType(self.esaFnId)
    self.test( len(bits) in self.pcfg.fnPartsOkLen, 'File name not parsed in %s elements [%s]' % (str(self.pcfg.fnPartsOkLen),str(bits)), abort=True )

    self.fnDict = {}
    if self.pcfg.projectV.id in ['ESA-CCI']:
      l0 = {0:6, 1:5, 2:5}[self.esaFnId]  
      for i in range(l0):
        x = self.pcfg.globalAttributesInFn[i]
        if x is not None and x[0] == '*':
          self.fnDict[x[1:]] = bits[i]
      self.fnDict['version'] = bits[-1]
      self.fnDict['gdsv'] = 'na'
      if self.esaFnId == 0:
        if len(bits) == 9:
          self.fnDict['additional'] = bits[-3]
          self.fnDict['gdsv'] = bits[-2]
        elif len(bits) == 8:
          if bits[-2][0] == 'v':
            self.fnDict['gdsv'] = bits[-2]
          else:
            self.fnDict['additional'] = bits[-2]
      elif self.esaFnId in [1,2]:
        if len(bits) == 8:
          self.fnDict['additional'] = bits[-3]

          
    
    if self.pcfg.groupIndex is not None:
      self.group = self.fnParts[self.pcfg.groupIndex]
    else:
      self.group = None

    if self.pcfg.freqIndex is not None:
      self.freq = self.fnParts[self.pcfg.freqIndex]
    elif self.group in ['fx','fixed']:
      self.freq = 'fx'
    else:
      self.freq = None

    ##if self.cls == 'CORDEX':
      ##self.freq = self.fnParts[7]
    ##elif self.cls == 'SPECS':
      ##self.freq = self.fnParts[1]

    self.var = self.fnParts[self.pcfg.varIndex]

    if self.pcfg.fnvdict is not None:
      if self.var in self.pcfg.fnvdict:
        self.var = self.pcfg.fnvdict.get( self.var )['v']
      else:
        addi = self.fnDict.get('additional','xxxx')
        thiskey = '%s:%s' % (self.var,addi)
        if thiskey in self.pcfg.fnvdict:
          self.var = self.pcfg.fnvdict.get( thiskey )['v']

    self.isFixed = self.freq in ['fx','fixed']
    self.parent.fileIsFixed = self.isFixed
    if self.isFixed:
      self.test( len(self.fnParts) in self.pcfg.fnPartsOkFixedLen, 'Number of file name elements not acceptable for fixed data' )

    self.checkId = ('002','parse_filename_timerange')
    if not self.isFixed:

## test time segment
      if self.pcfg.trangeType == 'CMIP':
        bits = self.fnParts[-1].split( '-' )
        self.test( len(bits) == 2, 'File time segment [%s] will not parse into 2 elements' % (self.fnParts[-1] ), abort=True, part=True )

        self.test(  len(bits[0]) == len(bits[1]), 'Start and end time specified in file name [%s] of unequal length' % (self.fnParts[-1] ), abort=True, part=True  )
        self.test(  int(bits[0]) <= int(bits[1]), 'Start and end time specified in file name [%s] in wrong order' % (self.fnParts[-1] ), abort=True, part=True  )

        for b in bits:
          self.test( self.isInt(b), 'Time segment in filename [%s] contains non integer characters' % (self.fnParts[-1] ),  abort=True, part=True  )
        self.log_pass()
        self.fnTimeParts = bits[:]
        l0 = []
        ## pick out month, day, hours etc, until end of string )
        for b in bits:
          l00 = [int( b[:4] ),]
          k0 = 4
          while k0 + 2 <= len(b):
            l00.append( int( b[k0:k0+2] ) )
            k0 += 2
          l0.append( tuple( l00 ) )
            
        self.fnTimeTuples = tuple( l0 )

      elif self.pcfg.trangeType == 'ESA-CCI':
        self.pcfg.checkTrangeLen = False
        tt = self.fnParts[self.pcfg.trangeIndex] 
        if self.test( len(tt) in [4,6,8,10,12,14] and self.re_c1.match(tt) is not None, 'Length of indicative date/time not consistent with YYYY[MM[DD[HH[MM[SS]]]]] specification: %s' % self.fnParts[-1], part=True  ):
          ll = [tt[:4],]
          tt = tt[4:]
          for j in range(5):
            if len(tt) > 0:
              ll.append( tt[:2] )
              tt = tt[2:]
            elif j in [1,2]:
              ll.append( '01' )
            else:
              ll.append( '00' )
          indDateTime = list(map( int, ll ))
          self.test( indDateTime[1] in range(1,13), 'Invalid Month in indicative date time %s' % str(ll), part=True )
          self.test( indDateTime[2] in range(1,32), 'Invalid Day in indicative date time %s' % str(ll), part=True )
          self.test( indDateTime[3] in range(25), 'Invalid hour in indicative date time %s' % str(ll), part=True )
          self.test( indDateTime[4] in range(60), 'Invalid minute in indicative date time %s' % str(ll), part=True )
          self.test( indDateTime[5] in range(60), 'Invalid second in indicative date time %s' % str(ll), part=True )

    self.checkId = '003'

    self.checkId, ok = (('004','filename_timerange_length'),True)
    if (not self.isFixed) and self.pcfg.checkTrangeLen:
      ltr = { 'mon':6, 'sem':6, 'day':8, '3hr':[10,12], '6hr':10, '1hr':12 }
      ok &=self.test( self.freq in list(ltr.keys()), 'Frequency [%s] not recognised' % self.freq, part=True )
      if ok:
        if type( ltr[self.freq] ) == type(0):
          msg = 'Length of time range parts [%s,%s] not equal to required length [%s] for frequency %s' % (self.fnTimeParts[0],self.fnTimeParts[1],ltr[self.freq],self.freq)
          ok &= self.test( len(self.fnTimeParts[0]) == ltr[self.freq], msg, part=True )
        elif type( ltr[self.freq] ) in [type([]),type( () )]:
          msg = 'Length of time range parts [%s,%s] not in acceptable list [%s] for frequency %s' % (self.fnTimeParts[0],self.fnTimeParts[1],str(ltr[self.freq]),self.freq)
          ok &= self.test( len(self.fnTimeParts[0]) in ltr[self.freq], msg, part=True )

      if ok:
        self.log_pass()

  def do_check_fnextra(self):
    """Check whether file name components match constraints -- but only if those constraints are not implicitly verified through comparison with global attributes in later checks"""
    self.checkId = ('004','file_name_extra' )
    vocabs = self.pcfg.vocabs
    m = []
    for a in self.pcfg.controlledFnParts:
      if a in self.fnDict:
        try:
          if not vocabs[a].check( str(self.fnDict[a]) ):
            m.append( (a,self.fnDict[a],vocabs[a].note) )
        except:
          print('failed trying to check file name component %s' % a)
          raise baseException( 'failed trying to check file name component %s' % a )

    self.test( len(m)  == 0, 'File name components do not match constraints: %s' % str(m) )


class checkGlobalAttributes(CheckBase):
  """Check global and variable attributes, using tables of valid values"""

  def init(self):
    self.id = 'C4.002'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.do_check_ga,)
    self.fileId = None

  def check(self,globalAts, varAts,varName,varGroup, vocabs, fnParts):
    self.errorCount = 0
    assert type(varName) in [type('x'),type('x')], '1st argument to "check" method of checkGrids shound be a string variable name (not %s)' % type(varName)
    self.var = varName
    self.globalAts = globalAts
    self.varAts = varAts
    self.varGroup = varGroup
    self.vocabs = vocabs
    self.fnParts = fnParts
    self.runChecks()

  def getId(self):
    if self.fileId is None:
      id = self.globalAts['id']
##
## hack to allow for awkward usage in DLR ozone, where id is different for each file
## may need to improve on this if problem exists for other files in different form
##
      xx = re_dlr01.findall( id )
      if len(xx) != 0:
        id = id[:-19]
      if id != '':
        self.fileId = '%s.%s' % (self.globalAts['naming_authority'],id)
        if self.globalAts['naming_authority'] == 'uk.ac.pml':
          i0 = self.globalAts['id'].find( 'OC4v6_QAA')
          if i0 != -1:
            self.fileId = '%s.%s' % (self.globalAts['naming_authority'],self.globalAts['id'][:i0+9])
      else:
        self.fileId = '%s.:%s:%s' % (self.globalAts['naming_authority'],self.globalAts['title'],self.globalAts['time_coverage_duration'])

  def getDrs( self ):
    assert self.completed, 'method getDrs should not be called if checks have not been completed successfully'
    ee = {}
    drsDefaults = { 'convention_version':'n/a'}
    variant_ixs = ['realization', 'initialization', 'physics', 'forcing']
    if 'product' not in self.globalAts:
        self.globalAts['product'] = 'output'
    for k in self.drsMappings:
      if self.drsMappings[k] == '@var':
        ee[k] = self.var
      elif self.drsMappings[k][0] == '=':
        ee[k] = self.drsMappings[k][1:]
      elif self.drsMappings[k] == '@ensemble':
        ee[k] = "r%si%sp%s" % (self.globalAts["realization"],self.globalAts["initialization_method"],self.globalAts["physics_version"])
      elif self.drsMappings[k] == '@variant':
        ee[k] = "r%si%sp%sf%s" % tuple( [self.globalAts["%s_index" % x] for x in variant_ixs])
        if 'sub_experiment_id' in self.globalAts:
            ee[k] = '%s-%s' % (self.globalAts['sub_experiment_id'], ee[k] )
      elif self.drsMappings[k] == '@forecast_reference_time':
        x = self.globalAts.get("forecast_reference_time",'yyyy-mm-dd Thh:mm:ssZ' )
        ee[k] = "%s%s%s" % (x[:4],x[5:7],x[8:10])
      elif self.drsMappings[k] == '@mip_id':
        ee[k] = self.globalAts["table_id"].split( )[1]
      elif self.drsMappings[k] == '@ecv':
        ee[k] = self.pcfg.ecvMappings[ self.parent.fnDict['project'] ]
      elif self.drsMappings[k][0] == '$':
        self.pcfg.getExtraAtts()
        self.getId()
        if self.drsMappings[k].find(':') != -1:
          k2,dflt = self.drsMappings[k][1:].split(':')
          ee[k] = self.pcfg.extraAtts[self.fileId].get( k2, dflt )
        else:
          ee[k] = self.pcfg.extraAtts[self.fileId][self.drsMappings[k][1:]]
      elif self.drsMappings[k][0] == '*':
        thisk = self.drsMappings[k][1:]
        ee[k] = self.varAts[self.var].get(thisk,'__none__')
      elif self.drsMappings[k][0] == '#':
        thisk = self.drsMappings[k][1:]
        if thisk in drsDefaults:
          ee[k] = self.parent.fnDict.get(thisk, drsDefaults[thisk] )
        else:
          ee[k] = self.parent.fnDict[thisk]
      else:
        ee[k] = self.globalAts[ self.drsMappings[k] ]

    for k in ['creation_date','tracking_id']:
      if k in list(self.globalAts.keys()):
        ee[k] = self.globalAts[k]

    return ee

  def do_check_ga(self):
    varName = self.var
    globalAts = self.globalAts
    varAts = self.varAts
    varGroup = self.varGroup
    vocabs = self.vocabs
    fnParts = self.fnParts

    self.completed = False
    self.checkId = ('001','global_ncattribute_present')
    m = []
    for k in self.requiredGlobalAttributes:
      if k not in globalAts:
         m.append(k)
         self.globalAts[k] = '__errorReported__'

    if not self.test( len(m)  == 0, 'Required global attributes missing: %s' % str(m) ):
      gaerr = True
      for k in m:
        self.parent.amapListDraft.append( '#@;%s=%s|%s=%s' % (k,'__absent__',k,'<insert attribute value and uncomment>') )

    self.checkId = ('002','variable_in_group')

    
    if not self.test( varName in varAts, 'Expected variable [%s] not present' % varName, abort=True, part=True ):
      if varName.lower() in [x.lower() for x in varAts]:
        possible = {x.lower():x for x in varAts}[varName.lower()]
        self.parent.amapListDraft.append( '## @varname=%s|%s|Rename variable %s to %s (automation not implemented)' % (varName,possible, possible, varName) )
    
    msg = 'Variable %s not in table %s' % (varName,varGroup)
    self.test( vocabs['variable'].isInTable( varName, varGroup ), msg, abort=True, part=True )

    if self.pcfg.checkVarType:
      self.checkId = ('003','variable_type')

      mipType = vocabs['variable'].getAttr( varName, varGroup, 'type' )
      thisType = {'real':'float32', 'integer':'int32', 'float':'float32', 'double':'float64' }.get( mipType, mipType )
      variable_type = varAts[varName]['_type']

      if '>' in variable_type:
        # Big endian!
        variable_type = {'>f8': 'float64', '>f4': 'float32', '>i4': 'int32'}.get(variable_type, variable_type)
      self.test( mipType is None or variable_type == thisType, 'Variable [%s/%s] not of type %s [%s]' % (varName,varGroup,str(thisType),variable_type) )

    else:
      mipType = None

    self.checkId = ('004','variable_ncattribute_present')
    m = []
    reqAts = self.requiredVarAttributes[:]
    if (not self.parent.fileIsFixed) and self.pcfg.projectV.id in ['CORDEX']:
      reqAts.append( 'cell_methods' )
    for k in reqAts + vocabs['variable'].lists(varName, 'addRequiredAttributes'):
      if k not in varAts[varName]:
         m.append(k)
    if not self.test( len(m)  == 0, 'Required variable attributes missing: %s' % str(m) ):
      vaerr = True
      for k in m:
        self.parent.amapListDraft.append( '#@var=%s;%s=%s|%s=%s|Required attribute is missing and needs a value assigned' % (varName,k,'__absent__',k,'<insert attribute value and uncomment>') )
        ## print self.parent.amapListDraft[-1]

## need to insert a check that variable is present
    self.checkId = ('005','variable_ncattribute_mipvalues')
    ok = True
    hm = varAts[varName].get( 'missing_value', None ) is not None
    hf = '_FillValue' in varAts[varName]
    if hm or hf:
## both are not required for SPECS.
      if self.pcfg.varTables=='CMIP' and self.pcfg.projectV.id != 'SPECS':
        ok &= self.test( hm, 'missing_value must be present if _FillValue is [%s]' % varName )
        ok &= self.test( hf, '_FillValue must be present if missing_value is [%s]' % varName )
      else:
        ok = True
      if mipType == 'real':
        if 'missing_value' in varAts[varName]:
           msg = 'Variable [%s] has incorrect attribute missing_value=%s [correct: %s]' % (varName,varAts[varName]['missing_value'],self.missingValue)
### need to use ctypes here when using ncq3 to read files -- appears OK for other libraries.
           ok &= self.test( ctypes.c_float(varAts[varName]['missing_value']).value == ctypes.c_float(self.missingValue).value, msg, part=True )
        if '_FillValue' in varAts[varName]:
           msg = 'Variable [%s] has incorrect attribute _FillValue=%s [correct: %s]' % (varName,varAts[varName]['_FillValue'],self.missingValue)
           ok &= self.test( varAts[varName]['_FillValue'] == self.missingValue, msg, part=True )

    mm = []
    
    if self.pcfg.varTables=='CMIP':
      contAts = ['long_name', 'standard_name', 'units']
      if not self.parent.fileIsFixed:
      ##if varGroup not in ['fx','fixed']:
        contAts.append( 'cell_methods' )
    else:
      contAts = ['standard_name']
    hcm = "cell_methods" in varAts[varName]
    for k in contAts + vocabs['variable'].lists(varName,'addControlledAttributes'):
      targ = varAts[varName].get( k, 'Attribute not present' )
      val = vocabs['variable'].getAttr( varName, varGroup, k )

#
# . if standard_name in tables is blank, this is interpreted as no standard name.
#
      if k == "standard_name":
        if val is not None:
          if val.strip() == '':
                val = None
          else:
            if val.find( ' ' ) != -1:
              val = ' '.join( val.split(maxsplit=1) )
            if targ.find( ' ' ) != -1:
              targ = ' '.join( targ.split(maxsplit=1) )
              if targ == '':
                targ = 'Attribute not present'

      if k == "cell_methods":
        if val is not None:
          parenthesies1 = []
          targ0 = targ[:]
          while targ.find( '(' ) != -1:
            i0 = targ.index( '(' )
            i1 = targ.index( ')' )
            parenthesies1.append( targ[i0:i1+1] )
            targ = targ[:i0-1] + targ[i1+1:]
          parenthesies2 = []
          val0 = val[:]
          while val.find( '(' ) != -1:
            i0 = val.index( '(' )
            i1 = val.index( ')' )
            parenthesies2.append( val[i0:i1+1] )
            val = val[:i0-1] + val[i1+1:]
          for p in parenthesies2:
            if p not in parenthesies1:
              mm.append( (k,parenthesies1,p) )
          if targ.find( val):
             mm.append( (k,targ,val) )
      else:
          if val == None or targ == 'Attribute not present':
             pass
          elif  targ != val:
             mm.append( (k,targ,val) )

    ok &= self.test( len(mm)  == 0, 'Variable [%s] has incorrect attributes: %s' % (varName, strmm3(mm)), part=True )
    if len( mm  ) != 0:
      if self.parent.amapListDraft is None:
        self.parent.amapListDraft = []
      for m in mm:
          if m[2] is None:
            self.parent.amapListDraft.append( '## @var=%s;%s=%s|@delete=%s -- not supported yet' % (varName,m[0],m[1],m[0]) )
          else:
            self.parent.amapListDraft.append( '@var=%s;%s=%s|%s=%s|Incorrect attribute value needs to be reset' % (varName,m[0],m[1],m[0],m[2]) )

    if ok:
       self.log_pass()

    if (not self.parent.fileIsFixed) and hcm:
    ## if (varGroup not in ['fx','fixed']) and hcm:
      self.isInstantaneous = varAts[varName]['cell_methods'].find( 'time: point' ) != -1
    else:
      self.isInstantaneous = True

    self.checkId = ('006','global_ncattribute_cv' )
    m = []
    for a in self.controlledGlobalAttributes:
      if a in globalAts:
        try:
          #if not vocabs[a].check( str(globalAts[a]) ):
          if self.pcfg.legacy:
            this = vocabs[a].check( str(globalAts[a]) )
          else:
            this = vocabs[a].check( globalAts[a] )
          if not this:
            m.append( (a,globalAts[a],vocabs[a].note) )
        except:
          print('failed trying to check global attribute %s' % a)
          raise baseException( 'failed trying to check global attribute %s' % a )

    if not self.test( len(m)  == 0, 'Global attributes do not match constraints: %s' % str(m) ):
      for t in m:
        self.parent.amapListDraft.append( '#@;%s=%s|%s=%s|Required global attribute needs to be set' % (t[0],str(t[1]),t[0],'<insert attribute value and uncomment>' + str(t[2]) ) )

    self.checkId = ('007','filename_filemetadata_consistency')
    m = []
    for i in range(len(self.globalAttributesInFn)):
       gaif = self.globalAttributesInFn[i]
       if gaif is not None and gaif[0] != '*':
         if gaif[-1] == ':':
           bits = gaif.split(':')
           gaif0 = gaif
           gaif = bits[0]
           ix = int(bits[1])
         else:
           ix = i

         targVal = fnParts[ix]
         variant_ixs = ['realization', 'initialization', 'physics', 'forcing']
         if gaif[0] == "@":
           if gaif[1:] == "mip_id":
               bits = globalAts[ "table_id" ].split( ) 
               if len( bits ) > 2 and bits[0] == "Table":
                 thisVal = bits[1]
               else:
                 thisVal = globalAts[ "table_id" ]
                 self.test( False, 'Global attribute table_id does not conform to CMOR pattern ["Table ......"]: %s' % thisVal, part=True)
           elif gaif == "@ensemble":
               thisVal = "r%si%sp%s" % (globalAts["realization"],globalAts["initialization_method"],globalAts["physics_version"])
## following mappings are depricated -- introduced for SPECS and withdrawn ---
           elif gaif == '@variant':
             thisVal = "r%si%sp%sf%s" % tuple( [self.globalAts["%s_index" % x] for x in variant_ixs])
             if 'sub_experiment_id' in self.globalAts and self.globalAts['sub_experiment_id'] != 'none':
               thisVal = '%s-%s' % (self.globalAts['sub_experiment_id'],    thisVal )
           elif gaif[1:] == "experiment_family":
               thisVal = globalAts["experiment_id"][:-4]
           elif gaif[1:] == "forecast_reference_time":
               x = self.globalAts.get("forecast_reference_time",'yyyy-mm-dd Thh:mm:ssZ' )
               thisVal = "S%s%s%s" % (x[:4],x[5:7],x[8:10])
           elif gaif[1:] == "series":
               thisVal = 'series%s' % globalAts["series"]
           else:
               assert False, "Not coded to deal with this configuration: globalAttributesInFn[%s]=%s" % (i,self.globalAttributesInFn[i])
         
         else:
             thisVal = globalAts[gaif]

         if thisVal not in [targVal,'__errorReported__']:
             m.append( (i,self.globalAttributesInFn[i]) )

    self.test( len(m)  == 0,'File name segments do not match corresponding global attributes: %s' % str(m) )

    self.completed = True
       
class checkStandardDims(CheckBase):
  """Check the dimensions which are defined in the specifications"""

  def init(self):
    self.id = 'C4.003'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.check_timeVals, self.do_check,)
    ###self.plugins = ('timeAxisConsistency',)
    self.plevRequired = self.pcfg.plevRequired
    self.plevValues = self.pcfg.plevValues
    self.heightRequired = self.pcfg.heightRequired
    self.heightValues = self.pcfg.heightValues
    self.heightRange = self.pcfg.heightRange

  def check(self,varName,varGroup, da, va, isInsta,vocabs,fnParts):
    """API called from check manager *run_c4* for each file"""

    self.errorCount = 0
    assert type(varName) in [type('x'),type('x')], '1st argument to "check" method of checkGrids shound be a string variable name (not %s)' % type(varName)
    self.var = varName
    self.varGroup = varGroup
    self.da = da
    self.va = va
    self.fnParts = fnParts
    self.isInsta = isInsta
    self.vocabs = vocabs
    self.runChecks()

  def check_timeVals(self):
    da = self.da
    va = self.va
    self.errorCount = 0
    self.completed = False
    self.checkId = ('001','time_attributes')
    self.calendar = 'None'
    if not self.parent.fileIsFixed:
    ## if varGroup not in ['fx','fixed']:
      ok = True
      self.test( 'time' in list(da.keys()), 'Time dimension not found' , abort=True, part=True )
      if self.pcfg.varTables=='CMIP':
        if not self.isInsta:
          ok &= self.test(  da['time'].get( 'bounds', 'xxx' ) == 'time_bnds', 'Required bounds attribute not present or not correct value', part=True )

## is time zone designator needed?
        tunits = da['time'].get( 'units', 'xxx' )
        if self.project  == 'CORDEX':
          ok &= self.test( tunits in ["days since 1949-12-01 00:00:00Z", "days since 1949-12-01 00:00:00", "days since 1949-12-01"],
               'Time units [%s] attribute not set correctly to "days since 1949-12-01 00:00:00Z"' % tunits, part=True )
        else:
          ok &= self.test( tunits[:10] == "days since", 'time units [%s] attribute not set correctly to "days since ....."' % tunits, part=True )

        ok &= self.test(  'calendar' in da['time'], 'Time: required attribute calendar missing', part=True )

        ok &= self.test( da['time']['_type'] in ["float64","double"], 'Time: data type not float64 [%s]' % da['time']['_type'], part=True )
       
        if ok:
          self.log_pass()
        self.calendar = da['time'].get( 'calendar', 'None' )

        if self.project  == 'CMIP5':
          pass
          ##print da['time']['_data'][0], da['time']['_data'][-1],self.parent.fnTimeTuples
    self.completed = True

  def do_check(self):
    varName = self.var
    varGroup = self.varGroup
    da = self.da
    va = self.va
    isInsta = self.isInsta
    self.errorCount = 0
    self.completed = False


    self.checkId = ('002','pressure_levels')
    if varName in self.plevRequired:
      ok = True
      self.test( 'plev' in list(va.keys()), 'plev coordinate not found %s' % str(list(va.keys())), abort=True, part=True )

      ok &= self.test( int( va['plev']['_data'][0] ) == self.plevValues[varName],  \
                  'plev value [%s] does not match required [%s]' % (va['plev']['_data'],self.plevValues[varName] ), part=True )
      
      plevAtDict = {'standard_name':"air_pressure", \
                    'long_name':"pressure", \
                    'units':"Pa", \
                    'positive':"down", \
                    'axis':"Z" }

      if varName in ['clh','clm','cll']:
        plevAtDict['bounds']= "plev_bnds"

      for k in list(plevAtDict.keys()):
        ok &= self.test( va['plev'].get( k, None ) == plevAtDict[k], 
                     'plev attribute %s absent or wrong value (should be %s)' % (k,plevAtDict[k]), part=True )

      if varName in ['clh','clm','cll']:
         self.test( "plev_bnds" in list(va.keys()), 'plev_bnds variable not found %s' % str(list(va.keys())), abort=True, part=True )
         mm = []
         for k in list(plevAtDict.keys()):
            if k != 'bounds' and k in list(va['plev_bnds'].keys()):
               if va['plev_bnds'][k] != va['plev'][k]:
                 mm.append(k)
         ok &= self.test( len(mm) == 0, 'Attributes of plev_bnds do not match those of plev: %s' % str(mm), part=True )

         bndsVals = {'clh':[44000, 0], 'clm':[68000, 44000], 'cll':[100000, 68000] }
         res = self.test( len( va['plev_bnds']['_data'] ) == 2, 'plev_bnds array is of wrong length', part=True )
         ok &= res
         if res:
            kk = 0
            for i in [0,1]:
               if int(va['plev_bnds']['_data'][i]) != bndsVals[varName][i]:
                  kk+=1
            ok &= self.test( kk == 0, 'plev_bnds values not correct: should be %s' % str(bndsVals[varName]), part=True )

      if ok:
        self.log_pass()

    self.checkId = ('003','height_levels')
    hreq = varName in self.heightRequired
    if self.parent.experimental:
      print('utils_c4: ', varName, self.vocabs['variable'].varcons[varGroup][varName].get( '_dimension',[]))
      hreq = "height2m" in self.vocabs['variable'].varcons[varGroup][varName].get( '_dimension',[])
      if hreq:
        print('testing height, var=%s' % varName)
    if hreq:
      heightAtDict = {'long_name':"height", 'standard_name':"height", 'units':"m", 'positive':"up", 'axis':"Z" }
      ok = True
      ok &= self.test( 'height' in list(va.keys()), 'height coordinate not found %s' % str(list(va.keys())), abort=True, part=True )
      ##ok &= self.test( abs( va['height']['_data'] - self.heightValues[varName]) < 0.001, \
                ##'height value [%s] does not match required [%s]' % (va['height']['_data'],self.heightValues[varName] ), part=True )

      ok1 = self.test( len( va['height']['_data'] ) == 1, 'More height values (%s) than expected (1)' % (len( va['height']['_data'])), part=True )
      if ok1:
        r = self.heightRange[varName]
        ok1 &= self.test( r[0] <= va['height']['_data'][0] <= r[1], \
                'height value [%s] not in specified range [%s]' % (va['height']['_data'], (self.heightRange[varName] ) ), part=True )

      ok &= ok1
      
      for k in list(heightAtDict.keys()):
        val =  va['height'].get( k, "none" )
        if not self.test( val == heightAtDict[k], \
                         'height attribute %s absent or wrong value (should be %s)' % (k,heightAtDict[k]), part=True ):
          self.parent.amapListDraft.append( '@var=%s;%s=%s|%s=%s' % ('height',k,val,k,heightAtDict[k]) )
          ok = False

      if ok:
        self.log_pass()

    self.completed = True

class checkGrids(CheckBase):

  def init(self):
    self.id = 'C4.004'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.do_check_rp,self.do_check_intd)

  def check(self,varName, domain, da, va):
    self.errorCount = 0
    assert type(varName) in [type('x'),type('x')], '1st argument to "check" method of checkGrids shound be a string variable name (not %s)' % type(varName)
    self.var = varName
    self.domain = domain
    self.da = da
    self.va = va

    self.runChecks()
    ##for c in self.checks:
      ##c()
    ##self.do_check_rp()
    ##self.do_check_intd()

  def do_check_rp(self):
    varName = self.var
    domain = self.domain
    da = self.da
    va = self.va
    if va[varName].get( 'grid_mapping', None ) == "rotated_pole":
      self.checkId = ('001','grid_mapping')
      atDict = { 'grid_mapping_name':'rotated_latitude_longitude' }
      atDict['grid_north_pole_latitude'] = self.pcfg.rotatedPoleGrids[domain]['grid_np_lat']
      if self.pcfg.rotatedPoleGrids[domain]['grid_np_lon'] != 'N/A':
        atDict['grid_north_pole_longitude'] = self.pcfg.rotatedPoleGrids[domain]['grid_np_lon']

      self.checkId = ('002','rotated_latlon_attributes')
      self.test( 'rlat' in list(da.keys()) and 'rlon' in list(da.keys()), 'rlat and rlon not found (required for grid_mapping = rotated_pole )', abort=True, part=True )

      atDict = {'rlat':{'long_name':"rotated latitude", 'standard_name':"grid_latitude", 'units':"degrees", 'axis':"Y", '_type':'float64'},
                'rlon':{'long_name':"rotated longitude", 'standard_name':"grid_longitude", 'units':"degrees", 'axis':"X", '_type':'float64'} }
      mm = []
      for k in ['rlat','rlon']:
        for k2 in list(atDict[k].keys()):
          if atDict[k][k2] != da[k].get(k2, None ):
            mm.append( (k,k2) )
            record = '#@ax=%s;%s=%s|%s=%s <uncomment if correct>' % (k,k2,da[k].get(k2, '__missing__'),k2,atDict[k][k2]   )
            self.parent.amapListDraft.append( record )
      self.test( len(mm) == 0, 'Required attributes of grid coordinate arrays not correct: %s' % str(mm) )

      self.checkId = ('003','rotated_latlon_domain')
      ok = True
      for k in ['rlat','rlon']:
        res = len(da[k]['_data']) == self.pcfg.rotatedPoleGrids[domain][ {'rlat':'nlat','rlon':'nlon' }[k] ]
        if not res:
          self.test( res, 'Size of %s dimension does not match specification (%s,%s)' % (k,a,b), part=True  )
          ok = False

      a = ( da['rlat']['_data'][0], da['rlat']['_data'][-1], da['rlon']['_data'][0], da['rlon']['_data'][-1] )
      b = [self.pcfg.rotatedPoleGrids[domain][x] for x in ['s','n','w','e']]
      mm = []
      for i in range(4):
        if abs(a[i] - b[i]) > self.pcfg.gridSpecTol:
          mm.append( (a[i],b[i]) )

      ok &= self.test( len(mm) == 0, 'Domain boundaries for rotated pole grid do not match %s within tolerance (%s)' % (str(mm),self.pcfg.gridSpecTol), part=True )

      for k in ['rlat','rlon']:
        ok &= self.test( cs.check( da[k]['_data'] ), '%s values not evenly spaced -- min/max delta = %s, %s' % (k,cs.dmn,cs.dmx), part=True )

      if ok:
        self.log_pass()

  def do_check_intd(self):
    varName = self.var
    domain = self.domain
    da = self.da
    va = self.va
    if domain[-1] == 'i':
      self.checkId = ('004','regular_grid_attributes')
      self.test( 'lat' in list(da.keys()) and 'lon' in list(da.keys()), 'lat and lon not found (required for interpolated data)', abort=True, part=True )

      atDict = {'lat':{'long_name':"latitude", 'standard_name':"latitude", 'units':"degrees_north", '_type':'float64'},
                'lon':{'long_name':"longitude", 'standard_name':"longitude", 'units':"degrees_east", '_type':'float64'} }
      mm = []
      for k in ['lat','lon']:
        for k2 in list(atDict[k].keys()):
          if atDict[k][k2] != da[k].get(k2, None ):
            mm.append( (k,k2) )
            record = '#@ax=%s;%s=%s|%s=%s <uncomment if correct>' % (k,k2,da[k].get(k2, '__missing__'),k2,atDict[k][k2]   )
            self.parent.amapListDraft.append( record )

      self.test( len(mm) == 0,  'Required attributes of grid coordinate arrays not correct: %s' % str(mm), part=True )

      ok = True
      self.checkId = ('005','regular_grid_domain')
      for k in ['lat','lon']:
        res = len(da[k]['_data']) >= self.pcfg.interpolatedGrids[domain][ {'lat':'nlat','lon':'nlon' }[k] ]
        if not res:
          a,b =  len(da[k]['_data']), self.pcfg.interpolatedGrids[domain][ {'lat':'nlat','lon':'nlon' }[k] ]
          self.test( res, 'Size of %s dimension does not match specification (%s,%s)' % (k,a,b), part=True )
          ok = False

      a = ( da['lat']['_data'][0], da['lat']['_data'][-1], da['lon']['_data'][0], da['lon']['_data'][-1] )
      b = [self.pcfg.interpolatedGrids[domain][x] for x in ['s','n','w','e']]
      rs = self.pcfg.interpolatedGrids[domain]['res']
      c = [-rs,rs,-rs,rs]
      mm = []
      for i in range(4):
        if a[i] != b[i]:
          x = (a[i]-b[i])/c[i]
          if x < 0 or abs( x - int(x) ) > 0.001:
             skipThis = False
             if self.project  == 'CORDEX':
               if domain[:3] == 'ANT':
                 if i == 2 and abs( a[i] - 0.25 ) < 0.001:
                    skipThis = True
                 elif i == 3 and abs( a[i] - 359.75 ) < 0.001:
                    skipThis = True
             if not skipThis:
               mm.append( (a[i],b[i]) )

      ok &= self.test( len(mm) == 0, 'Interpolated grid boundary error: File %s; Req. %s' % (str(a),str(b)), part=True )

      for k in ['lat','lon']:
        ok &= self.test( cs.check( da[k]['_data'] ), '%s values not evenly spaced -- min/max delta = %s, %s' % (k,cs.dmn,cs.dmx), part=True )
      if ok:
        self.log_pass()

class checkByVar(CheckBase):
  """Run some checks on groups of files with a common variable. Checks for continuity of time in group"""

  def init(self,fileNameSeparator='_'):
    self.id = 'C5.001'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.checkTrange,)
    ## empty for ccmi2022 ############
    ##self.checks = tuple()
    self.fnsep = fileNameSeparator

  def setLogDict( self,fLogDict ):
    self.fLogDict = fLogDict

  def impt(self,flist):
    """Scan a list of files and identify groups which a common variable and extract time ranges into a dictionary of lists, keyed on group identifiers.
     :param flist: List of file names.

 This routine has rather obscure nested logical tests used to identify the group to which a file belongs. The complexity arises from the fact that the identification of the files that should form a continuous time series from the file names alone is not a standardised feature of the file names."""
    ee = {}
    elist = []
    for f in flist:
      fn = f.split( '/' )[-1]
      fnParts = fn[:-3].split( self.fnsep )
      
      try:
        if self.pcfg.freqIndex is not None:
          if self.pcfg.freqIndex < len( fnParts ):
              freq = fnParts[self.pcfg.freqIndex]
          else:
              print( 'ERROR: freqIndex=%s, fnParts=%s' % (self.pcfg.freqIndex, fnParts) )
              raise
        else:
          freq = None

        group = fnParts[ self.pcfg.groupIndex ]

        if self.parent.fileIsFixed:
          trange = None
        else:
          trange = fnParts[-1].split( '-' )
        var = fnParts[self.pcfg.varIndex]
        thisKey = '.'.join( fnParts[:-1] )
####        print (var, thisKey )
        if group not in list(ee.keys()):
          ee[group] = {}
        if thisKey not in list(ee[group].keys()):
          ee[group][thisKey] = []
        ee[group][thisKey].append( (f,fn,group,trange) )
      except:
        print('Cannot parse file name: %s' % (f)) 
        elist.append(f)
## this ee entry is not used, except in bookkeeping check below. 
## parsing of file name is repeated later, and a error log entry is created at that stage -- this could be improved.
## in order to improve, need to clarify flow of program: the list here is used to provide preliminary info before log files etc are set up.
        group = '__error__'
        thisKey = fn
        if group not in list(ee.keys()):
          ee[group] = {}
        if thisKey not in list(ee[group].keys()):
          ee[group][thisKey] = []
        ee[group][thisKey].append( (f,fn,group) )
        raise

    nn = len(flist)
    n2 = 0
    for k in list(ee.keys()):
      for k2 in list(ee[k].keys()):
        n2 += len( ee[k][k2] )

    assert nn==n2, 'some file lost!!!!!!'
    if len(elist) == 0:
      self.info =  '%s %s, %s' % (nn, maybe_plural("file", nn), str(list(ee.keys())))
    else:
      self.info =  '%s %s, %s frequencies, severe errors in file names: %s' % (nn, maybe_plural("file", nn), len(list(ee.keys())), len(elist))
      for e in elist:
        self.info += '\n%s' % e
    self.ee = ee

  def check(self, recorder=None,calendar='None',norun=False):
    self.errorCount = 0
    self.recorder=recorder
    self.calendar=calendar

    if calendar == '360_day':
      self.enddec = 30
    else:
      self.enddec = 31
    mm = { 'enddec':self.enddec }
    self.pats = {'mon':('(?P<d>[0-9]{3})101','(?P<e>[0-9]{3})012'), \
            'sem':('(?P<d>[0-9]{3})(012|101)','(?P<e>[0-9]{3})(011|010)'), \
            'day':('(?P<d>[0-9]{3}[16])0101','(?P<e>[0-9]{3}[50])12%(enddec)s' % mm), \
            'subd':('(?P<d>[0-9]{4})0101(?P<h1>[0-9]{2})(?P<mm>[30]0){0,1}$', '(?P<e>[0-9]{4})12%(enddec)s(?P<h2>[0-9]{2})([30]0){0,1}$' % mm ), \
            'subd2':('(?P<d>[0-9]{4})0101(?P<h1>[0-9]{2})', '(?P<e>[0-9]{4})010100' ) }

    if not norun:
      self.runChecks()

  def checkTrange(self):
    """Manage time range checks: loop over groups of files identified by :meth:`impt`"""
    keys = list(self.ee.keys())
    keys.sort()
    for k in keys:
      if k not in ['fx','fixed']:
        keys2 = list(self.ee[k].keys())
        keys2.sort()
        for k2 in keys2:
          self.checkThisTrange( self.ee[k][k2], k )

  def checkThisTrange( self, tt, group):
    """Check consistency across a list of time ranges"""

    if group in ['1hr','3hr','6hr']:
       kg = 'subd'
    else:
       kg = group
    if kg not in self.pats:
        print ('WORKFLOW ERROR 001.001: kg=%s, keys=%s' % (kg,sorted( list( self.pats.keys() ) ) )) 
    ps = self.pats[kg]
    rere = (re.compile( ps[0] ), re.compile( ps[1] ) )

    n = len(tt)
    self.checkId = ('001','filename_timerange_value')
    for j in range(n):
      if self.monitor is not None:
         nofh0 = self.monitor.get_open_fds()
      t = tt[j]
      fn = t[1]
      isFirst = j == 0
      isLast = j == n-1
      lok = True
      for i in [0,1]:
        if not (i==0 and isFirst or i==1 and isLast):
          x = rere[i].match( t[3][i] )
          lok &= self.test( x is not None, 'Cannot match time range %s: %s [%s/%s]' % (i,fn,j,n), part=True, appendLogfile=(self.fLogDict.get(fn,None),fn) )
        if not lok:
          if self.recorder is not None:
            self.recorder.modify( t[1], 'ERROR: time range' )
      if self.monitor is not None:
         nofh9 = self.monitor.get_open_fds()
         if nofh9 > nofh0:
           print('Open file handles: %s --- %s [%s]' % (nofh0, nofh9, j ))


### http://stackoverflow.com/questions/2023608/check-what-files-are-open-in-python
class SysMonitor(object):

  def __init__(self):
    self.fhCountMax = 0

  def get_open_fds(self):
    '''
    return the number of open file descriptors for current process
    .. warning: will only work on UNIX-like os-es.
    '''
    import subprocess
    import os

    pid = os.getpid()
    self.procs = subprocess.check_output( 
        [ "lsof", '-w', '-Ff', "-p", str( pid ) ] )

    ##print (type(self.procs) )
    ##for  s in str(self.procs).split( '\n' ):
        ##print ('P3.001: ',s)
        

    self.ps = [s for s in str(self.procs).split( '\n' ) if s and s[ 0 ] == 'f' and s[1: ].isdigit()]
    self.fhCountMax = max( self.fhCountMax, len(self.ps) )
    return len( self.ps )

def maybe_plural(word, n):
    "Return ``word`` if n is 1, and plural of ``word`` if n is not."
    if n == 1:
        return word
    return "%ss" % word
