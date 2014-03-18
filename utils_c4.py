
import string, re, os, sys, traceback

from fcc_utils import mipTableScan

class reportSection:

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

class abortChecks(Exception):
  pass
class loggedException(Exception):
  pass
class baseException(Exception):
 
  def __init__(self,msg):
    self.msg = 'utils_c4:: %s' % msg

  def __str__(self):
        return unicode(self).encode('utf-8')

  def __unicode__(self):
        return self.msg % tuple([force_unicode(p, errors='replace')
                                 for p in self.params])
class checkSeq:
  def __init__(self):
    pass

  def check(self,x):
    d = map( lambda i: x[i+1] - x[i], range(len(x)-1) )
    self.delt = sum(d)/len(d)
    self.dmx = max(d)
    self.dmn = min(d)
    return self.dmx - self.dmn < abs(self.delt)*1.e-4

cs = checkSeq()

class checkBase:

  def  __init__(self,cls="CORDEX",reportPass=True,parent=None,monitor=None):
    self.cls = cls
    self.project = cls
    self.abortMessageCount = parent.abortMessageCount
    self.monitor = monitor
    ## check done earlier
    ## assert cls in ['CORDEX','SPECS'],'This version of the checker only supports CORDEX, SPECS'
    self.re_isInt = re.compile( '[0-9]+' )
    self.errorCount = 0
    self.passCount = 0
    self.missingValue = 1.e20
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
    self.messageCount = 0
    self.init()

  def isInt(self,x):
    return self.re_isInt.match( x ) != None

  def logMessage(self, msg, error=False ):
    self.messageCount += 1
    assert self.abortMessageCount < 0 or self.abortMessageCount > self.messageCount, 'Raising error [TESTX01], perhaps for testing'
    if self.parent != None and self.parent.log != None:
       if error:
         self.parent.log.error( msg )
       else:
         self.parent.log.info( msg )
    else:
       print msg

    doThis = True
    if self.appendLogfile[0] != None and doThis:
      if self.monitor != None:
         nofh0 = self.monitor.get_open_fds()
      xlog = self.c4i.getFileLog( self.appendLogfile[1], flf=self.appendLogfile[0] )
      if error:
         xlog.error( msg )
      else:
         xlog.info( msg )
      self.c4i.closeFileLog()
      if self.monitor != None:
         nofh9 = self.monitor.get_open_fds()
         if nofh9 > nofh0:
           print 'Leaking file handles [1]: %s --- %s' % (nofh0, nofh9)

  def log_exception( self, msg):
    if self.parent != None and self.parent.log != None:
        self.parent.log.error("Exception has occured" ,exc_info=1)
    else:
        traceback.print_exc(file=sys.stdout)

  def log_error( self, msg ):
    self.lastError = msg
    self.errorCount += 1
    self.logMessage( '%s.%s: FAILED:: %s' % (self.id,self.checkId,msg), error=True )

  def log_pass( self ):
    self.passCount = True
    if self.reportPass:
      self.logMessage(  '%s.%s: OK' % (self.id,self.checkId) )

  def log_abort( self ):
    self.completed = False
    self.logMessage(   '%s.%s: ABORTED:: Errors too severe to complete further checks in this module' % (self.id,'xxx') )
    raise abortChecks

  def status(self):
    return '%s.%s' % (self.id,self.checkId)

  def test(self,res,msg,abort=False,part=False,appendLogfile=(None,None)):
    self.appendLogfile = appendLogfile
    if res:
      if not part:
         self.log_pass()
    else:
      self.log_error(msg)
      if abort:
        self.log_abort()
    return res

  def runChecks(self):

    try:
      for c in self.checks:
        c()  # run check
      self.completed = True
    except abortChecks:
      ## error logging done before raising this exception
      return
    except:
      self.log_exception( 'Exception caught by runChecks' )
      raise loggedException
      ##traceback.print_exc(file=open("errlog.txt","a"))
      ##logger.error("Exception has occured" ,exc_info=1)
    
