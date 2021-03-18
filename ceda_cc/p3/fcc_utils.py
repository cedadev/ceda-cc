import string, os, re, stat, sys

ncdumpCmd = 'ncdump'
ncdumpCmd = '/usr/local/5/bin/ncdump'
##

from .xceptions import *

##
## this class carries a logging method, and is used to carry information about datasets being parsed.
##
class qcHandler(object):

  def __init__( self, qcc, log, baseDir, logPasses=True ):
    self.datasets = {}
    self.groups = {}
    self.baseDir = baseDir
    self.logPasses = logPasses
    self.log = log
    self.nofail = True
    self.hasTimeRange = False
    for k in list(qcc.datasets.keys()):
      self.datasets[k] = {}
    for g in qcc.groups:
      self.groups[g[0]] = { 'pat':g[1]}
    self.msg = {}
    self.msgk = {}
    self.msg['CQC.101.001.001'] = 'File size above 10 bytes'
    self.msg['CQC.101.001.002'] = 'File name matches DRS syntax'
    self.msg['CQC.101.001.003'] = 'File name time component matches DRS syntax'
    self.msg['CQC.101.001.004'] = 'File name component not in vocabulary'
    self.msg['CQC.101.001.005'] = 'File name component does not match regex'
    self.msg['CQC.101.001.006'] = 'File name component does not match regex list'
    self.msg['CQC.101.001.007'] = 'File name component does not match regex list with constraints'
    self.msg['CQC.102.002.001'] = 'File name time components in ADS have same length'
    self.msg['CQC.102.002.002'] = 'File name time components in ADS do not overlap'
    self.msg['CQC.102.002.003'] = 'File name time components in ADS have no gaps'
    self.msg['CQC.102.002.004'] = 'File name time components in ADS have correct gap for monthly data'
    self.msg['CQC.102.002.005'] = 'File name time components present for multi-file dataset'
    self.msg['CQC.102.002.006'] = 'Consistency checks'
    self.msg['CQC.102.002.007'] = 'Required variables'
    self.msg['CQC.102.002.008'] = 'Required data variables'
    self.msg['CQC.102.002.009'] = 'File is a recognised NetCDF format'
    self.msg['CQC.102.002.010'] = 'Variable attributes match tables'
    self.msg['CQC.200.003.001'] = 'NetCDF files occur at one directory level'
    self.msg['CQC.103.003.002'] = 'Conformant version directory'
    self.msg['CQC.103.003.003'] = 'Latest link points to most recent version'
    self.msg['CQC.200.003.004'] = 'ads occurs in a single directory'
    self.msg['CQC.104.004.001'] = 'Consistent global attributes across experiment'
    self.msg['CQC.105.004.002'] = 'Valid calendar attribute'
    self.msg['CQC.101.004.003'] = 'Regular time step in file'
    self.msg['CQC.102.004.004'] = 'Regular time step between files'
    self.msg['CQC.102.004.005'] = 'Exceptions to regular time period'
    self.msg['CQC.102.004.005'] = 'Consistent global attributes across ADS'
    self.msg['CQC.105.004.006'] = 'Consistent global attributes across ensemble'
    self.msg['CQC.101.004.007'] = 'Required global attributes'
    self.msg['CQC.103.900.001'] = 'Identifiedmost recent version'
    self.msg['CQC.103.003.005'] = 'Version directories identified in directory containing "latest"'
## error keys: when these occur, further processing of that file is blocked.
    self.errorKeys = ['CQC.101.001.001', 'CQC.101.001.002']
## keys in this list will not be recorded as failed tests.
    self.ignoreKeys = []
    for k in list(self.msg.keys()):
        self.msgk[k] = 0

  def _log( self, key, item, msg, ok=False ):
    if ok:
      if self.logPasses:
         thisMsg = '%s OK: %s: %s: %s' % (key,item,self.msg[key], msg)
         self.log.info( thisMsg )
      return

    if key not in self.ignoreKeys:
      self.nofail = False
    item = string.replace( item, self.baseDir, '' )
    if key in self.errorKeys:
       self.log.error( '%s [ERROR] FAIL !(%s): %s: %s' % (key,self.msg[key], item,msg))
       self.noerror = False
    else:
       thisMsg = '%s FAIL !(%s): %s: %s' % (key,self.msg[key],item, msg)
       self.log.info( thisMsg )
             
    self.msgk[key] += 1

class dirParser(object):

  def __init__(self, qcc, linksOnly=True):
    self.nclevs = []
    self.qcc = qcc
    self.dirNames = {}
    self.count_nc  = 0
    self.linksOnly=linksOnly

  def parse( self, handler,dir, files ):
    handler.log.info( 'Directory: %s [%s]' % (dir, len(files)) )
    bits = string.split(dir,'/')
    thisLev = len(bits)
    files.sort()
    skipf = []

    for f in files:
      if os.path.isdir( '%s/%s' % (dir,f) ) and f in self.qcc.omitDirectories:
        skipf.append(f)
    for f in skipf:
      handler.log.info( 'skipping %s' % f )
      files.pop( files.index(f) )
      
# record directory names at each level
    if thisLev not in list(self.dirNames.keys()):
       self.dirNames[thisLev] = []
    if bits[-1] not in self.dirNames[thisLev]:
       self.dirNames[thisLev].append( bits[-1] )

    ncFiles = []
    for f in files:
      if f[-3:] == ".nc" and (not self.linksOnly or os.path.islink('%s/%s'%(dir,f))):
        ncFiles.append(f)

