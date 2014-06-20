import string, os, re, stat, sys

ncdumpCmd = 'ncdump'
ncdumpCmd = '/usr/local/5/bin/ncdump'
##

from xceptions import *

class mipTableScan(object):

  def __init__(self, vats = ['standard_name','long_name','units','cell_methods'] ):
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
    for s in sll:
      if s[0] == 'variable_entry':
         bits = string.split(s[1][0],':')
         assert len(bits) == 2, 'Can not unpack: %s' % str(s[1])
         k,var =  map( string.strip, string.split(s[1][0],':') )
         aa = {'standard_name':None, 'long_name':None,'units':None,'cell_methods':None }
         ds = 'scalar'
         for l in s[1][1:]:
           bits = string.split(l,':')
           k = string.strip(bits[0])
           v = string.strip( string.join( bits[1:], ':' ) )
           if k == 'dimensions':
             ds = string.split(v)
           else:
             aa[k] = v
         if self.project == 'CMIP5':
           if var == 'tos':
             if aa['standard_name'] != 'sea_surface_temperature':
               print 'Overriding incorrect CMIP5 standard_name for %s' % var
               aa['standard_name'] = 'sea_surface_temperature'
           elif var == 'ps':
             if aa['long_name'] != 'Surface Air Pressure':
               print 'Overriding inconsistent CMIP5 long_name for %s' % var
               aa['long_name'] = 'Surface Air Pressure'
         eee.append( (var,ds,aa,tag) )


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
      for l in eee:
        ff[l[0]] = ( l[1], l[2], l[3] )
      if appendTo != None:
        for k in ff.keys():
          assert ff[k][1].has_key( 'standard_name' ), 'No standard name in %s:: %s' % (k,str(ff[k][1].keys()))
          if appendTo.has_key(k):
            if lax:
              if ff[k][1]['standard_name'] != appendTo[k][1]['standard_name']:
                if warn:
                  print 'ERROR[X1]%s: Inconsistent standard_names %s:: %s [%s] --- %s [%s]' % (tag,k,ff[k][1],ff[k][2], appendTo[k][1], appendTo[k][2])
              if ff[k][1]['long_name'] != appendTo[k][1]['long_name']:
                if warn:
                  print 'WARNING[X1]%s: Inconsistent long_names %s:: %s --- %s' % (tag,k,ff[k][1]['long_name'],appendTo[k][1]['long_name'])
            if not lax:
              assert ff[k][1] == appendTo[k][1], 'Inconsistent entry definitions %s:: %s [%s] --- %s [%s]' % (k,ff[k][1],ff[k][2], appendTo[k][1], appendTo[k][2])
          else:
            appendTo[k] = ff[k]
        return appendTo
      else:
        return ff
