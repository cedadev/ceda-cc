"""
Arguments:
  :-p: project
  :--copy-config: <target directory path>: copy configuration files to target directory path;
  :--sum: <log file directory> create a summary of the results  logged in the specified directory.
  :-f: <file>: check a single file;
  :-d: <directory>: check all the NetCDF files in a directory;
  :-D: <directory>: check all the NetCDF files in a directory tree (or latest versions if a recognised version managment system is defined for the project);
  :--ld: <log file directory>:  ## directory to take log files;
  :-R: <record file name>: file name for file to take one record per file checked;
  :-l: <file list file>: a file containing one data file to check per line;
  :--cae: "catch all errors": will trap exceptions and record in  log files, and then continue. Default is to stop after unrecognised exceptions.
  :--log: <single|multi>:  Set log file management option -- see "Single log" and "Multi-log" below.
  :--blfmode: <mode>:    Set mode for batch log file -- see log file modes
  :--blfms:            Set milli-second mode for naming batch log files (instead of second mode);
  :--flfmode: <mode>:  Set mode for file-level log file -- see log file modes
  :--aMap:             Read in some attribute mappings and run tests with virtual substitutions;

Log file modes
--------------

Valid modes are: 'a': append
                 'n', 'np': new file, 'np': protect after closing (mode = 444)
                 'w', 'wo': write (overwrite if present), 'wo': protect after closing (mode = 444)

Note that the log files generated in multi-log mode will re-use file names. If running with --flfmode set to 'n','np' or 'wo' it will be necessary to change or clear the target directory. The names of batch log files include the time, to the nearest second, when the process is started, so will not generally suffer from re-use.
"""

"""
ceda_cc -p <project> [-f <NetCDF file>|-d <directory containing files>|-D <root of directory tree>|-l <file list file>] [other options]

With the "-D" option, all files in the directory tree beneath the given directory will be checked. With the "-d" option, only files in the given directory will be checked.
"""
import sys, os, string, time, logging, glob
from ceda_cc_config import config_c4

