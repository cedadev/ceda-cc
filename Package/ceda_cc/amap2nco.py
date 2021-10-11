"""USAGE:
python amap2nco.py   mappingsFile  inputDirectoryBase outputDirectoryBase
mappingsFile: text file containing mapping information, generated by c4.py
inputDirectoryBase: initial part of the directory tree, to be replaced for corrected files
outputDirectoryBase: initial part of directory tree to be used for corrected files.

A bash script of nco commands will be written to ncoscript.sh. Excecute with, for example, "bash ncoscript.sh"

Check ouput and run ceda-cc to verify that the correct changes have been implemented -- this software does not offer any guarantees.

See file USAGE_amap2nco.txt in code repository for more detail"""

import os, random, time
from .xceptions import *

xx='abcdefghijklmnopqrstuvwxyz1234567890$%-=+*'

class map2nco(object):

  def __init__(self,ifile,ipth,opth,newtid=True):
    assert os.path.isfile( ifile ), 'File %s not found' % ifile
    ii = open(ifile).readlines()
    self.directives = []
    for l in [x.strip() for x in ii]:
      if l[0] == '@':
        if l[:9] == '@varname:':
          self.directives.append( ('var',l[9:] ) )
        elif l[:5] == '@var:':
          self.directives.append( ('var',l[5:] ) )
        elif l[:4] == '@ax:':
          self.directives.append( ('ax',l[4:] ) )
        elif l[:4] == '@fn:':
          self.directives.append( ('fn',l[4:] ) )
        elif l[:2] == '@:':
          self.directives.append( ('ga',l[2:] ) )
        else:
          raise baseException( 'unrecognised directive:\n %s' % l )
      elif l[0] != '#':
        if l.strip() != '':
           raise baseException( 'unrecognised line:\n %s' % l )
    self.ipth = ipth
    self.opth = opth
    self.newtid = newtid

  def parse1( self ):
    self.flist = []
    oo = open( 'ncoscript.sh', 'w' )
    thislist = None
    lok = {'var':5, 'fn':2, 'ax':5, 'ga':4 }
    for d in self.directives:
      assert d[0] in lok, 'Directive not recognised'
      bits = d[1].strip( '"' ).split( '","' ) 
      assert len(bits) == lok[d[0]], 'Not enough elements for directive'
      fpath = bits[0]
      if thislist == None or thislist[0] != fpath:
        if thislist != None:
          self.flist.append( thislist )
        thislist = [fpath,] 
      thislist.append( (d[0],bits[1:] ) )

    self.flist.append( thislist )
    li = len(self.ipth)
    ndl = []
    for f in self.flist:
      assert os.path.isfile( f[0], ), 'File %s not found' % f[0]
      assert f[0][:li] == self.ipth, 'File not in declared input directory %s' % self.ipth
      ofile = self.opth + f[0][li:]
      ofb = ofile.split( '/')
      fn = ofb[-1]
      odir = '/'.join( ofb[:-1] ) + '/'
      if odir not in ndl:
        if not os.path.isdir( odir ):
          oo.write( 'echo Creating output directory %s\n' % odir )
          oo.write( 'mkdir -p %s\n' % odir )
          ndl.append( odir )
      
      toklist = []
      for d in f[1:]:
        if d[0] in ['var','ga']:
          print(d)
          var, att, oval, nval = d[1]
          if d[0] == 'var':
            token = '%s,%s,o,c,"%s"' % (att,var,nval)
          else:
            token = '%s,global,o,c,"%s"' % (att,var,nval)
          toklist.append(token)
        elif d[0] == 'fn':
          fs = fn.split( '.' )
          bits = fs[0].split( '_' )
          assert  d[1][0] in bits, '%s not found in file name: %s' % (d[1][0], fn)
          i = bits.index( d[1][0] )
          bits[i] =  d[1][1]
          fs[0] = '_'.join( bits )
          ofn = '.'.join( '.' )
          ofile = odir + ofn
        else:
          print('WARNING: UNREPARABLE ERRORS ARE LISTED')
          print(d)
      cmd = 'ncatted '
      if self.newtid:
        tid = ''
        for k in range(36):
          tid += xx[random.randint(0,len(xx)-1)]
        toklist.append( 'tracking_id,global,o,c,"%s"' % tid )
        toklist.append( 'creation_date,global,o,c,"%s"' % time.ctime() )
        
      for t in toklist:
        cmd += ' -a %s \\\n' % t
      cmd += ' -o %s \\\n' % ofile
      cmd += ' %s \n' % f[0]
      oo.write( 'echo Editting file %s\n'  % fn )
      oo.write( '%s\n'  % cmd )
    oo.close()
    

def main_entry():
  import sys
  if len(sys.argv) != 4:
    if os.path.isfile( 'USAGE_amap2nco.txt' ):
      for l in open( 'USAGE_amap2nco.txt').readlines():
        print(l.strip())
    else:
      print(__doc__)
  else:
     mfile, idir, odir = sys.argv[1:]
     m = map2nco(mfile, idir, odir )
     m.parse1()
      
if __name__ == '__main__':
  main_entry()


    #@var:/data/work/cordex/early/AFR-44i/SMHI/ECMWF-ERAINT/evaluation/SMHI-RCA4/v1/mon/tas/tas_AFR-44i_ECMWF-ERAINT_evaluation_r1i1p1_SMHI-RCA4_v1_mon_198001-198012.nc","height","long_name","height above the surface","height"
