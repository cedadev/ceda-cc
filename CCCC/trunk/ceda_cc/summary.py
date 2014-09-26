
import string, sys, glob, os
import collections

HERE = os.path.dirname(__file__)
if HERE == '':
  HERE = '.'
print '############################ %s' % HERE

NT_esn = collections.namedtuple( 'errorShortName', ['name', 'long_name', 'description' ] )
class errorShortNames(object):

  def __init__(self,file='config/testStandardNames.txt' ):
    assert os.path.isfile(file), 'File %s not found' % file
    ii = map( string.strip, open(file).readlines() )
    ll = [[ii[0],]]
    for l in ii[1:]:
      if len(l) > 0 and l[0] == '=':
        ll.append( [l,] )
      else:
        ll[-1].append( l )
    self.ll = []
    for l in ll:
      if len(l) < 2:
        print l
      else:
        self.ll.append( NT_esn( string.strip(l[0],'='), l[1][1:], string.join(l[2:]) ) )

def cmin(x,y):
  if x < 0:
        return y
  else:
    return min(x,y)

class main(object):

  def __init__(self):
    args = sys.argv[1:-1]
    idir = sys.argv[-1]
    ndisp = 2
    dohtml = False
    while len(args) > 0:
      x = args.pop(0)
      if x == '-n':
        ndisp = int( args.pop(0) )
      elif x == '-html':
        dohtml = True

    fl = glob.glob( '%s/*__qclog_*.txt' % idir )
    fb = glob.glob( '%s/qcBatchLog*' % idir )
    fb.sort()
    fb = fb[-1]
    ii = open( fb )
    jj = []
    for k in range(10):
      jj.append( string.strip(ii.readline()) )
    ii.close()
    i0 = jj[0].index( ' INFO ' )
    tstart = jj[0][:i0]
    m1 = jj[0][i0+6:]
    m2 = jj[1][i0+6:]
    self.info = (tstart, m1, m2)
