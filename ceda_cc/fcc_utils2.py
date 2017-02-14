import string, os, re, stat, sys
from ceda_cc_config.config_c4 import CC_CONFIG_DIR

ncdumpCmd = 'ncdump'
ncdumpCmd = '/usr/local/5/bin/ncdump'
##

from xceptions import *

class mipTableScan(object):

  def __init__(self, vats = ['standard_name','long_name','units','cell_methods'] ):
    self.al = []
    self.vats = vats
    self.re_cmor_mip2 = re.compile( 'dimensions:(?P<dims>.*?):::' )
    self.re_vats = { }
    self.nn_tab = 0
    for v in vats:
      self.re_vats[v] = re.compile( '%s:(?P<dims>.*?):::' % v )
##
  def scan_table(self,ll,log,asDict=False,appendTo=None,lax=False,tag=None,warn=True, project='CMIP5'):

    self.project = project
    lll0 = map( string.strip, ll )
    lll = []
    for l in lll0:
      if len(l) != 0:
        if l[0] != '!':
          lll.append(string.split(l,'!')[0])
    sll = []
    sll.append( ['header',[]] )
    for l in lll:
      k = string.split( l, ':' )[0]
      if k in ['variable_entry','axis_entry']:
        sll.append( [k,[]] )
      sll[-1][1].append(l)

    eee = []
    fff = []
    nal = []
    for s in sll:
      if s[0] in ['variable_entry','axis_entry']:
        x = self.scan_entry_01( s,tag )
        if s[0] == 'variable_entry':
           eee.append(x[0])
           nal += x[1]
        else:
           fff.append(x[0])

    self.axes = fff
    nal.sort()
    nalu = [nal[0],]
    for a in nal[1:]:
      if a != nalu[-1]:
        nalu.append(a)
        if a not in self.al:
          self.al.append( a )

    checkOldMethod = False
    if checkOldMethod:
      ssss = string.join( lll, ':::' )
      vitems = string.split( ssss, ':::variable_entry:' )[1:]
 
      ee = []
      for i in vitems:
        b1 = string.split( i, ':::')[0]
        var = string.strip( b1 )
        aa = {}
        for v in self.vats:
          mm = self.re_vats[v].findall(i)
          if len(mm) == 1:
             aa[v] = string.strip(mm[0])
          else:
             aa[v] = 'None'
 
        mm = self.re_cmor_mip2.findall( i )
        if len(mm) == 1:
          ds = string.split( string.strip(mm[0]) )
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
          print 'OK:::', ee[k]
        else:
          print 'DIFF: ',ee[k],eee[k]
      
    if not asDict:
      return tuple( eee )
    else:
      ff = {}
## l[0] = var name, l[1] = dimensions, l[2] = attributes, l[3] = tag
      for l in eee:
        ff[l[0]] = ( l[1], l[2], l[3] )
      self.adict = {}