class checkFileName(checkBase):

  def init(self):
    self.id = 'C4.001'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.do_check_fn,)
####

  def check(self,fn):
    self.errorCount = 0
    assert type(fn) in [type('x'),type(u'x')], '1st argument to "check" method of checkGrids shound be a string variable name (not %s)' % type(fn)
    self.fn = fn

    self.runChecks()
###
  def do_check_fn(self):
    fn = self.fn
    self.errorCount = 0
    self.completed = False

## check basic parsing of file name
    self.checkId = '001'
    self.test( fn[-3:] == '.nc', 'File name ending ".nc" expected', abort=True, part=True )
    bits = string.split( fn[:-3], '_' )
    self.fnParts = bits[:]

    if self.pcfg.domainIndex != None:
      self.domain = self.fnParts[self.pcfg.domainIndex]
    else:
      self.domain = None
    ##if self.cls == 'CORDEX':
      ##self.fnPartsOkLen = [8,9]
      ##self.fnPartsOkFixedLen = [8,]
      ##self.fnPartsOkUnfixedLen = [9,]
      ##checkTrangeLen = True
    ##elif self.cls == 'SPECS':
      ##self.fnPartsOkLen = [6,7]
      ##self.fnPartsOkFixedLen = [6,]
      ##self.fnPartsOkUnfixedLen = [7,]
      ##checkTrangeLen = False

    self.test( len(bits) in self.pcfg.fnPartsOkLen, 'File name not parsed in %s elements [%s]' % (str(self.pcfg.fnPartsOkLen),str(bits)), abort=True )

    if self.pcfg.freqIndex != None:
      self.freq = self.fnParts[self.pcfg.freqIndex]
    else:
      self.freq = None

    if self.pcfg.groupIndex != None:
      self.group = self.fnParts[self.pcfg.groupIndex]
    else:
      self.group = None

    ##if self.cls == 'CORDEX':
      ##self.freq = self.fnParts[7]
    ##elif self.cls == 'SPECS':
      ##self.freq = self.fnParts[1]

    self.var = self.fnParts[0]

    self.isFixed = self.freq == 'fx'

    self.checkId = '002'
    if not self.isFixed:

## test time segment
      bits = string.split( self.fnParts[-1], '-' )
      self.test( len(bits) == 2, 'File time segment [%s] will not parse into 2 elements' % (self.fnParts[-1] ), abort=True, part=True )

      self.test(  len(bits[0]) == len(bits[1]), 'Start and end time specified in file name [%s] of unequal length' % (self.fnParts[-1] ), abort=True, part=True  )

      for b in bits:
        self.test( self.isInt(b), 'Time segment in filename [%s] contains non integer characters' % (self.fnParts[-1] ),  abort=True, part=True  )
      self.log_pass()
      self.fnTimeParts = bits[:]

    self.checkId = '003'
    if self.isFixed:
      self.test( len(self.fnParts) in self.pcfg.fnPartsOkFixedLen, 'Number of file name elements not acceptable for fixed data' )

    self.checkId, ok = ('004',True)
    if len(self.fnParts) == 9 and self.pcfg.checkTrangeLen:
      ltr = { 'mon':6, 'sem':6, 'day':8, '3hr':[10,12], '6hr':10 }
      ok &=self.test( self.freq in ltr.keys(), 'Frequency [%s] not recognised' % self.freq, part=True )
      if ok:
        if type( ltr[self.freq] ) == type(0):
          msg = 'Length of time range parts [%s,%s] not equal to required length [%s] for frequency %s' % (self.fnTimeParts[0],self.fnTimeParts[1],ltr[self.freq],self.freq)
          ok &= self.test( len(self.fnTimeParts[0]) == ltr[self.freq], msg, part=True )
        elif type( ltr[self.freq] ) in [type([]),type( () )]:
          msg = 'Length of time range parts [%s,%s] not in acceptable list [%s] for frequency %s' % (self.fnTimeParts[0],self.fnTimeParts[1],str(ltr[self.freq]),self.freq)
          ok &= self.test( len(self.fnTimeParts[0]) in ltr[self.freq], msg, part=True )

      if ok:
        self.log_pass()
    self.completed = True