class c4_init(object):

  def __init__(self,args=None):
    self.logByFile = True
    self.policyFileLogfileMode = 'w'
    self.policyBatchLogfileMode = 'np'
    self.policyBatchLogfileMs = False
    if args==None:
       args = sys.argv[1:]
    nn = 0

    self.attributeMappingFile = None
    self.recordFile = 'Rec.txt'
    self.logDir = 'logs_02'
    self.errs = []
    
    # Set default project to "CORDEX"
    self.project = "CORDEX"
    self.holdExceptions = False
    forceLogOrg = None
    argsIn = args[:]
   
    # Show help if no args or help requested
    if len(args) == 0 or args[0] in ('-h', '-help', '--help'):
       print __doc__
       raise SystemExit(0)	
    # The --copy-config option must be the first argument if it is present.
    elif args[0] == '--copy-config':
       if len(args) < 2:
         self.commandHints( argsIn )
       args.pop(0)
       dest_dir = args.pop(0)
       config_c4.copy_config(dest_dir)
       print 'Configuration directory copied to %s.  Set CC_CONFIG_DIR to use this configuration.' % dest_dir
       print
       raise SystemExit(0)

    self.summarymode = args[0] == '--sum'
    if self.summarymode:
      return

    self.experimental = False
    self.forceNetcdfLib = None
    self.getdrs = True
    fltype = None
    argu = []
    while len(args) > 0:
      next = args.pop(0)
      if next == '-f':
        flist = [args.pop(0),]
        self.logByFile = False
        fltype = '-f'
        self.source = flist[0]
      elif next == '--log':
        x = args.pop(0)
        assert x in ['single','multi','s','m'], 'unrecognised logging option (--log): %s' % (x)
        if x in ['multi','m']:
           forceLogOrg = 'multi'
        elif x in ['single','s']:
           forceLogOrg = 'single'
      elif next == '--experimental':
        self.experimental = True
      elif next == '--force-ncq':
        self.forceNetcdfLib = 'ncq3'
      elif next == '--force-cdms2':
        self.forceNetcdfLib = 'cdms2'
      elif next == '--force-pync4':
        self.forceNetcdfLib = 'netCDF4'
      elif next == '--nodrs':
        self.getdrs = False
      elif next == '--force-scientific':
        self.forceNetcdfLib = 'Scientific'
      elif next == '--flfmode':
        lfmk = args.pop(0)
        assert lfmk in ['a','n','np','w','wo'], 'Unrecognised file logfile mode (--flfmode): %s' % lfmk
        self.policyFileLogfileMode = lfmk
      elif next == '--blfmode':
        lfmk = args.pop(0)
        assert lfmk in ['a','n','np','w','wo'], 'Unrecognised batch logfile mode (--blfmode): %s' % lfmk
        self.policyBatchLogfileMode = lfmk
      elif next == '--blfms':
        self.policyBatchLogfileMs = False
      elif next == '-fl':
        flf = args.pop(0)
        flist = []
        for l in open( flf ).readlines():
          flist.append( l.strip() )
        self.source = flf  
      elif next == '-d':
        fdir = args.pop(0)
        flist = glob.glob( '%s/*.nc' % fdir  )
        self.source = '%s/*.nc' % fdir
      elif next == '-D':
        flist  = []
        fdir = args.pop(0)
        for root, dirs, files in os.walk( fdir, followlinks=True ):
          for f in files:
            fpath = '%s/%s' % (root,f)
            if (os.path.isfile( fpath ) or os.path.islink( fpath )) and f[-3:] == '.nc':
              flist.append( fpath )
        self.source = '%s/.....' % fdir
      elif next == '-l':
        flist = open(args.pop(0)).read().split()
        self.source = flist[0]
      elif next == '-R':
        self.recordFile = args.pop(0)
      elif next == '--ld':
        self.logDir = args.pop(0)
      elif next in ['--catchAllExceptions','--cae']:
        self.holdExceptions = True
      elif next == '--aMap':
        self.attributeMappingFile = args.pop(0)
        assert os.path.isfile( self.attributeMappingFile ), 'The token "--aMap" should be followed by the path or name of a file'
      elif next == "-p":
        self.project = args.pop(0)
      else:
       print 'Unused argument: %s' % next
       argu.append( next )
       nn+=1
    if nn != 0:
      print 'Unused arguments: ', argu
      self.commandHints( argsIn )

    if self.project == 'CMIP5' and fltype != '-f':
      fl0 = []
      for f in flist:
        if string.find( f, '/latest/' ) != -1:
          fl0.append(f)
      flist = fl0

    if forceLogOrg != None:
      if forceLogOrg == 'single':
        self.logByFile = False
      else:
        self.logByFile = True

    if self.project[:2] == '__':
       self.source = 'dummy'
       flist = []
       ss = 'abcdefgijk'
       ss = 'abcdefgijklmnopqrstuvwxyz'
       ss = 'abc'
       for i in range(10):
         v = 'v%s' % i
         for a in ss:
           for b in ss:
             flist.append( '%s_day_%s_%s_1900-1909.nc' % (v,a,b) )
    flist.sort()
    fnl = []
    for f in flist:
      fn = string.split(f, '/')[-1]
      fnl.append(fn)
    nd = 0
    dupl = []
    for k in range(len(fnl)-1):
      if fnl[k] == fnl[k-1]:
        nd += 1
        dupl.append( fnl[k] )
    self.dupDict = {}
    for f in dupl:
      self.dupDict[f] = 0
    if nd != 0:
      self.errs.append( 'Duplicate file names encountered: %s' % nd )
      self.errs.append( dupl )
    self.flist = flist
    self.fnl = fnl
    if not os.path.isdir(   self.logDir ):
       os.mkdir(   self.logDir )

    tstring1 = '%4.4i%2.2i%2.2i_%2.2i%2.2i%2.2i' % time.gmtime()[0:6]
    if self.policyBatchLogfileMs:
      t = time.time()
      ms = int( ( t-int(t) )*1000. )
      tsring1 += '.%3.3i' % ms
    self.batchLogfile = '%s/qcBatchLog_%s.txt' % (  self.logDir,tstring1)