# record which directory levels contain netcdf files
    if len(ncFiles) and thisLev not in self.nclevs:
      self.nclevs.append( thisLev )
      
    tbits = []
    ncFiles.sort()
    self.count_nc += len( ncFiles )
    dbits = string.split( string.strip(dir,'/'), '/' )
    for f in ncFiles:
      fpath = '%s/%s' % (dir,f)
      handler.noerror = True
      handler.nofail = True

      if not os.path.islink( fpath ):
         fsb = os.stat(  fpath  )[stat.ST_SIZE]
      else:
         fsb = os.stat(  fpath  )[stat.ST_SIZE]
         if fsb < 10:
           handler._log( 'CQC.101.001.001',  fpath, '' )

      fbits = string.split( string.split(f,'.')[0], self.qcc.fileNameSegments.sep )
      if not len( fbits ) in self.qcc.fileNameSegments.nn:
        handler._log( 'CQC.101.001.002',  fpath, str(fbits) )
######
######
      else:
       qfns = self.qcc.fileNameSegments
       ns = {}
       for k in range(len(fbits)): 
         ns['fn_%s' % qfns.segments[k][1]] = fbits[k]
         if qfns.segments[k][0] == 'vocabulary':
           assert qfns.segments[k][1] in list(self.qcc.vocab.keys()), '%s not a valid vocabulary name' % qfns.segments[k][1]
           if not fbits[k] in self.qcc.vocab[qfns.segments[k][1]]:
              handler._log( 'CQC.101.001.004',  fpath, 'Not in vocab %s' % qfns.segments[k][1] )
         elif qfns.segments[k][0] == 'abstractVocab':
           assert qfns.segments[k][1] in list(self.qcc.vocab.keys()), '%s not a valid abstract vocabulary name' % qfns.segments[k][1]
           this = self.qcc.vocab[qfns.segments[k][1]]
           assert this[0] == 'regex', 'Unexpected start of abstractVocab, %s' % str( this )
           match = False
           for s,t,tt in this[1]:
              if s.match( fbits[k] ):
                match = True
                ## print 'Match [%s] found for %s {%s}' % (t,fbits[k],tt)
                for k in list(y.groupdict().keys()):
                    ns['fnre_%s' % k] = y.groupdict()[k]
                if tt != None:
                  ##print 'trying further test'
                  tt1 = string.replace(tt,'$','_arg_')
                  y = s.match( fbits[k] )
                  for k in list(y.groupdict().keys()):
                    eval( '_arg_%s = int( %s )' % (k,y.groupdict()[k] ) )
                  eval( 'res = tt1' )
                  ##print res
              else:
                pass
                ## print 'no match [%s] for %s ' % (t,fbits[k])
                   
           if not match:
              handler._log( 'CQC.101.001.006',  fpath, 'Failed abstractVocab regex tests %s' % fbits[k] )
         elif qfns.segments[k][0] == 'condAbstractVocab':
           assert qfns.segments[k][1] in list(self.qcc.vocab.keys()), '%s not a valid abstract vocabulary name' % qfns.segments[k][1]
           this = self.qcc.vocab[qfns.segments[k][1]]
           assert this[0] == 'regex', 'Unexpected start of abstractVocab, %s' % str( this )
           match = False
           olc = 0
           for sss in this[1]:
             ol = False
             if sss[0] == '*':
               ol = True
             else:
               for b in string.split(sss[0],','):
                 if b in fbits:
                   ol = True
             if ol:
               nunc = 0
               olc += 1
               for s,t,tt in sss[1]:

                 if not match:
                  y = s.match( fbits[k] )
                  if y:
                    ## print 'Match [%s] found for %s {%s}' % (t,fbits[k],tt)
                    nunc += 1
                    for key in list(y.groupdict().keys()):
                        ns['fnre_%s' % key] = y.groupdict()[key]
                    ##print '--- Match [%s] found for %s {%s}' % (t,fbits[k],tt)
                    if tt != None:
                      ## create string with test condition.`
                      tt1 = string.replace(tt,'$','_arg_')
                      y = s.match( fbits[k] )
                      for key in list(y.groupdict().keys()):
                        locals()['_arg_%s' % key ] = int( y.groupdict()[key] )
                        ##print '_arg_%s' % key , locals()['_arg_%s' % key ]
                      res = eval( tt1 )
                      ## print '#####', res,tt1
                      if res:
                        match = True
                    else:
                      match = True
                  else:
                    ##print 'no match [%s] for %s ' % (t,fbits[k])
                    pass
             ##else:
               ##print 'No overlap for %s, %s' % (sss[0],str(fbits))
           if olc == 0:
             ##print 'No matches fround for %s' % str(fbits)
             pass
                   
           if not match:
              handler._log( 'CQC.101.001.007',  fpath, 'Failed constrained regex tests %s (%s unconditional matches)' % (fbits[k], nunc) )
         elif qfns.segments[k][0] == 'regex-match':
           res = qfns.segments[k][2].match( fbits[k] )
           if res == None:
               handler._log( 'CQC.101.001.005',  fpath, 'Failed regex-match test: %s [%s]' % (fbits[k],qfns.segments[k][1] ) )
         elif qfns.segments[k][0] == 'vocabulary*':
           pass
         else:
           print('segment test id %s not recognised' % qfns.segments[k][0])
           raise baseException( 'segment test id %s not recognised' % qfns.segments[k][0] )
##################################
       versionned = False
       if not versionned:
        for k in list(self.qcc.datasets.keys()):
          if self.qcc.datasets[k].datasetIdArg == 'fileNameBits':
            dsId = self.qcc.datasets[k].getDatasetId( fbits )
          elif self.qcc.datasets[k].datasetIdArg == 'filePathBits':
            try:
              dsId = self.qcc.datasets[k].getDatasetId( fbits, dbits )
            except:
              print('Failed to get dsID:',fbits,dbits)
              raise baseException( 'Failed to get dsID: %s,%s' % (fbits,dbits) )
          else:
            assert False, 'datasetIdMethod %s not supported yet' % self.qcc.datasets[k].datasetIdMethod
            
          if os.path.islink( fpath ):
            dsId += '_lnk'
          if dsId not in handler.datasets[k]:
            handler.datasets[k][dsId] = []
          handler.datasets[k][dsId].append( (dir,f, handler.nofail, ns) )