class checkGlobalAttributes(checkBase):

  def init(self):
    self.id = 'C4.002'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.do_check_ga,)

  def check(self,globalAts, varAts,varName,varGroup, vocabs, fnParts):
    self.errorCount = 0
    assert type(varName) in [type('x'),type(u'x')], '1st argument to "check" method of checkGrids shound be a string variable name (not %s)' % type(varName)
    self.var = varName
    self.globalAts = globalAts
    self.varAts = varAts
    self.varGroup = varGroup
    self.vocabs = vocabs
    self.fnParts = fnParts
    self.runChecks()

  def getDrs( self ):
    assert self.completed, 'method getDrs should not be called if checks have not been completed successfully'
    ee = {}
    self.globalAts['forecast_reference_time'] = 'dummy'
    for k in self.drsMappings:
      if self.drsMappings[k] == '@var':
        ee[k] = self.var
      elif self.drsMappings[k] == '@ensemble':
        ee[k] = "r%si%sp%s" % (self.globalAts["realization"],self.globalAts["initialization_method"],self.globalAts["physics_version"])
      else:
        ee[k] = self.globalAts[ self.drsMappings[k] ]

    for k in ['creation_date','tracking_id']:
      if k in self.globalAts.keys():
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
    self.checkId = '001'
    m = []
    for k in self.requiredGlobalAttributes:
      if not globalAts.has_key(k):
         m.append(k)

    gaerr = not self.test( len(m)  == 0, 'Required global attributes missing: %s' % str(m) )

    self.checkId = '002'

    self.test( varAts.has_key( varName ), 'Expected variable [%s] not present' % varName, abort=True, part=True )
    msg = 'Variable %s not in table %s' % (varName,varGroup)
    self.test( vocabs['variable'].isInTable( varName, varGroup ), msg, abort=True, part=True )

    self.checkId = '003'

    self.test( varAts[varName]['_type'] == "float32", 'Variable [%s] not of type float' % varName )

    self.checkId = '004'
    m = []
    reqAts = self.requiredVarAttributes[:]
    if varGroup != 'fx' and self.pcfg.project in ['CORDEX']:
      reqAts.append( 'cell_methods' )
    for k in reqAts + vocabs['variable'].lists(varName, 'addRequiredAttributes'):
      if not varAts[varName].has_key(k):
         m.append(k)
    vaerr = not self.test( len(m)  == 0, 'Required variable attributes missing: %s' % str(m) )

    ##if vaerr or gaerr:
      ##self.log_abort()