## l[0] = axis name, l[1] = attributes, l[2] = tag
      for l in fff:
        self.adict[l[0]] = ( l[1], l[2] )
      if appendTo != None:
        for k in ff.keys():
          assert ff[k][1].has_key( 'standard_name' ), 'No standard name in %s:: %s' % (k,str(ff[k][1].keys()))
          if appendTo.has_key(k):
            if lax:
              if ff[k][1]['standard_name'] != appendTo[k][1]['standard_name']:
                if warn:
                  print 'ERROR[X1]%s - %s : Inconsistent standard_names %s:: %s [%s] --- %s [%s]' % (tag,appendTo[k][3],k,ff[k][1],ff[k][2], appendTo[k][1], appendTo[k][2])
              if ff[k][1]['long_name'] != appendTo[k][1]['long_name']:
                if warn:
                  k3 = min( 3, len(appendTo[k])-1 )
                  print 'WARNING[X1]%s -- %s: Inconsistent long_names %s:: %s --- %s' % (tag,appendTo[k][k3],k,ff[k][1]['long_name'],appendTo[k][1]['long_name'])

              p1 = ff[k][1].get('positive','not set')
              p2 = appendTo[k][1].get('positive','not set')
              if p1 != p2:
                if warn:
                  k3 = min( 3, len(appendTo[k])-1 )
                  print 'WARNING[X1]%s -- %s: Inconsistent positive attributes %s:: %s --- %s' % (tag,appendTo[k][k3],k,p1,p2)

              for k2 in ff[k][1].keys():
                if k2 not in ['standard_name','long_name','positive']:
                    p1 = ff[k][1].get(k2,'not set')
                    p2 = appendTo[k][1].get(k2,'not set')
                    if p1 != p2:
                      if warn:
                        k3 = min( 3, len(appendTo[k])-1 )
                        print 'WARNING[Y1]%s -- %s: Inconsistent %s attributes %s:: %s --- %s' % (tag,appendTo[k][k3],k2,k,p1,p2)

            if not lax:
              assert ff[k][1] == appendTo[k][1], 'Inconsistent entry definitions %s:: %s [%s] --- %s [%s]' % (k,ff[k][1],ff[k][2], appendTo[k][1], appendTo[k][2])
          else:
            appendTo[k] = ff[k]
        return appendTo
      else:
        return ff

  def scan_entry_01(self,s,tag):
      assert s[0] in ['variable_entry','axis_entry'],'scan_entry_01 called with unsupported entry type: %s' % s[0]
      bits = string.split(s[1][0],':')
      assert len(bits) == 2, 'Can not unpack: %s' % str(s[1])
      k,var =  map( string.strip, string.split(s[1][0],':') )
      nal = []
      if s[0] == 'variable_entry':
         aa = {'standard_name':None, 'long_name':None,'units':None,'cell_methods':None }
         ds = 'scalar'
      else:
         aa = {'standard_name':None, 'long_name':None,'units':None }
         ds = None
      for l in s[1][1:]:
           bits = string.split(l,':')
           k = string.strip(bits[0])
           v = string.strip( string.join( bits[1:], ':' ) )
           if k == 'dimensions':
             ds = string.split(v)
           else:
             aa[k] = v
             nal.append(k)
      if self.project == 'CMIP5':
           if var == 'tos':
             if aa['standard_name'] != 'sea_surface_temperature':
               print 'Overriding incorrect CMIP5 standard_name for %s' % var
               aa['standard_name'] = 'sea_surface_temperature'
           elif var == 'ps':
             if aa['long_name'] != 'Surface Air Pressure':
               print 'Overriding inconsistent CMIP5 long_name for %s' % var
               aa['long_name'] = 'Surface Air Pressure'
      if s[0] == 'variable_entry':
        return ((var,ds,aa,tag), nal)
      else:
        return ((var,aa,tag), nal)

class snlist:

  def __init__(self,dir=None,tab='cf-standard-name-table.xml' ):
    if dir  == None:
      dir = os.path.join(CC_CONFIG_DIR, 'cf/')
    self.re_sn = re.compile( 'entry id="(.*)"' )
    self.re_sna = re.compile( 'alias id="(.*)"' )
    self.dir = dir
    self.tab = tab

##alias id="atmosphere_water_vapor_content"
##entry id="age_of_sea_ice"'

  def gen_sn_list(self ):
    pathn = self.dir + self.tab
    assert os.path.isfile( pathn ), '%s not found ' % pathn
    snl = []
    snla = []
    for l in open(pathn).readlines():
      m = self.re_sn.findall(l )
      if len(m) > 0:
        for i in m:
          snl.append( i )
      m = self.re_sna.findall(l )
      if len(m) > 0:
        for i in m:
          snla.append( i )
    return (snl,snla)

class tupsort:
   def __init__(self,k=0):
     self.k = k
   def cmp(self,x,y):
     return cmp( x[self.k], y[self.k] )

class tupsort2:
   def __init__(self,k0,k1):
     self.k0 = k0
     self.k1 = k1
   def cmp(self,x,y):
     if x[self.k0] == y[self.k0]:
       return cmp( x[self.k1], y[self.k1] )
     return cmp( x[self.k0], y[self.k0] )

class tupsort3:
   def __init__(self,k0,k1,k2):
     self.k0 = k0
     self.k1 = k1
     self.k2 = k2
   def cmp(self,x,y):
     if x[self.k0] == y[self.k0]:
       if x[self.k1] == y[self.k1]:
         return cmp( x[self.k2], y[self.k2] )
       return cmp( x[self.k1], y[self.k1] )
     return cmp( x[self.k0], y[self.k0] )