class dataSetParser(object):

  def __init__(self,qcc, log, handler):
    self.qcc = qcc
    self.log = log
    self.h = handler
    self.re_istr = re.compile( '^[0-9]*$' )

  def parse(self,dsclass, dsid, files, inFileChecks=False, forceInFileChecks=True):
      self.h.nofail = True
## allowEndPeriodEqual should only be permitted for time averaged fields, but in this version it is set true for all fields.
      allowEndPeriodEqual = True
      try:
        fns = [x[1] for x in self.qcc.fileNameSegments.segments]
      except:
        print(self.qcc.fileNameSegments.segments)
        raise baseException(  str( self.qcc.fileNameSegments.segments ) )
      dsok = True
      for dir,f, fok, ns in files:
        dsok &= fok

      self.h.nofail = dsok
##
## this test should have a switch -- only to be applied to one category of file group
## need dsclass constraints
##
## constraint: setOnce: 
##
      if dsok:
        if self.qcc.hasTimeRange:
          allOk = True
          tbl = []
          for dir,f, fok, ns in files:
            thisOk = True
            fbits = string.split( string.split(f,'.')[0], self.qcc.fileNameSegments.sep )
            thisOk, tb = self.qcc.timeRange.get( fbits )

            allOk &= thisOk
            tbl.append( tb )

          if allOk:
            kkl = []
            for tb in tbl:
              kk = 0
              for i in range(2):
                if tb[i] != None:
                  ## tb[i] = int(tb[i])
                  kk+=1
              kkl.append(kk)
            
            thisOk = True
            cc = ''
            for k in range( len(tbl)-1  ):
              if kkl[k] != kkl[0]:
                 thisOk = False
                 cc += str(files[k])
            self.h._log( 'CQC.102.002.001', cc, '', ok=thisOk )

            self.h._log( 'CQC.102.002.005', '%s@%s' % (dsid,dsclass), '', ok=not(thisOk and kkl[0] == 0 and len(files) > 1) )

            if thisOk and kkl[0] == 2:
              cc = ''
              for k in range( len(tbl) -1 ):
                if tbl[k+1][0] < tbl[k][1] or (tbl[k+1][0] == tbl[k][1] and not allowEndPeriodEqual):
                  thisOk = False
                  cc += '%s, %s [%s,%s];' % (str(files[k]), str(files[k+1]),tbl[k][1],tbl[k+1][0])
              self.h._log( 'CQC.102.002.002', cc, '', ok=thisOk )

###
### run group constraints
###
          if dsclass in self.qcc.groupConstraints:
              for ct in self.qcc.groupConstraints[dsclass]:
                 ct.__reset__()
                 for dir,f, fok, ns in files:
                     if fok:
###
                        rv,res = ct.check( ns )
                        if rv != 'PASS':
                          self.h._log( ct.code, f, ct.msg, False )

##
## should only do the in-file checks once
## intention is to be able to have multiple definitions of groups with different tests
##
      files2 = []
      if (self.h.nofail and inFileChecks) or forceInFileChecks:
          ##print 'starting in-file checks'
          import ncd_parse
          for dir,f, fok, ns in files:
            if fok or forceInFileChecks:
             tmpDumpFile = '/tmp/qc_ncdump_tmp.txt'
             if os.path.isfile( tmpDumpFile ):
               os.unlink( tmpDumpFile )
             targf = '%s/%s' % (dir,f)
             fsb = os.stat(  targf  )[stat.ST_SIZE]
             assert fsb > 10, 'Small file slipped through: %s, %s' % (targ,fok)
             cmd = '%s -k %s/%s 2>&1 > %s' % (ncdumpCmd,dir,f,tmpDumpFile)
             res = os.popen( cmd ).readlines()
             ii = open( tmpDumpFile ).readlines()
             if len(ii) == 0:
               this_ok = False
             else:
               this_ok = 'Unknown' not in ii[0]
             self.h._log( 'CQC.102.002.009', '%s/%s' % (dir,f), '', ok=this_ok )
             files2.append( (dir,f, this_ok, ns) )
             if this_ok:
               cmd = '%s -h %s/%s > %s' % (ncdumpCmd,dir,f,tmpDumpFile)
               ii = os.popen( cmd ).readlines()
               fsb = os.stat(  tmpDumpFile  )[stat.ST_SIZE]
               assert fsb > 100, 'ncdump output too small, %s/%s' % (dir,f)
             
               rd = ncd_parse.read_ncdump( tmpDumpFile )
               rd.parse()

##
## messy hack -- copying globals attributes into a new dictionary
##
               for k in list(rd.gats.keys()):
                 ns['g_%s' % k] = rd.gats[k]
## rd.vars[k] is a tuple: (dims,atts), where atts is a dictionary of attributes.
               for k in list(rd.vars.keys()):
                 ns['v_%s' % k] = rd.vars[k]
               for k in list(rd.dims.keys()):
                 ns['d_%s' % k] = rd.dims[k]

               if self.qcc.attributeTests:
                 for a in self.qcc.requiredGlobalAttributes:
                   self.h._log( 'CQC.101.004.007', '%s/%s' % (dir,f), 'Attribute: %s' % a, ok=a in list(rd.gats.keys()) )

          if self.qcc.variableTests:
            for dir,f, fok, ns in files2:
             if fok:
              for rv in self.qcc.requiredVariables:
                if rv[0][0] != '$':
                  self.h._log( 'CQC.102.002.007', f, 'Required variable %s'% (rv[0]), 'v_%s' % rv[0] in list(ns.keys()))

          if self.qcc.groups:
            for dir,f, fok, ns in files2:
             if fok:
               for g in self.qcc.groups:
                  gid = g[1] % ns
                  if gid not in self.qcc.groupDict[g[0]]:
                    self.qcc.groupDict[g[0]][ gid ] = []
                  self.qcc.groupDict[g[0]][ gid ].append( ( dir,f,fok) )
                  ## print '%s:: %s' % (g[0],gid)
            

          if self.qcc.constraintTests:
            for dir,f, fok, ns in files2:
             if fok:
              for ct in self.qcc.constraints:
###
                rv,res = ct.check( ns )
                if rv != 'PASS':
                  self.h._log( ct.code, f, ct.msg, False )

          if self.qcc.variableTests:
            for dir,f, fok, ns in files2:
             if fok:
              for v in self.qcc.dataVariables:
                var = ns[v[1]]
                if v[0] == 'ns':
                  isPresent = 'v_%s' % var in list(ns.keys())
                  if v[3]:
                    self.h._log( 'CQC.102.002.008', f, '%s [%s::%s]'% (var,v[1],v[2]), isPresent )
       

class dataset(object):
   def __init__(self,name):
     self.name = name

class qcConfigParse(object):

  def __init__( self, file, log=None ):
    assert os.path.isfile( file ), '%s not found' % file
    self.firstFile = True
    self.fh = open( file )
    self.file = file
    self.sections = {}
    self.omitDirectories = ['.svn']
    self.log = log
    self.mipTables = None
    self.mipMapping = None
    self.hasTimeRange = False

  def close(self):
    self.fh.close()
    self.file = None

  def open(self,file):
    assert os.path.isfile( file ), '%s not found' % file
    self.fh = open( file )
    self.file = file

  def parse_l0(self):
    f = False
    sname = None
    for l in self.fh.readlines():
      if f:
        if l[0:4] == 'END ' and string.index( l,sname) == 4:
          f = False
          self._parse_l0_section.close()
        else:
          self._parse_l0_section.add( l )
      elif l[0:6] == 'START ':
        sname = string.strip( string.split(l)[1] )
        self._parse_l0_section = section_parser_l0( self, sname )
        f = True

  def parse_l1(self):

     if self.firstFile:
       requiredSections = ['FILENAME', 'VOCABULARIES','PATH']
     else:
       requiredSections = []
     self.firstFile = False

     for s in requiredSections:
       assert s in list(self.sections.keys()), 'Required section %s not found in %s [parsing %s]' % (s, list(self.section.keys()),self.file)
     self._parse_l1 = section_parser_l1( self )
     self._parse_l1.parse( 'GENERAL' )
     self._parse_l1.parse( 'VOCABULARIES' )
     if self.mipTables != None:
        assert self.mipMapping != None, '"mipMapping" must be set if MIP tables are used'
        ee = {}
        for m in self.mipTables:
          ee[m] = self.vocab[m]
        self.mipConstraint = Constraint__VarAtts( ee, self.mipMapping,self.vocab['mipVarAtts'] )

     self._parse_l1.parse( 'FILENAME' )
     self._parse_l1.parse( 'PATH' )
     self._parse_l1.parse( 'ATTRIBUTES' )
     self._parse_l1.parse( 'VARIABLES' )
     self._parse_l1.parse( 'CONSTRAINTS' )
     self._parse_l1.parse( 'GROUPS' )

regv = re.compile( 'version=([0-9.]+)' )
refs = re.compile( 'separator=(.+)' )
revsc = re.compile( 'validSectionCount,(.+)' )