## need to insert a check that variable is present
    self.checkId = '005'
    ok = True
    if ( varAts[varName].get( 'missing_value', None ) != None ) or varAts[varName].has_key( '_FillValue' ):
      tval = ( varAts[varName].get( 'missing_value', None ) != None ) and varAts[varName].has_key( '_FillValue' )
      ok &= self.test( tval, 'missing_value and _FillValue must both be present if one is [%s]' % varName )
      if varAts[varName].has_key( 'missing_value' ):
         msg = 'Variable [%s] has incorrect missing_value attribute' % varName
         ok &= self.test( varAts[varName]['missing_value'] == self.missingValue, msg, part=True )
      if varAts[varName].has_key( '_FillValue' ):
         msg = 'Variable [%s] has incorrect _FillValue attribute' % varName
         ok &= self.test( varAts[varName]['_FillValue'] == self.missingValue, msg, part=True )

    mm = []
    
    contAts = ['long_name', 'standard_name', 'units']
    if varGroup != 'fx':
      contAts.append( 'cell_methods' )
    hcm = varAts[varName].has_key( "cell_methods" )
    for k in contAts + vocabs['variable'].lists(varName,'addControlledAttributes'):
      targ = varAts[varName].get( k, 'Attribute not present' )
      val = vocabs['variable'].getAttr( varName, varGroup, k )
      if k == "cell_methods":
        if val != None:
          if string.find( targ, val):
             mm.append(k)
      elif targ != val:
        mm.append( k )

    ok &= self.test( len(mm)  == 0, 'Variable [%s] has incorrect attributes: %s' % (varName, str(mm)), part=True )
    if ok:
       self.log_pass()

    if varGroup != 'fx' and hcm:
      self.isInstantaneous = string.find( varAts[varName]['cell_methods'], 'time: point' ) != -1
    else:
      self.isInstantaneous = True

    self.checkId = '006'
    m = []
    for a in self.controlledGlobalAttributes:
      if globalAts.has_key(a):
        try:
          if not vocabs[a].check( str(globalAts[a]) ):
            m.append( (a,globalAts[a],vocabs[a].note) )
        except:
          print 'failed trying to check global attribute %s' % a
          raise

    self.test( len(m)  == 0, 'Global attributes do not match constraints: %s' % str(m) )

    self.checkId = '007'
    m = []
    for i in range(len(self.globalAttributesInFn)):
       if self.globalAttributesInFn[i] != None:
         targVal = fnParts[i]
         if self.globalAttributesInFn[i][0] == "@":
           if self.globalAttributesInFn[i][1:] == "mip_id":
               thisVal = string.split( globalAts["table_id"] )[1]
           elif self.globalAttributesInFn[i][1:] == "ensemble":
               thisVal = "r%si%sp%s" % (globalAts["realization"],globalAts["initialization_method"],globalAts["physics_version"])
           elif self.globalAttributesInFn[i][1:] == "series":
               thisVal = 'series%s' % globalAts["series"]
           elif self.globalAttributesInFn[i][1:] == "experiment_family":
             thisVal = globalAts["experiment_id"][:-4]
           else:
               assert False, "Not coded to deal with this configuration: globalAttributesInFn[%s]=%s" % (i,self.globalAttributesInFn[i])
           ##print "Generated text val: %s:: %s" % (self.globalAttributesInFn[i], thisVal)
         
         else:
             thisVal = globalAts[self.globalAttributesInFn[i]]

         if thisVal != targVal:
             m.append( (i,self.globalAttributesInFn[i]) )

    self.test( len(m)  == 0,'File name segments do not match corresponding global attributes: %s' % str(m) )

    self.completed = True
       
class checkStandardDims(checkBase):

  def init(self):
    self.id = 'C4.003'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.do_check,)
    self.plevRequired = self.pcfg.plevRequired
    self.plevValues = self.pcfg.plevValues
    self.heightRequired = self.pcfg.heightRequired
    self.heightValues = self.pcfg.heightValues
    self.heightRange = self.pcfg.heightRange

  def check(self,varName,varGroup, da, va, isInsta):
    self.errorCount = 0
    assert type(varName) in [type('x'),type(u'x')], '1st argument to "check" method of checkGrids shound be a string variable name (not %s)' % type(varName)
    self.var = varName
    self.varGroup = varGroup
    self.da = da
    self.va = va
    self.isInsta = isInsta
    self.runChecks()

  def do_check(self):
    varName = self.var
    varGroup = self.varGroup
    da = self.da
    va = self.va
    isInsta = self.isInsta

    self.errorCount = 0
    self.completed = False
    self.checkId = '001'
    if varGroup != 'fx':
      ok = True
      self.test( 'time' in da.keys(), 'Time dimension not found' , abort=True, part=True )
      if not isInsta:
        ok &= self.test(  da['time'].get( 'bounds', 'xxx' ) == 'time_bnds', 'Required bounds attribute not present or not correct value', part=True )

