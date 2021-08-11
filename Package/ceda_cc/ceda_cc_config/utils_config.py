"""A set of classes running checks and providing utilities to support checks"""
import re, os, sys, traceback, ctypes, collections, json

class baseException(Exception):
  """Basic exception for general use in code."""

  def __init__(self,msg):
    self.msg = 'utils_c4:: %s' % msg

  def __str__(self):
        return str(self).encode('utf-8')

  def __repr__(self):
    return self.msg

  def __unicode__(self):
        return self.msg % tuple([force_unicode(p, errors='replace')
                                 for p in self.params])

class mipTableScan(object):

  def __init__(self, vats = ['standard_name','long_name','units','cell_methods'] ):
    self.vats = vats
    self.re_cmor_mip2 = re.compile( 'dimensions:(?P<dims>.*?):::' )
    self.re_vats = { }
    for v in vats:
      self.re_vats[v] = re.compile( '%s:(?P<dims>.*?):::' % v )
##
  def scan_table(self,ll,log,asDict=False,appendTo=None,lax=False,tag=None):
 
    ##lll0 = list(map( string.strip, ll ))
    lll0 = [x.strip() for x in ll]
    lll = []
    for l in lll0:
      if len(l) != 0:
        if l[0] != '!':
          lll.append(l.split('!')[0])
    sll = []
    sll.append( ['header',[]] )
    for l in lll:
      k = l.split( ':' )[0]
      if k in ['variable_entry','axis_entry']:
        sll.append( [k,[]] )
      sll[-1][1].append(l)

    eee = []
    for s in sll:
      if s[0] == 'variable_entry':
         bits = s[1][0].split(':')
         assert len(bits) == 2, 'Can not unpack: %s' % str(s[1])
         #k,var =  list(map( string.strip, string.split(s[1][0],':') ))
         k,var =  [x.strip() for x in s[1][0].split(':') ]
         aa = {'standard_name':None, 'long_name':None,'units':None,'cell_methods':None }
         ds = 'scalar'
         for l in s[1][1:]:
           bits = l.split(':')
           k = bits[0].strip()
           v = ':'.join( bits[1:] ).strip( )
           if k == 'dimensions':
             ds = v.split()
           else:
             aa[k] = v
         eee.append( (var,ds,aa,tag) )


    checkOldMethod = False
    if checkOldMethod:
      ssss = ':::'.join( lll )
      vitems = ssss.split( ':::variable_entry:' )[1:]
 
      ee = []
      for i in vitems:
        b1 = i.split( ':::')[0]
        var = b1.strip( )
        aa = {}
        for v in self.vats:
          mm = self.re_vats[v].findall(i)
          if len(mm) == 1:
             aa[v] = mm[0].strip()
          else:
             aa[v] = 'None'
 
        mm = self.re_cmor_mip2.findall( i )
        if len(mm) == 1:
          ds = mm[0].strip().split( )
        elif len(mm) == 0:
          ds = 'scalar'
        else:
          if log != None:
             log.warn(  'Mistake?? in scan_table %s' % str(mm) )
          ds = mm
          raise baseException( 'Mistake?? in scan_table %s' % str(mm) )
        ee.append( (var,ds,aa,tag) )

      for k in range(len(ee) ):
        if ee[k][0:2] == eee[k][0:2] and ee[k][2]['standard_name'] == eee[k][2]['standard_name'] and ee[k][2]['long_name'] == eee[k][2]['long_name']:
          print('OK:::', ee[k])
        else:
          print('DIFF: ',ee[k],eee[k])
      
    if not asDict:
      return tuple( eee )
    else:
      ff = {}
      for l in eee:
        ff[l[0]] = ( l[1], l[2], l[3] )
      if appendTo != None:
        for k in list(ff.keys()):
          assert 'standard_name' in ff[k][1], 'No standard name in %s:: %s' % (k,str(list(ff[k][1].keys())))
          if k in appendTo:
            if lax and  ff[k][1]['standard_name'] != appendTo[k][1]['standard_name']:
              print('ERROR[X1]: Inconsistent entry definitions %s:: %s [%s] --- %s [%s]' % (k,ff[k][1],ff[k][2], appendTo[k][1], appendTo[k][2]))
            if not lax:
              assert ff[k][1] == appendTo[k][1], 'Inconsistent entry definitions %s:: %s [%s] --- %s [%s]' % (k,ff[k][1],ff[k][2], appendTo[k][1], appendTo[k][2])
          else:
            appendTo[k] = ff[k]
        return appendTo
      else:
        return ff