##2014-09-06 18:42:24,109 INFO Starting batch -- number of file: 338
##2014-09-06 18:42:24,109 INFO Source: /data/work/cordex/early/AFR-44i/SMHI/ECMWF-ERAINT/evaluation//.....

    ee = {}
    self.write( 'Summarising error reports from %s log file' % len(fl) )
    nne = 0
    nerr = 0
    ff = {}
    for f in fl:
      nef = 0
      elist = []
      for l in open(f).readlines():
        fn = string.split(f,'/')[-1]
        if (l[:3] == 'C4.' and string.find(l, 'FAILED') != -1) or string.find(l,'CDMSError:') != -1:
          nef += 1
          nerr += 1
          bits = map( string.strip, string.split(l, ':' ) )
          if 'FAILED' in bits:
             kb1 = bits.index('FAILED') + 1
          else:
             kb1 = 1
          if len(bits) > kb1:
            code = bits[0]
            if kb1 == 3:
              msg0 = string.join(bits[kb1:], ':' )
              msg = string.strip( bits[1] + ' ' + msg0 )
              se = bits[1][1:-1]
            else:
              msg = string.strip( string.join(bits[kb1:], ':' ) )
              msg0 = msg
              se = None
            if code not in ee.keys():
              ee[code] = [0,{msg:[0,[]]},se]
            elif msg not in ee[code][1].keys():
              ee[code][1][msg] = [0,[]]
            ee[code][0] += 1
            ee[code][1][msg][0] += 1
            if ee[code][1][msg][0]:
              ee[code][1][msg][1].append(fn)
            elist.append( (code,msg,se) )
          else:
            self.write( str(bits) )
      if nef == 0:
        nne += 1
      else:
        ff[fn] = elist

    keys = ee.keys()
    keys.sort()

    for k in keys:
      ks = ee[k][1].keys()
      if len(ks) == 1:
        self.write( '%s:  %s  %s' % (k,ee[k][0],ks[0]) )
        for i in range(cmin(ndisp,ee[k][0])):
          self.write( '               %s' % ee[k][1][ks[0]][1][i] )
      else:
        self.write( '%s: %s' % (k,ee[k][0])  )
        ks.sort()
        for k2 in ks:
          self.write( '  --- %s: %s' % (k2,ee[k][1][k2][0]) )
          for i in range(cmin(ndisp,ee[k][1][k2][0])):
            self.write( '               %s' % ee[k][1][k2][1][i] )

    self.write( 'Number of files with no errors: %s' % nne )
    esum = (len(fl), nerr, nne )
    self.testnames()
    if dohtml:
      self.htmlout( ee, ff, esum )
      self.htmlEsn( )

  def testnames(self):
    tnfile = '%s/config/testStandardNames.txt' % HERE
    ii = open( tnfile ).readlines()
    self.tests = []
    thistest = None
    for l in ii:
      if l[0] == '=':
        name = string.strip(l)[1:-1]
        if thistest != None:
          thistest.append(defn)
          self.tests.append( thistest )
        thistest = [name,]
        defn = ''
      elif l[0] == '*':
        thistest.append( string.strip(l)[1:] )
      elif string.strip(l) != '':
        defn += l
    thistest.append(defn)
    self.tests.append( thistest )
    self.testdict = {}
    for t in self.tests:
      self.testdict[t[0]] = (t[1],t[2])
    
  def write( self, s ):
    print s

  def htmlEsn( self ):
    esn = errorShortNames()
    cnt = '<h1>Error Short Names</h1>\n'
    for l in esn.ll:
      cnt += '''<a name="%s"><h2>%s</h2></a>
            <p><i>%s</i><br/>
             %s
             </p>
             ''' % (l.name,l.name, l.long_name, l.description )
    
    self.__htmlPageWrite( 'html/ref/errorShortNames.html', cnt )

  def htmlout( self, ee, ff, esum ):
    if not os.path.isdir( 'html' ):
      os.mkdir( 'html' )
      os.mkdir( 'html/ref' )
      os.mkdir( 'html/files' )
      os.mkdir( 'html/errors' )
    about = """<p>Output from CEDA CC</p>
<p>This report contains a list of errors for each file, and a list of files associated with each error.</p>
"""
    data = """<p>%s<br/>
     %s<br/>
     Start of checks: %s</p>
""" % (self.info[1], self.info[2], self.info[0] )
    results = """<ul><li>Number of files tested: %s: <a href="files/findex.html">index by file</a></li>
                     <li>Number of errors: %s: <a href="errors/eindex.html">index by error</a></li>
                     <li>Number of error free files: %s</li></ul>
""" % esum

    keys = ee.keys()
    keys.sort()
    list = []
    for k in keys:
      if ee[k][2] == None:
        list.append( '<li>%s: %s</li>' % (k,ee[k][0]) )
      else:
        assert ee[k][2] in self.testdict.keys(), 'unrecognised test name: %s' % ee[k][2]
        list.append( '<li>%s [%s:%s]: %s</li>' % (self.testdict[ee[k][2]][0],k,ee[k][2],ee[k][0]) )
    res2 = '<ul>%s</ul>' % string.join(list, '\n' )
    results += res2

    maincontent = """<h1>The test</h1>
                         %s
                     <h1>The data</h1>
                         %s
                     <h1>Results</h1>
                         %s
""" % (about,data,results)
    self.__htmlPageWrite( 'html/index.html', maincontent )

    keys = ee.keys()
    keys.sort()

    eItemTmpl = '<li><a href="rep.%3.3i.html">%s [%s]</a>: %s</li>'
    list = []
    nn = 0
    for k in keys:
      ks = ee[k][1].keys()
      ks.sort()
      sect_esn = None
      for k2 in ks:
        nn += 1
        this_esn = string.split(k2,']')[0][1:]
        if this_esn != sect_esn:
          sect_esn = this_esn
          list.append( '<h2>%s: %s<a href="../ref/errorShortNames.html#%s">(definition)</a></h2>' % (k,this_esn, this_esn) )
        list.append( eItemTmpl % (nn,k, ee[k][1][k2][0], k2  ) )
        l2 = []
        for ss in ee[k][1][k2][1]:
            i0 = string.index( ss, '__qclog' )
            fs = ss[:i0]
            l2.append( '<li><a href="../files/rep.%s.html">%s</a></li>' % (fs,fs) )
        ePage = """<h1>Error %s </h1> %s <ul>%s</ul> """ % (nn,k2,string.join( l2, '\n' ) )
        efp = 'html/errors/rep.%3.3i.html' % nn 
        self.__htmlPageWrite( efp, ePage )
    eIndexContent = """<h1>List of detected errors</h1>
<p>Code[number of files with error]: result <br/>
Click on the code to see a list of the files in which each error is detected.
</p>
<ul>%s</ul>
"""  % (string.join(list, '\n' ) )
    self.__htmlPageWrite( 'html/errors/eindex.html', eIndexContent )

    keys = ff.keys()
    keys.sort()
    fItemTmpl = '<li><a href="%s">%s [%s]</a></li>'
    list = []
    for k in ff:
      i0 = string.index( k, '__qclog' )
      fs = k[:i0]
      knc = fs + '.nc'
      hfn = 'rep.%s.html' % fs
      hfp = 'html/files/%s' % hfn
      list.append( fItemTmpl % (hfn, knc, len(ff[k]) ) )
      l2 = []
      for f in ff[k]:
        l2.append( '<li>%s: %s</li>' % f[:2] )
      fPage = """<h1>Errors in %s.nc</h1>
<ul>%s</ul>
""" % (fs,string.join( l2, '\n' ) )
      self.__htmlPageWrite( hfp, fPage )
    list.sort()
    fIndexContent = """<h1>List of files with errors</h1>
        File name [number of errors]
<ul> %s </ul>
"""  % string.join( list, '\n' )
    self.__htmlPageWrite( 'html/files/findex.html', fIndexContent )


  def __htmlPageWrite(self, pp, content):
    ptmpl = """<html><body>%s</body></html>"""
    oo = open( pp, 'w' )
    oo.write( ptmpl % content )
    oo.close()

if __name__ == '__main__':
  main()