## is time zone designator needed?
      tunits = da['time'].get( 'units', 'xxx' )
      if self.project  == 'CORDEX':
        ok &= self.test( tunits in ["days since 1949-12-01 00:00:00Z", "days since 1949-12-01 00:00:00", "days since 1949-12-01"],
               'Time units [%s] attribute not set correctly to "days since 1949-12-01 00:00:00Z"' % tunits, part=True )
      else:
        ok &= self.test( tunits[:10] == "days since", 'time units [%s] attribute not set correctly to "days since ....."' % tunits, part=True )

      ok &= self.test(  da['time'].has_key( 'calendar' ), 'Time: required attribute calendar missing', part=True )

      ok &= self.test( da['time']['_type'] == "float64", 'Time: data type not float64', part=True )
       
      if ok:
        self.log_pass()
      self.calendar = da['time'].get( 'calendar', 'None' )
    else:
      self.calendar = 'None'
    self.checkId = '002'
    if varName in self.plevRequired:
      ok = True
      self.test( 'plev' in va.keys(), 'plev coordinate not found %s' % str(va.keys()), abort=True, part=True )

      ok &= self.test( int( va['plev']['_data'] ) == self.plevValues[varName],  \
                  'plev value [%s] does not match required [%s]' % (va['plev']['_data'],self.plevValues[varName] ), part=True )
      
      plevAtDict = {'standard_name':"air_pressure", \
                    'long_name':"pressure", \
                    'units':"Pa", \
                    'positive':"down", \
                    'axis':"Z" }

      if varName in ['clh','clm','cll']:
        plevAtDict['bounds']= "plev_bnds"

      for k in plevAtDict.keys():
        ok &= self.test( va['plev'].get( k, None ) == plevAtDict[k], 
                     'plev attribute %s absent or wrong value (should be %s)' % (k,plevAtDict[k]), part=True )

      if varName in ['clh','clm','cll']:
         self.test( "plev_bnds" in va.keys(), 'plev_bnds variable not found %s' % str(va.keys()), abort=True, part=True )
         mm = []
         for k in plevAtDict.keys():
            if k != 'bounds' and k in va['plev_bnds'].keys():
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

    self.checkId = '003'
    if varName in self.heightRequired:
      heightAtDict = {'long_name':"height", 'standard_name':"height", 'units':"m", 'positive':"up", 'axis':"Z" }
      ok = True
      ok &= self.test( 'height' in va.keys(), 'height coordinate not found %s' % str(va.keys()), abort=True, part=True )
      ##ok &= self.test( abs( va['height']['_data'] - self.heightValues[varName]) < 0.001, \
                ##'height value [%s] does not match required [%s]' % (va['height']['_data'],self.heightValues[varName] ), part=True )

      r = self.heightRange[varName]
      ok &= self.test( r[0] <= va['height']['_data'] <= r[1], \
                'height value [%s] not in specified range [%s]' % (va['height']['_data'], (self.heightRange[varName] ) ), part=True )
      
      for k in heightAtDict.keys():
        ok &= self.test( va['height'].get( k, None ) == heightAtDict[k], \
                         'height attribute %s absent or wrong value (should be %s)' % (k,heightAtDict[k]), part=True )

      if ok:
        self.log_pass()

    self.completed = True