##
## this class carries a logging method, and is used to carry information about datasets being parsed.
##

class mipVocab(object):

  def __init__(self,pcfg,dummy=False):
     self.pcfg = pcfg
     if dummy:
       self.dummyMipTable()
     elif pcfg.varTables=='CMIP':
       if pcfg.varTableFlavour=='json_ccmi':
         self.ingestJsonMipTables()
       else:
         self.ingestMipTables()
     elif pcfg.varTables=='FLAT':
       self.flatTable()
    
  def ingestJsonMipTables(self):
     dir, tl, vgmap, fnpat = self.pcfg.mipVocabPars
     self.varInfo = {}
     self.varcons = {}
     ##self.varcons = collections.defaultdict( dict )
     full = ['cell_measures', 'cell_methods', 'comment', 'dimensions', 'frequency', 'long_name', 'modeling_realm', 'out_name', 'positive', 'standard_name', 'type', 'units', 'valid_max', 'valid_min']
     here = ['cell_measures', 'cell_methods', 'long_name', 'standard_name', 'type', 'units']
     for vg in tl:
        if vg not in self.varcons:
          self.varcons[vg] = {}
        fn = fnpat % vg
        print ('ingestJson ... ',dir,fn)
        ee = json.load( open( '%s%s' % (dir,fn) ) )
        for var,i in ee['variable_entry'].items():
          eeee = dict()

          for kk in here:
              eeee[kk] = i[kk]
          eeee['_dimension'] = i['dimensions']

          self.varInfo[var] = {'ar':[], 'ac':[] }
          self.varcons[vg][var] = eeee

  def ingestMipTables(self):
     dir, tl, vgmap, fnpat = self.pcfg.mipVocabPars
     ms = mipTableScan()
     self.varInfo = {}
     self.varcons = {}
     ##self.varcons = collections.defaultdict( dict )
     for f in tl:
        vg = vgmap.get( f, f )
        if vg not in self.varcons:
          self.varcons[vg] = {}
        fn = fnpat % f
        ll = open( '%s%s' % (dir,fn) ).readlines()
        ee = ms.scan_table(ll,None,asDict=True)
        for v in list(ee.keys()):
## set global default: type float
          eeee = { 'type':self.pcfg.defaults.get( 'variableDataType', 'float' ) }
          eeee['_dimension'] = ee[v][0]
          ar = []
          ac = []
          for a in list(ee[v][1].keys()):
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
          eeee['type'] = 'float'
          ar = []
          ac = []
          self.varInfo[v] = {'ar':ar, 'ac':ac }
          self.varcons[vg][v] = eeee

  def flatTable(self):
     self.varInfo = {}
     self.varcons = {}
     dir, tl, vgm, fn = self.pcfg.mipVocabPars
     vg = list(vgm.keys())[0]
     ee = { 'standard_name':'sn%s', 'long_name':'n%s', 'units':'1' }
     ll = open( '%s%s' % (dir,fn) ).readlines()
     self.varcons[vg] = {}
     for l in ll:
       if l[0] != '#':
          bits = l.strip().split( '|' )
          if len(bits) == 2:
            p1,p2 = bits
          else:
            p1 = l
            p2 = None
          dt, v, sn = p1.strip().split( maxsplit=2 )
          if p2 is not None:
            bits = p2.strip().split( '=' )
            eex = { bits[0]:bits[1] }
          else:
            eex = None
          self.pcfg.fnvdict[dt] = { 'v':v, 'sn':sn, 'ex':eex }
          ar = []
          ac = []
          self.varInfo[v] = {'ar':ar, 'ac':ac }
          self.varcons[vg][v] = {'standard_name':sn, 'type':'float' }

  def lists( self, k, k2 ):
     if k2 == 'addRequiredAttributes':
       return self.varInfo[k]['ar']
     elif k2 == 'addControlledAttributes':
       return self.varInfo[k]['ac']
     else:
       raise baseException( 'mipVocab.lists called with bad list specifier %s' % k2 )

  def isInTable( self, v, vg1 ):
    vg = vg1
    if vg == 'ESA':
      vg = 'ESACCI'
   
    assert vg in list(self.varcons.keys()), '%s not found in  self.varcons.keys() [%s]' % (vg,str(list(self.varcons.keys())) )
    return (v in list(self.varcons[vg].keys()))
      
  def getAttr( self, v, vg1, a ):
    vg = vg1
    if vg == 'ESA':
      vg = 'ESACCI'
    assert vg in list(self.varcons.keys()), '%s not found in  self.varcons.keys()'
    assert v in list(self.varcons[vg].keys()), '%s not found in self.varcons[%s].keys()' % (v,vg)
      
    return self.varcons[vg][v][a]
      