class section_parser_l1(object):

  def __init__(self,parent):
     self.parent = parent
     self.currentSection = None
     self.gc = {}
     self.parent.constraintTests = False

  def _getVersion( self ):
    assert self.currentSection != None, '_getVersion called with no section set'
    x = regv.findall( self.currentSection[0] )
    assert len(x) == 1, 'valid version not identified at start of section: %s\n%s' % (self.currentSectionName,self.currentSection[0])
    self.version = x[0]

  def parse( self, sname ):
    if sname in self.parent.sections:

      self.currentSectionName = sname
      self.currentSection = self.parent.sections[sname]
      self._getVersion()
    else:
      self.currentSection = None

    ## print 'Parsing %s' % sname
    if sname == 'VOCABULARIES':
      self.parent.vocab = {}
      self.parse_vocabularies()
    elif sname == 'FILENAME':
      self.parse_filename()
    elif sname == 'PATH':
      self.parse_path()
    elif sname == 'ATTRIBUTES':
      self.parse_attributes()
    elif sname == 'VARIABLES':
      self.parse_variables()
    elif sname == 'CONSTRAINTS':
      self.parse_constraints()
    elif sname == 'GENERAL':
      self.parse_general()
    elif sname == 'GROUPS':
      self.parse_groups()

  def __get_match( self, regex, line, id ):
    x = regex.findall( line )
    assert len(x) == 1, 'No match found, id=%s, line=%s' % 'id,line'
    return x[0]

  def parse_vocabularies(self):
    ## print len( self.currentSection )
    base = ''
    for l in self.currentSection[1:]:
      bits = list(map( string.strip, string.split( l, ', ' ) ))
      id = bits[0]
      if id[0:2] == '__':
        assert id[2:] in ['base','mipMapping'], 'vocabulary record not recognised: %s' % l
        if id[2:] == 'base':
          assert os.path.isdir( bits[1] ), '!!!parse_vocabularies: directory %s not found' % bits[1]
          base = bits[1]
          if base[-1] != '/':
            base += '/'
        elif id[2:] == 'mipMapping':
          self.parent.mipMapping = bits[1]
      else:
        isAbstract = False
        if id[0] == '*':
          id = id[1:]
          isAbstract = True

        sl = string.split( bits[1], '|' )
        fromFile = 'file' in  sl
        isRegex = 'regex' in sl
        withSub = 'sub' in sl
        isCond = 'cond' in sl

        if not fromFile:
          vlist = string.split( bits[2] )
        else:
          fn = '%s%s' % (base,bits[2])
          assert os.path.isfile( fn), 'File %s (specified as vocabulary %s) not found' % (fn,bits[0] )
          ii = open( fn ).readlines()
          bb = string.split( bits[1], '|' )
          if '1stonline' in sl:
            vlist = []
            for i in ii:
              if i[0] != '#' and len( string.strip(i) ) > 0:
                vlist.append( string.split( string.strip(i) )[0] )
          elif '1perline' in sl:
            vlist = list(map( string.strip, ii ))
          elif 'mip' in sl:
            vlist = self.mipsc.scan_table( ii, self.parent.log )
            if self.parent.mipTables == None:
              self.parent.mipTables = []
            self.parent.mipTables.append( id )
          else:
            assert False, 'file syntax option (%s) not recognised' % bits[1]
  
        if isRegex:
          cr = []
          if withSub:
            if isCond:
              for ccc in vlist:
                 i0 = ccc.index(':')
                 cc = ccc[:i0]
                 cr0 = []
                 for v in string.split( ccc[i0+1:] ):
                     v = string.strip(v)
                     if v[0] == '{':
                       i1 = v.index('}')
                       tt = v[1:i1]
                       v = v[i1+1:]
                     else:
                       tt = None
                     v = string.strip( v, "'" )
                     try:
                       cr0.append( (re.compile( v % self.gc ),v % self.gc,tt) )
                     except:
                       print('Error trying to compile: ', v % self.gc)
                       print('Pattern: ',v)
                       raise baseException(  'Error trying to compile: %s [%s]' % ( v % self.gc, v) )
                     ## print 'compiled ' +  v % self.gc, tt
                 cr.append( (cc,cr0) )
            else:
              for v in vlist:
                 v = string.strip( v, "'" )
                 cr.append( (re.compile( v % self.gc ),v % self.gc) )
          else:
            for v in vlist:
               v = string.strip( v, "'" )
               cr.append( (re.compile( v ),v) )
          self.parent.vocab[id] = ('regex', cr )
        else:
          self.parent.vocab[id] = vlist[:]
          if id == 'mipVarAtts':
            self.mipsc = mipTableScan( vlist )
  
  def parse_filename(self):
    sep = self.__get_match( refs, self.currentSection[1], 'File separator' )
    nn = list(map( int, string.split( self.__get_match( revsc, self.currentSection[2], 'File separator' ),',') ))
    self.parent.fileNameSegments = fileNameSegments( self.parent, sep, nn )
    for l in self.currentSection[3:]:
       self.parent.fileNameSegments.add(l)
    self.parent.fileNameSegments.finish()

  def parse_attributes(self):
    if self.currentSection == None:
       self.parent.attributeTests = False
       return
    self.parent.requiredGlobalAttributes = []
    self.parent.attributeTests = True
    for l in self.currentSection[1:]:
      bits = list(map( string.strip, string.split(l,',')))
      if bits[0] == 'global':
        if bits[2] == 'required':
           self.parent.requiredGlobalAttributes.append( bits[1] )

  def parse_general(self):
    if self.currentSection == None:
       return
    self.parent.requiredGlobalAttributes = []
    self.parent.dataVariables = []
    for l in self.currentSection[1:]:
      if l[0] == '$':
        bits = list(map( string.strip, string.split(l[1:],'=')))
        self.gc[bits[0]] = bits[1]
      else:
        bits = list(map( string.strip, string.split(l,',')))
        if bits[0] == 'DataVariable':
          if bits[1] == 'byName':
            isRequired = bits[3] == 'required'
            key, msg = ref_to_key( bits[2] )
            self.parent.dataVariables.append( ('ns',key,msg,isRequired) )

  def parse_groups(self):
    self.parent.groups = []
    self.parent.groupDict = {}
    if self.currentSection == None:
       return
    for l in self.currentSection[1:]:
      bits = list(map( string.strip, string.split(l,',')))
      if bits[1] not in list(self.parent.groupDict.keys()):
          self.parent.groupDict[bits[1]] = {}
      if bits[0] == 'group':
        cc = []
        for r in string.split( bits[2], '.' ):
           cc.append( '%' + ('(%s)s' % ref_to_key( r )[0] ) )
        self.parent.groups.append( (bits[1], string.join( cc, '.' ) ) )

  def parse_constraints(self):
    if self.currentSection == None:
       self.parent.constraintTests = False
       return
    self.parent.constraintTests = True
    self.parent.constraints = []
    self.parent.groupConstraints = {}
    for l in self.currentSection[1:]:
       bits = list(map( string.strip, string.split(l,',')))
       bb = string.split( bits[0], ':' )
       if len(bb) == 2:
         gid = bb[0]
         cid = bb[1]
         if gid not in list(self.parent.groupConstraints.keys()):
            self.parent.groupConstraints[gid] = []
       else:
         gid = None
         cid = bits[0]
       assert cid in ['identity','onlyOnce','constant','special'], 'constraint id %s not recognised' % cid

       if cid == 'identity':
         cstr = Constraint__IdentityChecker( bits[1], bits[2] )
       elif cid == 'onlyOnce':
         ## print 'Set Constraint only once, %s ' % bits[1]
         cstr = Constraint__OnlyOnce( bits[1] )
       elif cid == 'constant':
         ## print 'Set Constraint only once, %s ' % bits[1]
         cstr = Constraint__Constant( bits[1] )
       elif cid == 'special':
         assert bits[1] in ['mip','CordexInterpolatedGrid'], 'Special constraint [%s] not recognised' % bits[1]
         if bits[1] == 'mip':
            cstr = self.parent.mipConstraint
         elif bits[1] == 'CordexInterpolatedGrid':
            cstr = Constraint__CordexInterpolatedGrid()
         
       if gid == None:
           self.parent.constraints.append( cstr )
       else:
           self.parent.groupConstraints[gid].append( cstr )

  def parse_variables(self):
    if self.currentSection == None:
       self.parent.variableTests = False
       return
    self.parent.variableTests = True
    self.parent.requiredVariables = []
    for l in self.currentSection[1:]:
       bits = list(map( string.strip, string.split(l,',')))
       isDimension = bits[0] == 'dimension'
       if bits[2] == 'required':
         if bits[1][0] != '$':
           self.parent.requiredVariables.append( (bits[1],isDimension) )
         else:
           key,info = ref_to_key( bits[1][1:] )
           if key == 'VALUE':
             self.parent.requiredVariables.append( (info,isDimension) )
           else:
             self.parent.requiredVariables.append( ('$%s' % key, isDimension) )
           


  def parse_path(self):
    if self.currentSection == None:
       self.pathTests = False
       return
    self.pathTests = True
    self.datasetIdMethod = None
    self.datasetVersionMode = [None,]
    self.parent.datasets = {}
    datasetHierarchy = None
    for l in self.currentSection[1:]:
       bits = list(map( string.strip, string.split(l,',')))
       if bits[0] == 'datasetVersion':
         vdsName = bits[1]
         if bits[2] == 'pathElement':
           self.datasetVersionMode = ['pathElement',]
           self.versionPathElement = int( bits[3] )
         if bits[4] == 'regex':
           self.datasetVersionMode.append( 'regex' )
           self.datasetVersionRe = re.compile( string.strip( bits[5], '"' ) )
         else:
           self.datasetVersionMode.append( None )
       elif bits[0] == 'datasetId':
         thisDs = dataset(bits[1])
         thisDs.datasetIdMethod = bits[2]
         if bits[2] == 'prints':
           thisDs.getDatasetId = lambda x: bits[3] % x
           thisDs.datasetIdTuple = tuple( bits[4:] )
         elif bits[2] == 'joinFileNameSegSlice':
           thisSlice = slice( int(bits[4]), int(bits[5]) )
           thisDs.getDatasetId = dsid1( thisSlice, bits[3] ).get
           thisDs.datasetIdArg = 'fileNameBits'
         elif bits[2] == 'cmip5':
           thisSlice = slice( int(bits[4]), int(bits[5]) )
           thisDs.getDatasetId = cmip5_dsid( thisSlice, bits[3] ).get
           thisDs.datasetIdArg = 'filePathBits'
         self.parent.datasets[bits[1]] = thisDs
       elif bits[0] == 'datasetHierarchy':
         datasetHierarchy = bits[1:]
       elif bits[0] == 'omitDirectories':
         self.parent.omitDirectories = string.split( string.strip( bits[1] ) )

    if self.datasetVersionMode[0] != None:
      assert vdsName in list(self.parent.datasets.keys()), 'Invalid dataset specified for version: %s [%s]' % (vdsName, str( list(self.parent.datasets.keys()) ) )
      self.versionnedDataset = self.parent.datasets[ vdsName ]

    if datasetHierarchy == None:
      self.datasetHierarchy = False
    else:
      self.datasetHierarchy = True
      bb = string.split( string.strip( datasetHierarchy[0]), '/' )
      for b in bb:
        assert b in list(self.parent.datasets.keys()), 'Invalid dataset hierarchy, %s not among defined datasets' % b
      for k in list(self.parent.datasets.keys()):
        self.parent.datasets[k].inHierarchy = k in bb
          
      for k in range( len(bb) ):
        if k == 0:
          self.parent.datasets[bb[k]].parent = None
        else:
          self.parent.datasets[bb[k]].parent = self.parent.datasets[bb[k-1]]
        if k == len(bb)-1:
          self.parent.datasets[bb[k]].child = None
        else:
          self.parent.datasets[bb[k]].child = self.parent.datasets[bb[k+1]]
          