class checkGrids(checkBase):

  def init(self):
    self.id = 'C4.004'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.do_check_rp,self.do_check_intd)

  def check(self,varName, domain, da, va):
    self.errorCount = 0
    assert type(varName) in [type('x'),type(u'x')], '1st argument to "check" method of checkGrids shound be a string variable name (not %s)' % type(varName)
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
      self.checkId = '001'
      atDict = { 'grid_mapping_name':'rotated_latitude_longitude' }
      atDict['grid_north_pole_latitude'] = self.pcfg.rotatedPoleGrids[domain]['grid_np_lat']
      if self.pcfg.rotatedPoleGrids[domain]['grid_np_lon'] != 'N/A':
        atDict['grid_north_pole_longitude'] = self.pcfg.rotatedPoleGrids[domain]['grid_np_lon']

      self.checkId = '002'
      self.test( 'rlat' in da.keys() and 'rlon' in da.keys(), 'rlat and rlon not found (required for grid_mapping = rotated_pole )', abort=True, part=True )

      atDict = {'rlat':{'long_name':"rotated latitude", 'standard_name':"grid_latitude", 'units':"degrees", 'axis':"Y", '_type':'float64'},
                'rlon':{'long_name':"rotated longitude", 'standard_name':"grid_longitude", 'units':"degrees", 'axis':"X", '_type':'float64'} }
      mm = []
      for k in ['rlat','rlon']:
        for k2 in atDict[k].keys():
          if atDict[k][k2] != da[k].get(k2, None ):
            mm.append( (k,k2) )
      self.test( len(mm) == 0, 'Required attributes of grid coordinate arrays not correct: %s' % str(mm) )

      self.checkId = '003'
      ok = True
      for k in ['rlat','rlon']:
        res = len(da[k]['_data']) == self.pcfg.rotatedPoleGrids[domain][ {'rlat':'nlat','rlon':'nlon' }[k] ]
        if not res:
          self.test( res, 'Size of %s dimension does not match specification (%s,%s)' % (k,a,b), part=True  )
          ok = False

      a = ( da['rlat']['_data'][0], da['rlat']['_data'][-1], da['rlon']['_data'][0], da['rlon']['_data'][-1] )
      b = map( lambda x: self.pcfg.rotatedPoleGrids[domain][x], ['s','n','w','e'] )
      mm = []
      for i in range(4):
        if a[i] != b[i]:
          mm.append( (a[i],b[i]) )

      ok &= self.test( len(mm) == 0, 'Domain boundaries for rotated pole grid do not match %s' % str(mm), part=True )

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
      self.checkId = '002'
      self.test( 'lat' in da.keys() and 'lon' in da.keys(), 'lat and lon not found (required for interpolated data)', abort=True, part=True )

      atDict = {'lat':{'long_name':"latitude", 'standard_name':"latitude", 'units':"degrees_north", '_type':'float64'},
                'lon':{'long_name':"longitude", 'standard_name':"longitude", 'units':"degrees_east", '_type':'float64'} }
      mm = []
      for k in ['lat','lon']:
        for k2 in atDict[k].keys():
          if atDict[k][k2] != da[k].get(k2, None ):
            mm.append( (k,k2) )

      self.test( len(mm) == 0,  'Required attributes of grid coordinate arrays not correct: %s' % str(mm), part=True )

      ok = True
      for k in ['lat','lon']:
        res = len(da[k]['_data']) >= self.pcfg.interpolatedGrids[domain][ {'lat':'nlat','lon':'nlon' }[k] ]
        if not res:
          a,b =  len(da[k]['_data']), self.pcfg.interpolatedGrids[domain][ {'lat':'nlat','lon':'nlon' }[k] ]
          self.test( res, 'Size of %s dimension does not match specification (%s,%s)' % (k,a,b), part=True )
          ok = False

      a = ( da['lat']['_data'][0], da['lat']['_data'][-1], da['lon']['_data'][0], da['lon']['_data'][-1] )
      b = map( lambda x: self.pcfg.interpolatedGrids[domain][x], ['s','n','w','e'] )
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