class PatternControl(object):

  def __init__(self,tag,pattern,list=None,cls=None,examples=None,badExamples=None,runTest=True):
    if cls is not None:
      assert cls in ['ISO'], 'value of cls [%s] not recognised' % cls
      if cls == 'ISO':
        assert pattern in ['ISO8601 duration'], 'value of pattern [%s] for ISO constraint not recognised' % pattern
        if pattern == 'ISO8601 duration':
          thispat = '^(P([0-9]+Y){0,1}([0-9]+M){0,1}([0-9]+D){0,1}(T([0-9]+H){0,1}([0-9]+M){0,1}([0-9]+(.[0-9]+){0,1}S){0,1}){0,1})$|^(P[0-9]+W)$'
        self.re_pat = re.compile( thispat )
        self.pattern = thispat
        self.pattern_src = pattern
    else:
      try:
        self.re_pat = re.compile( pattern )
      except:
        print("Failed to compile pattern >>%s<< (%s)" % (pattern, tag))
      self.pattern = pattern
    
    self.examples = examples
    self.badExamples = badExamples
    self.list = list
    self.cls = cls

    if runTest:
      if examples is not None:
        for e in examples:
          assert self.check(e), 'Internal check failed: example %s does not fit pattern %s' % (e,self.pattern)

  def check(self,val):
    self.note = '-'
    m = self.re_pat.match( val )
    if self.list is None:
      self.note = "simple test"
      return m is not None
    else:
      if m is None:
        self.note = "no match %s::%s" % (val,self.pattern)
        return False
      if "val" not in m.groupdict():
        self.note = "no 'val' in match"
        return False
      self.note = "val=%s" % m.groupdict()["val"]
      return m.groupdict()["val"] in self.list
    
class NumericControl(object):
  """Check on a numeric object"""
  def __init__(self,tag,target_type=None,max_valid=None,min_valid=None,element_check=None, base_class=None):
    self.tag = tag
    self.target_type = target_type
    self.base_class = base_class
    self.max_valid = max_valid
    self.min_valid = min_valid
    self.element_check = element_check

  def check(self,val):
    if self.target_type != None:
      if not type(val) == self.target_type:
        self.note = 'Value has wrong type'
        return False
    elif self.base_class != None:
      if not isinstance(val, self.base_class):
        self.note = 'Value is not instance of required class (%s): %s -- %s' % (type( self.base_class), val, type(val) )
        return False

    if self.max_valid != None and val > self.max_valid:
      self.note = 'Value is too large'
      return False
    if self.min_valid != None and val < self.min_valid:
      self.note = 'Value is too small'
      return False
    if self.element_check != None and not all( [self.element_check.check(x) for x in val] ):
      self.note = 'Not all elements match specifications'
      return False
    return True
      
    
    
class ListControl(object):
  def __init__(self,tag,list,split=False,splitVal=None,enumeration=False):
    self.list = list
    self.tag = tag
    self.split = split
    self.splitVal = splitVal
    self.enumeration = enumeration
    self.etest = re.compile( '(.*)<([0-9]+(,[0-9]+)*)>' )
    self.essplit = re.compile(r'(?:[^\s,<]|<(?:\\.|[^>])*>)+')

  def check(self,val):
    self.note = '-'
    if len(self.list) < 4:
      self.note = str( self.list )
    else:
      self.note = str( self.list[:4] )
    if self.split:
      if self.splitVal is None:
        vs = val.split( )
      elif self.enumeration:
        #vs = list(map( string.strip, self.essplit.findall( val ) ))
        vs = [x.strip() for x in self.essplit.findall( val ) ]
      else:
        #vs = list(map( string.strip, string.split( val, self.splitVal ) ))
        vs =  [ x.split() for x in val.split( self.splitVal) ]
    else:
      vs = [val,]
    if self.enumeration:
      vs2 = []
      for v in vs:
        m = self.etest.findall( v )
        if m in [None,[]]:
          vs2.append( v )
        else:
          opts = m[0][1].split( ',' )
          for o in opts:
            vs2.append( '%s%s' % (m[0][0],o) )
      vs = vs2[:]
        
    return all( [x in self.list for x in vs] )