## default appending to myapp.log; mode='w' forces a new file (deleting old contents).
    self.logger = logging.getLogger('c4logger')
    if self.policyBatchLogfileMode in ['n','np']:
        assert not os.path.isfile( self.batchLogfile ), '%s exists and policy set to new file' % self.batchLogfile
    m = self.policyBatchLogfileMode[0]
    if m == 'n':
      m = 'w'
    if m == 'a':
      self.hdlr = logging.FileHandler(self.batchLogfile)
    else:
      self.hdlr = logging.FileHandler(self.batchLogfile,mode=m)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    self.hdlr.setFormatter(formatter)
    self.logger.setLevel(logging.INFO)
    self.logger.addHandler(self.hdlr)

    self.attributeMappings = []
    self.attributeMappingsLog = None
    if self.attributeMappingFile != None:
      for l in open( self.attributeMappingFile ).readlines():
        if l[0] != '#':
          bb = string.split( string.strip(l), '|' ) 
          assert len(bb) ==2, "Error in experimental module attributeMapping -- configuration line not scanned [%s]" % str(l)
          bits = string.split( bb[0], ';' )
          cl = []
          for b in bits:
            cl.append( string.split(b, '=' ) )
          self.attributeMappings.append( ('am001',cl, string.split(bb[1],'=') ) )
      self.attributeMappingsLog = open( 'attributeMappingsLog.txt', 'w' )

  def commandHints(self, args):
    if args[0] in ['-h','--sum']:
      print 'Arguments look OK'
    elif args[0] == '--copy-config':
      print 'Usage [configuration copy]: ceda_cc --copy-config <target directory path>'
    else:
      if not( '-f' in args or '-d' in args or '-D' in args):
        print 'No file or target directory specified'
        print __doc__
    raise SystemExit(0)
   

  def getFileLog( self, fn, flf=None ):
    if flf == None:
      tstring2 = '%4.4i%2.2i%2.2i' % time.gmtime()[0:3]
      if fn in self.dupDict.keys():
        tag = '__%2.2i' % self.dupDict[fn]
        self.dupDict[fn] += 1
      else:
        tag = ''
      self.fileLogfile = '%s/%s%s__qclog_%s.txt' % (self.logDir,fn[:-3],tag,tstring2)
      if self.policyFileLogfileMode in ['n','np']:
        assert not os.path.isfile( self.fileLogfile ), '%s exists and policy set to new file' % self.fileLogfile
      m = self.policyFileLogfileMode[0]
      if m == 'n':
        m = 'w'
    else:
      m = 'a'
      self.fileLogfile = flf

    self.fLogger = logging.getLogger('fileLog_%s_%s' % (fn,m))
    if m == 'a':
      self.fHdlr = logging.FileHandler(self.fileLogfile)
    else:
      self.fHdlr = logging.FileHandler(self.fileLogfile,mode=m)
    fileFormatter = logging.Formatter('%(message)s')
    self.fHdlr.setFormatter(fileFormatter)
    self.fLogger.addHandler(self.fHdlr)
    self.fLogger.setLevel(logging.INFO)
    return self.fLogger

  def closeFileLog(self):
    self.fLogger.removeHandler(self.fHdlr)
    self.fHdlr.close()
    if self.policyFileLogfileMode in ['wo','np']:
      os.popen( 'chmod %s %s;' % (444, self.fileLogfile) )

  def closeBatchLog(self):
    self.logger.removeHandler(self.hdlr)
    self.hdlr.close()
    if self.policyBatchLogfileMode in ['wo','np']:
      os.popen( 'chmod %s %s;' % (444, self.batchLogfile) )