class mipVocab:

  def __init__(self,pcfg,dummy=False):
     project = pcfg.project
     if dummy:
       self.pcfg = pcfg
       return self.dummyMipTable()
     ##assert project in ['CORDEX','SPECS'],'Project %s not recognised' % project
     ##if project == 'CORDEX':
       ##dir = 'cordex_vocabs/mip/'
       ##tl = ['fx','sem','mon','day','6h','3h']
       ##vgmap = {'6h':'6hr','3h':'3hr'}
       ##fnpat = 'CORDEX_%s'
     ##elif project == 'SPECS':
       ##dir = 'specs_vocabs/mip/'
       ##tl = ['fx','Omon','Amon','Lmon','OImon','day','6hrLev']
       ##vgmap = {}
       ##fnpat = 'SPECS_%s'
     dir, tl, vgmap, fnpat = pcfg.mipVocabPars
     ms = mipTableScan()
     self.varInfo = {}
     self.varcons = {}
     for f in tl:
        vg = vgmap.get( f, f )
        self.varcons[vg] = {}
        fn = fnpat % f
        ll = open( '%s%s' % (dir,fn) ).readlines()
        ee = ms.scan_table(ll,None,asDict=True)
        for v in ee.keys():
          eeee = {}
          ar = []
          ac = []
          for a in ee[v][1].keys():
            eeee[a] = ee[v][1][a]
          ##if 'positive' in eeee.keys():
            ##ar.append( 'positive' )
            ##ac.append( 'positive' )
          self.varInfo[v] = {'ar':ar, 'ac':ac }
          self.varcons[vg][v] = eeee
            
  def dummyMipTable(self):
     self.varInfo = {}
     self.varcons = {}
     ee = { 'standard_name':'sn%s', 'long_name':'n%s', 'units':'1' }
     dir, tl, vgmap, fnpat = self.pcfg.mipVocabPars
     for f in tl:
        vg = vgmap.get( f, f )
        self.varcons[vg] = {}
        for i in range(12):
          v = 'v%s' % i
          eeee = {}
          eeee['standard_name'] = ee['standard_name'] % i
          eeee['long_name'] = ee['long_name'] % i
          eeee['cell_methods'] = 'time: point'
          eeee['units'] = ee['units']
          ar = []
          ac = []
          self.varInfo[v] = {'ar':ar, 'ac':ac }
          self.varcons[vg][v] = eeee

  def lists( self, k, k2 ):
     if k2 == 'addRequiredAttributes':
       return self.varInfo[k]['ar']
     elif k2 == 'addControlledAttributes':
       return self.varInfo[k]['ac']
     else:
       raise 'mipVocab.lists called with bad list specifier %s' % k2

  def isInTable( self, v, vg ):
    assert vg in self.varcons.keys(), '%s not found in  self.varcons.keys() [%s]' % (vg,str(self.varcons.keys()) )
    return (v in self.varcons[vg].keys())
      
  def getAttr( self, v, vg, a ):
    assert vg in self.varcons.keys(), '%s not found in  self.varcons.keys()'
    assert v in self.varcons[vg].keys(), '%s not found in self.varcons[%s].keys()' % (v,vg)
      
    return self.varcons[vg][v][a]
      
class patternControl:

  def __init__(self,tag,pattern,list=None):
    try:
      self.re_pat = re.compile( pattern )
    except:
      print "Failed to compile pattern >>%s<< (%s)" % (pattern, tag)
    self.pattern = pattern
    self.list = list

  def check(self,val):
    self.note = '-'
    m = self.re_pat.match( val )
    if self.list == None:
      self.note = "simple test"
      return m != None
    else:
      if m == None:
        self.note = "no match %s::%s" % (val,self.pattern)
        return False
      if not m.groupdict().has_key("val"):
        self.note = "no 'val' in match"
        return False
      self.note = "val=%s" % m.groupdict()["val"]
      return m.groupdict()["val"] in self.list
    
class listControl:
  def __init__(self,tag,list,split=False,splitVal=None):
    self.list = list
    self.tag = tag
    self.split = split
    self.splitVal = splitVal

  def check(self,val):
    self.note = '-'
    if len(self.list) < 4:
      self.note = str( self.list )
    else:
      self.note = str( self.list[:4] )
    if self.split:
      if self.splitVal == None:
        vs = string.split( val )
      else:
        vs = string.split( val, self.spliVal )
      return all( map( lambda x: x in self.list, vs ) )
    else:
      return val in self.list