class dsid1(object):

  def __init__(self,slice,sep):
    self.slice = slice
    self.sep = sep

  def get(self,x):
    return string.join( x[self.slice], self.sep ) 

class cmip5_dsid(object):

  def __init__(self,slice,sep):
    self.slice = slice
    self.sep = sep

  def get(self,x,y):
    return '%s_%s.%s' % (string.join( x[self.slice], self.sep ) , y[-2], y[-1] )


class get_trange(object):
 
  def __init__(self,pat,kseg):
    self.kseg = kseg
    self.re_istr = re.compile( '^[0-9]*$' )
    if type( pat ) == type( 'x' ):
      self.pat = pat
      self.re = re.compile( pat )
    else:
      self.re = pat

  def _test( self, s):
    return self.re.match( s ) != None

  def _get( self, s, handler=None ):
    x = self.re.match( s )
    tb = [None,None]
    if x == None:
      return False, tuple(tb)

    thisOk = True
    tb[0] = x.groupdict().get( 'start', None )
    tb[1] = x.groupdict().get( 'end', None )
    if 'isClim' in x.groupdict():
      tb.append( x.groupdict()['isClim'] )
    for i in range(2):
        b = tb[i]
        if b != None:
           if self.re_istr.match( b ) == None:
              if handler != None:
                handler._log( 'CQC.101.001.003',  dir + f, 'part of string not an integer' )
              thisOk = False
           else:
             tb[i] = int(tb[i])

    return thisOk, tb


  def test(self, l ):
    if len(l) < self.kseg + 1:
      return True
    return self._test( l[self.kseg] )

  def get(self,l):
    if len(l) < self.kseg + 1:
      return True, (None,None)
    return self._get( l[self.kseg] )
         
