
import string, sys, glob

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
    while len(args) > 0:
      x = args.pop(0)
      if x == '-n':
        ndisp = int( args.pop(0) )

    fl = glob.glob( '%s/*__qclog_*.txt' % idir )

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
        if string.find(l, 'FAILED') != -1 or string.find(l,'CDMSError:') != -1:
          nef += 1
          nerr += 1
          if string.find(l, 'FAILED') != -1:
             kb1 = 3
          else:
             kb1 = 1
          bits = string.split(l, ':' )
          if len(bits) > kb1:
            code = bits[0]
            msg = string.strip( string.join(bits[kb1:], ':' ) )
            if code not in ee.keys():
              ee[code] = [0,{msg:[0,[]]}]
            elif msg not in ee[code][1].keys():
              ee[code][1][msg] = [0,[]]
            ee[code][0] += 1
            ee[code][1][msg][0] += 1
            if ee[code][1][msg][0]:
              ee[code][1][msg][1].append(fn)
            elist.append( (code,msg) )
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
    self.htmlout( ee, ff, esum )

  def write( self, s ):
    print s

  def htmlout( self, ee, ff, esum ):
    about = "Output from CEDA CC"
    data = "Demonstration using test data"
    results = """<ul><li>Number of files tested: %s: <a href="files/findex.html">index by file</a></li>
                     <li>Number of errors: %s: <a href="errors/eindex.html">index by error</a></li>
                     <li>Number of error free files: %s</li></ul>
""" % esum

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
      for k2 in ks:
        nn += 1
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
Code[number of files with error]: result 
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
        l2.append( '<li>%s: %s</li>' % f )
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