class checkByVar(checkBase):

  def init(self):
    self.id = 'C5.001'
    self.checkId = 'unset'
    self.step = 'Initialised'
    self.checks = (self.checkTrange,)

  def setLogDict( self,fLogDict ):
    self.fLogDict = fLogDict

  def impt(self,flist):
    ee = {}
    for f in flist:
      fn = string.split(f, '/' )[-1]
      fnParts = string.split( fn[:-3], '_' )
      ##if self.cls == 'CORDEX':
        ##isFixed = fnParts[7] == 'fx'
        ##group = fnParts[7]
      ##elif self.cls == 'SPECS':
        ##isFixed = fnParts[1] == 'fx'
        ##group = fnParts[1]

      if self.pcfg.freqIndex != None:
        freq = fnParts[self.pcfg.freqIndex]
      else:
        freq = None

      isFixed = freq == 'fx'
      group = fnParts[ self.pcfg.groupIndex ]

      if isFixed:
        trange = None
      else:
        trange = string.split( fnParts[-1], '-' )
      var = fnParts[0]
      thisKey = string.join( fnParts[:-1], '.' )
      if group not in ee.keys():
        ee[group] = {}
      if thisKey not in ee[group].keys():
        ee[group][thisKey] = []
      ee[group][thisKey].append( (f,fn,group,trange) )

    nn = len(flist)
    n2 = 0
    for k in ee.keys():
      for k2 in ee[k].keys():
        n2 += len( ee[k][k2] )

    assert nn==n2, 'some file lost!!!!!!'
    self.info =  '%s files, %s frequencies' % (nn,len(ee.keys()) )
    self.ee = ee

  def check(self, recorder=None,calendar='None',norun=False):
    self.errorCount = 0
    self.recorder=recorder
    self.calendar=calendar
    if calendar == '360-day':
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
    keys = self.ee.keys()
    keys.sort()
    for k in keys:
      if k != 'fx':
        keys2 = self.ee[k].keys()
        keys2.sort()
        for k2 in keys2:
          self.checkThisTrange( self.ee[k][k2], k )

  def checkThisTrange( self, tt, group):

    if group in ['3hr','6hr']:
       kg = 'subd'
    else:
       kg = group
    ps = self.pats[kg]
    rere = (re.compile( ps[0] ), re.compile( ps[1] ) )

    n = len(tt)
    self.checkId = '001'
    for j in range(n):
      if self.monitor != None:
         nofh0 = self.monitor.get_open_fds()
      t = tt[j]
      fn = t[1]
      isFirst = j == 0
      isLast = j == n-1
      lok = True
      for i in [0,1]:
        if not (i==0 and isFirst or i==1 and isLast):
          x = rere[i].match( t[3][i] )
          lok &= self.test( x != None, 'Cannot match time range %s: %s [%s/%s]' % (i,fn,j,n), part=True, appendLogfile=(self.fLogDict.get(fn,None),fn) )
        if not lok:
          ### print 'Cannot match time range %s:' % t[1]
          if self.recorder != None:
            self.recorder.modify( t[1], 'ERROR: time range' )
      if self.monitor != None:
         nofh9 = self.monitor.get_open_fds()
         if nofh9 > nofh0:
           print 'Open file handles: %s --- %s [%s]' % (nofh0, nofh9, j )

### http://stackoverflow.com/questions/2023608/check-what-files-are-open-in-python
class sysMonitor:

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

    self.ps = filter( 
            lambda s: s and s[ 0 ] == 'f' and s[1: ].isdigit(),
            self.procs.split( '\n' ) )
    self.fhCountMax = max( self.fhCountMax, len(self.ps) )
    return len( self.ps )