class fileNameSegments(object):
  def __init__(self, parent, sep, nn ):
    self.sep = sep
    self.nn = nn
    self.nn.sort()
    self.__segments  = {}
    self.parent = parent

  def add( self, line ):
    bits = list(map( string.strip, string.split( line, ', ' ) ))
    k = int(bits[0])
    if bits[1] == 'vocabulary':
      assert bits[2] in list(self.parent.vocab.keys()), 'Vocabulary specified in file name section not defined in vocab sections, %s' % bits[2]
      
      self.__segments[k] = ('vocabulary',bits[2])
    elif bits[1][0:5] == 'regex' or bits[2] == 'TimeRange':
      try:
        regex = re.compile( string.strip( bits[3], "'") )
      except:
        print('Failed to compile (in re): %s' % bits[3])
        raise baseException(  'Failed to compile (in re): %s' % bits[3] )
      self.__segments[k] = (bits[1],bits[2], regex)
    else:
      self.__segments[k] = tuple( bits[1:] )

    if bits[2] == 'TimeRange':
       self.parent.hasTimeRange = True
       self.parent.timeRange = get_trange(regex,k)

  def finish(self):
    sl = []
    for k in range(self.nn[-1]):
      sl.append( self.__segments.get( k, None ) )
    self.segments = tuple( sl )

class Constraint__CordexInterpolatedGrid(object):

  def __init__(self):
     self.code = 'CQC.999.999.999'
     self.name = 'CordexInterpolatedGrid'
     self.mode = 'd'

  def __reset__(self):
    pass

  def check(self,fns):
    region = fns.get( 'g_CORDEX_domain', 'unset' )
    assert region != 'unset', 'CORDEX domain not found in %s' % str(list(fns.keys()))
    if region[-3:] != '44i':
       self.msg = 'Interpolated grid constraint not applicable to region %s' % region
       return ('PASS',self.msg)
    print('WARNING -- check not implemented')
    self.msg = 'WARNING -- check not implemented'
    return ('PASS',self.msg)

class Constraint__IdentityChecker(object):

  def __init__(self, ref1, ref2 ):
     self.code = 'CQC.102.002.006'
     self.name = 'IdentityChecker'
     self.mode = 'd'
     self.Ref1 = self.__parse_ref(ref1)
     self.Ref2 = self.__parse_ref(ref2)
     if self.Ref1 == 'VALUE':
       self.Ref1 = self.Ref2
       self.Ref2 = 'VALUE'
     if self.Ref2 == 'VALUE':
       self.mode = 's'

     if self.mode == 's':
       self.PassMsg = '%s (%s) equals %s' % (self.Ref1[1], ref1, self.value)
       self.FailMsg = '%s (%s) not equal %s' % (self.Ref1[1], ref1, self.value)
     else:
       self.PassMsg = '%s (%s) not equal %s (%s)' % (self.Ref1[1],ref1, self.Ref2[1],ref2)
       self.FailMsg = '%s (%s) not equal %s (%s)' % (self.Ref1[1],ref1, self.Ref2[1],ref2)

  def __parse_ref(self,ref):
     bits = string.split(ref,'/')
     assert bits[0] in ['VALUE','PATH','FILENAME','ATTRIBUTES','CONFIG','ARGS'], 'Bad line in CONSTRAINT section of config file'
     if bits[0] == 'ATTRIBUTES':
        if bits[1] == 'Global':
           return ('g_%s' % bits[2],'Global attribute %s' % bits[2] )
     elif bits[0] == 'FILENAME':
           return ('fn_%s' % bits[1],'File name component %s' % bits[1] )
     elif bits[0] == 'VALUE':
           self.value = bits[1]
           return 'VALUE'

  def __reset__(self):
    pass

  def check(self,fns):
    if self.mode == 's':
      if self.Ref1[0] in fns:
        if fns[self.Ref1[0]] == self.value:
          self.msg = self.PassMsg
          return ('PASS',self.msg)
        else:
          self.msg = self.FailMsg + ' [%s]' % fns[self.Ref1[0]] 
          return ('FAIL',self.msg)
      else:
        return ('DEFER', 'No entry in fns for %s' % self.Ref1[0])
    else:
      if self.Ref1[0] in fns and self.Ref2[0] in fns:
        if fns[self.Ref1[0]] == fns[self.Ref2[0]]:
          self.msg = self.PassMsg
          return ('PASS',self.msg)
        else:
          self.msg = self.FailMsg + ' [%s,%s]' % (fns[self.Ref1[0]] , fns[self.Ref2[0]])
          return ('FAIL',self.msg)
      else:
        return ('DEFER', 'No entry in fns for %s,%s' % (self.Ref1[0],self.Ref2[0]))

def parse_ref(ref):
     bits = string.split(ref,'/')
     assert bits[0] in ['VALUE','PATH','FILENAME','FILENAMEregex','ATTRIBUTES','CONFIG','ARGS'], 'Bad line in CONSTRAINT section of config file'
     if bits[0] == 'ATTRIBUTES':
        if bits[1] == 'Global':
           return ('g_%s' % bits[2],'Global attribute %s' % bits[2] )
     elif bits[0] == 'FILENAME':
           return ('fn_%s' % bits[1],'File name component %s' % bits[1] )
     elif bits[0] == 'FILENAMEregex':
           return ('fnre_%s' % bits[1],'File name component %s' % bits[1] )
     elif bits[0] == 'VALUE':
           return ('VALUE', bits[1])

class Constraint__OnlyOnce(object):

  def __init__(self, ref1):
     self.code = 'CQC.102.004.005'
     self.name = 'OnlyOnce'
     self.nn = 0
     self.Ref1 = parse_ref(ref1)
     self.msg = '%s occurs only once' % self.Ref1[1]

  def __reset__(self):
    self.nn = 0

  def check(self,fns):
      if self.Ref1[0] in fns:
        self.nn+=1
        if self.nn <= 1:
          return ('PASS' ,'Occurence rate OK')
        else:      
          return ('FAIL', '%s occurs too often' % self.Ref1[0] )
      else:
        keys = list(fns.keys())
        keys.sort()
        return ('PASS',None)

#### Mip table variable attribute check

class Constraint__VarDimsCordexHardWired(object):
  def __init__(self, attribVocabs,  kpat, keys, logger=None):
     self.code = 'CQC.102.002.010'
     self.name = 'VarAtts'
     self.tables = {}
     self.keys = keys
     self.kpat = kpat
     self.logger = logger
     self.plev_vars = ['clh','clm','cll','ua850','va850']

class Constraint__VarAtts(object):

  def __init__(self, attribVocabs,  kpat, keys, logger=None):
     self.code = 'CQC.102.002.010'
     self.name = 'VarAtts'
     self.tables = {}
     self.keys = keys
     self.kpat = kpat
     self.logger = logger
     for t in list(attribVocabs.keys()):
        self.tables[t] = {}
        for i in attribVocabs[t]:
          self.tables[t][i[0]] = (i[1],i[2])
        self.log( 'i', 'Initialising Constraint__VarAtts, table %s' % t )

  def log( self, lev, msg ):
     if self.logger != None:
       if lev == 'i':
         self.logger.info( msg )
       elif lev == 'w':
         self.logger.warn( msg )
     
  def check(self, fns):
     self.msg = 'starting'
     mip = self.kpat % fns
     var = fns['fn_variable']
     if mip not in self.tables:
       self.msg = 'VarAtts: no table found -- kpat = %s' % self.kpat
       return ('FAIL', self.msg )
     res = self.__check( mip, var, fns )
     return res

  def __check( self, mip, var, fns ):
     ms = ''
     self.log( 'i', 'CHECKING %s' % var )
     nf = 0
     if var not in self.tables[mip]:
       self.msg = 'Variable %s not present in table %s' % (var,mip)
       ##print ('FAIL',self.msg)
       return ('FAIL', self.msg)
     assert 'v_%s' % var in fns, 'Internal error: attempt to check variable %s which is not in fns' % var
     mip_dims, mip_ats = self.tables[mip][var]
     var_dims = fns['v_%s' % var ][0]
     for k in self.keys:
        if mip_ats[k] != fns['v_%s' % var ][1][k]:
           self.log( 'w', 'Variable attribute mismatch: %s -- %s' % (mip_ats[k], str(fns['v_%s' % var ]) ) )
           nf += 1
           ms += '%s; ' % k
        else:
           self.log( 'i', 'Attribute OK: %s' % (self.tables[mip][var][1][k]) )

     # unclear how to proceed here -- want to check, e.g., time dimension.  -- possibly easiest to have a CORDEX_SPECIAL flag for some ad hoc code..
     # ideally get axis information from "axis_entry" in mip tables -- need to improve the scanner for this.
     ##print 'DIMS:  %s -- %s -- %s' % (var, str(mip_dims), str(var_dims))
     if nf > 0:
       if nf == 1:
         self.msg = 'Failed 1 attribute test: %s' % ms
       else:
         self.msg = 'Failed %s attribute tests: %s' % (nf,ms)
       ##print ('FAIL',self.msg)
       return ('FAIL',self.msg)
     else:
       ##print ('PASS','%s attributes checked' % len(self.keys) )
       return  ('PASS','%s attributes checked' % len(self.keys) )

#### check whether a NS element is constant
class Constraint__Constant(object):

  def __init__(self, ref1, required=False):
     self.code = 'CQC.102.002.006'
     self.name = 'Constant'
     self.nn = 0
     self.Ref1 = parse_ref(ref1)
     self.msg = '%s occurs only once' % self.Ref1[1]
     self.value = None
     self.required = required

  def __reset__(self):
    self.nn = 0
    self.value = None

  def check(self,fns):
      if self.Ref1[0] in fns:
        if self.value == None:
          self.value = fns[self.Ref1[0]]
          return ('DEFER', 'first element')
        else:
          if self.value == fns[self.Ref1[0]]:
            return ('PASS','%s checked' % self.Ref1[0] )
          else:
            return ('FAIL', '%s not constant across file group' %  self.Ref1[0] )
      else:
        if self.required:
          return ('FAIL', 'missing NS element %s' % self.Ref1[0] )
        else:
          return ('PASS',None)

def ref_to_key(ref):
     bits = string.split(ref,'/')
     assert bits[0] in ['VALUE','PATH','FILENAME','ATTRIBUTES','CONFIG','ARGS'], 'Bad line in CONSTRAINT section of config file'
     if bits[0] == 'ATTRIBUTES':
        if bits[1] == 'Global':
           return ('g_%s' % bits[2],'Global attribute %s' % bits[2] )
     elif bits[0] == 'FILENAME':
           return ('fn_%s' % bits[1],'File name component %s' % bits[1] )
     elif bits[0] == 'VALUE':
           return ('VALUE',bits[1])

class section_parser_l0(object):

  def __init__(self,parent,sectionName):
     self.sname = sectionName
     self.parent = parent
     self.lines = []
     
  def add( self, l ):
    self.lines.append( string.strip( l ) )

  def close(self):
    assert type(self.parent.sections) == type( {} ), 'parent.sections has wrong type (%s), should be a dictionary' % ( str( type( self.parent.sections ) ) )

    self.parent.sections[self.sname] = self.lines[:]
    self.lines = []
