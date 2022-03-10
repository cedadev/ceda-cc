"""config_c4
##########
USAGE:
import config_c4

This module sets some basic variables, including some vocabulary lists.
"""
from . import utils_config as utils
import os
import os.path as op
import shutil, collections
import numpy
##from versionConfig import version, versionComment

NT_project = collections.namedtuple( 'project', ['id','v'] )
NT_fnParts = collections.namedtuple( 'fnParts', ['len','fxLen','unfLen','checkTLen','ixDomain','ixFreq'] )

##############################################################################
# Configure config-file paths
#
# All configuration directories, e.g. cmip5_vocabs, are looked for in a single
# parent directory.  This is the "config" directory within the package unless 
# the environment variable CC_CONFIG_DIR is set.

HERE = op.dirname(__file__)
CC_CONFIG_DEFAULT_DIR = op.join(HERE, 'config')
CC_CONFIG_DIR = os.environ.get('CC_CONFIG_DIR', CC_CONFIG_DEFAULT_DIR)

##############################################################################

validCmip5Experiments = ['1pctCO2', 'abrupt4xCO2', 'amip', 'amip4K', 'amip4xCO2', 'amipFuture', 'aqua4K', 'aqua4xCO2', 'aquaControl', 'decadal1959', 'decadal1960', 'decadal1961', 'decadal1962', 'decadal1963', 'decadal1964', 'decadal1965', 'decadal1966', 'decadal1967', 'decadal1968', 'decadal1969', 'decadal1970', 'decadal1971', 'decadal1972', 'decadal1973', 'decadal1974', 'decadal1975', 'decadal1976', 'decadal1977', 'decadal1978', 'decadal1979', 'decadal1980', 'decadal1981', 'decadal1982', 'decadal1983', 'decadal1984', 'decadal1985', 'decadal1986', 'decadal1987', 'decadal1988', 'decadal1989', 'decadal1990', 'decadal1991', 'decadal1992', 'decadal1993', 'decadal1994', 'decadal1995', 'decadal1996', 'decadal1997', 'decadal1998', 'decadal1999', 'decadal2000', 'decadal2001', 'decadal2002', 'decadal2003', 'decadal2004', 'decadal2005', 'decadal2006', 'decadal2007', 'decadal2008', 'decadal2009', 'decadal2010', 'decadal2011', 'decadal2012', 'esmControl', 'esmFdbk1', 'esmFdbk2', 'esmFixClim1', 'esmFixClim2', 'esmHistorical', 'esmrcp85', 'historical', 'historicalExt', 'historicalGHG', 'historicalMisc', 'historicalNat', 'lgm', 'midHolocene', 'noVolc1960', 'noVolc1965', 'noVolc1970', 'noVolc1975', 'noVolc1980', 'noVolc1985', 'noVolc1990', 'noVolc1995', 'noVolc2000', 'noVolc2005', 'past1000', 'piControl', 'rcp26', 'rcp45', 'rcp60', 'rcp85', 'sst2020', 'sst2030', 'sst2090', 'sst2090rcp45', 'sstClim', 'sstClim4xCO2', 'sstClimAerosol', 'sstClimSulfate', 'volcIn2010']

validCordexExperiment = validCmip5Experiments + ['evaluation']


validCmip5Frequencies = ['fx','yr','monClim','mon','day','6hr','3hr','subhr']
validCordexFrequencies = ['fx','sem','mon','day','6hr','3hr','1hr']
validSpecsFrequencies = ['fx','mon','day','6hr']
validCcmiFrequencies = ['fx','yr','mon','day','hr','subhr']
validSpecsExptFamilies = [x.strip( ) for x in open( op.join(CC_CONFIG_DIR, 'specs_vocabs/exptFamily.txt' )).readlines()]

validCordexDomainsL = [ 'SAM-44', 'CAM-44', 'NAM-44', 'EUR-44', 'AFR-44', 'WAS-44', 'EAS-44', 'CAS-44', 'AUS-44', 'ANT-44', 'ARC-44', 'MED-44']
validCordexDomainsLi = [x + 'i' for x in validCordexDomainsL]
validCordexDomainsH = ['EUR-11']
validCordexDomains = validCordexDomainsL + validCordexDomainsLi + validCordexDomainsH

plevRequired = ['clh', 'clm', 'cll', 'ua850', 'va850', 'ta850', 'hus850', 'ua500', 'va500', 'ta500', 'zg500', 'ua200', 'va200', 'ta200', 'zg200']
plevBndsRequired = ['clh', 'clm', 'cll']
heightRequired = ['tas','tasmax','tasmin','huss','sfcWind','sfcWindmax','wsgsmax','uas','vas']


ii = open( op.join(CC_CONFIG_DIR, 'cordex_vocabs/GCMModelName.txt' )).readlines()
validGcmNames = []
for l in ii:
  if l[0] != '#' and len( l.strip() ) > 0:
    validGcmNames.append( l.split()[0] )

ii = open( op.join(CC_CONFIG_DIR, 'cordex_vocabs/RCMModelName.txt' )).readlines()
validRcmNames = []
validInstNames = []
for l in ii:
  if l[0] != '#' and len( l.strip() ) > 0:
    bits = l.split()
    validRcmNames.append( bits[0] )
    validInstNames.append( bits[1] )

plevValues = {'clh':22000, 'clm':56000, 'cll':84000}
for i in [200,500,850]:
  for v in ['zg','ua', 'va', 'ta', 'hus']:
    k = '%s%s' % (v,i)
    plevValues[k] = i*100

heightRequired = ['tas', 'tasmax', 'tasmin', 'huss', 'sfcWind', 'sfcWindmax', 'wsgsmax', 'uas', 'vas']
heightValues = {}
heightRange = {}
for v in heightRequired:
  if v in ['tas', 'tasmax', 'tasmin', 'huss']:
    heightValues[v] = 2
  else:
    heightValues[v] = 10
  heightRange[v] = (1.5,10.)

ii = open( op.join(CC_CONFIG_DIR, 'cordex_vocabs/cordex_domains.csv' )).readlines()
keys = ['name','tag','res','grid_np_lon','grid_np_lat','nlon','nlat','w','e','s','n']
rotatedPoleGrids = {}
for l in ii[2:16]:
  bits = l.strip().split(',')
  ee = {}
  i = 0
  for k in keys:
    if k in ['nlon','nlat']:
      ee[k] = int(bits[i])
    elif k in ['grid_np_lon','grid_np_lat','w','e','s','n','res']:
      if bits[i] != 'N/A':
        ee[k] = float(bits[i])
      else:
        ee[k] = bits[i]
    else:
      ee[k] = bits[i]
    i += 1
    rotatedPoleGrids[bits[1]] = ee

##Area,Name, deg,Nlon,Nlat,West8,East8,South8,North8,
keys = ['name','tag','res','nlon','nlat','w','e','s','n']
interpolatedGrids = {}
for l in ii[18:33]:
  bits = l.strip().split(',')
  ee = {}
  i = 0
  for k in keys:
    if k in ['nlon','nlat']:
      ee[k] = int(bits[i])
    elif k in ['w','e','s','n','res']:
        ee[k] = float(bits[i])
    else:
      ee[k] = bits[i]
    i += 1
    interpolatedGrids[bits[1]] = ee

class readVocab(object):
  """readVocab:
  A general class to read in vocabulary lists ("code lists" in ISO 19115 terminology) from a variety of structured text files.
  """

  def __init__(self,dir):
    self.dir = dir

  def driver(self,tt):
    if tt[0] == "simpleList":
      tx = tt + (None,None,None,None)
      return self.getSimpleList( tx[1],bit=tx[2],omt=tx[3],options=tx[4] )
    else:
      print('readVocab.driver: option %s not recgnised' % tt[0])

  def getEvalAssign(self, file ):
    ii = open('%s/%s/%s' % (CC_CONFIG_DIR, self.dir,file) )
    ll = []
    for l in ii.readlines():
      if l[0] != '#':
        ll.append( l )
    assert len(ll) == 1, 'Too many lines in %s' % file 
    try:
      return eval( ll[0] )
    except:
      print('Failed to evaluate configuration line from %s:\n%s' % (file,l[0]))
      raise

  def getSimpleList(self,file,bit=None,omt=None,options=None):
    ii = open('%s/%s/%s' % (CC_CONFIG_DIR, self.dir,file) )
    oo = []
    if options == None:
      olist = []
    else:
      olist = options.split(',')

    if 'returnMappings' in olist:
      assert bit in [0, -1], 'only support returnMappings for bit = -1 or 0'
      ee = {}

    for l in ii.readlines():
      if l[0] != '#':
        ll = l.strip()
        if omt == 'last':
          oo.append(' '.join(ll.split()[:-1]))
        elif bit == None:
          oo.append(ll)
        else:
          if 'returnMappings' in olist:
            bb = ll.split()
            if bit == -1:
              ee[bb[-1]] = ' '.join( bb[:-1] )
            else:
              ee[bb[0]] = ' '.join( bb[1:] )
            oo.append( bb[bit] )
          else:
            oo.append(ll.split()[bit])

    if 'noneMap' in olist:
      oo = [{'None':None}.get(x,x) for x in oo]

    if 'returnMappings' in olist:
      return oo, ee
    else:
      return oo

validSpecsInstitutions = ['IC3', 'MPI-M', 'KNMI', 'UOXF', 'CNRM-CERFACS', 'ENEA', 'MOHC', 'SMHI', 'IPSL', 'UREAD', 'ECWMF']

class ProjectConfig(object):
  """projectConfig:
  Set project specific configuration options.
  
  USAGE:
  
  pcfg = projectConfig( <project id>[, version=..] )

  Creates a "pcfg" object which contains attributes used in the code, including vocabulary lists.
  """

  def __init__(self, project, version=-1):
    knownProjects = ['CMIP5','snapsi','ccmi2022','CCMI','CORDEX','SPECS','ESA-CCI', '__dummy']
    assert project in knownProjects, 'Project %s not in knownProjects %s' % (project, str(knownProjects))

    self.project = project
    self.fNameSep = '_'
    self.varIndex = 0
    self.fnvdict = None
    self.varTables='CMIP'
    self.varTableFlavour='def'
    self.checkVarType = True
    self.projectV = NT_project(project,version)
    self.gridSpecTol = 0.01
## default encoding of time range in file names: YYYY[MM[DD[HH]]]-YYYY[MM[DD[HH]]]
    self.trangeType = 'CMIP'
    self.controlledFnParts = []
    if project == 'CORDEX':
      self.requiredGlobalAttributes = [ 'institute_id', 'contact', 'rcm_version_id', 'product', 'CORDEX_domain', 'creation_date', \
             'frequency', 'model_id', 'driving_model_id', 'driving_experiment', 'driving_model_ensemble_member', 'experiment_id']
      self.controlledGlobalAttributes = ['frequency', 'driving_experiment_name', 'project_id', 'CORDEX_domain', 'driving_model_id', 'model_id', 'institute_id','driving_model_ensemble_member','rcm_version_id']
      self.globalAttributesInFn = [None,'CORDEX_domain','driving_model_id','experiment_id','driving_model_ensemble_member','model_id','rcm_version_id']
      self.requiredVarAttributes = ['long_name', 'standard_name', 'units']
      self.drsMappings = {'variable':'@var','institute':'institute_id', 'product':'product', 'experiment':'experiment_id', \
                        'ensemble':'driving_model_ensemble_member', 'model':'model_id', 'driving_model':'driving_model_id', \
                        'frequency':'frequency', \
                        'project':'project_id', 'domain':'CORDEX_domain', 'model_version':'rcm_version_id' }

    elif project == 'SPECS':
      lrdr = readVocab( 'specs_vocabs/')
      self.requiredGlobalAttributes = lrdr.driver( ('simpleList', 'globalAts.txt' ) )
      self.exptFamilies = lrdr.driver( ('simpleList', 'exptFamily.txt', 0 ) )
      self.validInstitutions = lrdr.driver( ('simpleList', 'validInstitutions_sv0101.txt' ) )
      self.realm = lrdr.driver( ('simpleList', 'realm_sv0101.txt' ) )
      self.controlledGlobalAttributes = lrdr.driver( ('simpleList', 'controlledGlobalAttributes_sv0101.txt' ) )
                       ##'initialization_method','physics_version','realization']
      self.globalAttributesInFn = lrdr.driver( ('simpleList', 'globalAttributesInFn_sv0101.txt',None,None,'noneMap' ) )
      self.requiredVarAttributes = ['long_name', 'standard_name', 'units']
      oo, self.drsMappings = lrdr.driver( ('simpleList', 'drsMappings_sv0101.txt',0,None,'returnMappings' ) )

      ##self.drsMappings = {'variable':'@var', 'institute':'institute_id', 'product':'product', 'experiment':'experiment_id', \
                        ##'ensemble':'@ensemble', 'model':'model_id', 'realm':'modeling_realm', \
                        ##'frequency':'frequency', 'start_date':'@forecast_reference_time', \
                        ##'table':'@mip_id',
                        ##'project':'project_id'}

    elif project == 'CMIP5':
      lrdr = readVocab( 'cmip5_vocabs/')
      self.requiredGlobalAttributes = [ 'contact', 'product', 'creation_date', 'tracking_id', \
              'experiment_id']
      ##self.requiredGlobalAttributes = lrdr.getSimpleList( 'globalAts.txt' )
      self.controlledGlobalAttributes = [ 'project_id','experiment_id', 'frequency','Conventions','modeling_realm', \
                       'initialization_method','physics_version','realization']
      self.globalAttributesInFn = [None,'@mip_id','model_id','experiment_id','@ensemble']
#sic_Oimon_EC-Earth2_seaIceBestInit_S19910501_series1_r1i1p1_199501-199502.nc 
## mip_id derived from global attribute Table_id (CMOR convention); experiment family derived from experiment_id, ensemble derived from rip attributes.
      self.requiredVarAttributes = ['long_name', 'standard_name', 'units']
## key: DRS element name, value: global attribute name or tag for mapping from file information ("@....").
      self.drsMappings = {'variable':'@var', 'institute':'institute_id', 'product':'product', 'experiment':'experiment_id', \
                        'ensemble':'@ensemble', 'model':'model_id', 'realm':'modeling_realm', \
                        'frequency':'frequency',  'table':'@mip_id',
                        'project':'project_id'}

    elif project == 'CCMI':
      lrdr = readVocab( 'ccmi_vocabs/')
      self.requiredGlobalAttributes = [ 'creation_date', 'tracking_id', 'forcing', 'model_id', 'parent_experiment_id', 'parent_experiment_rip', 'branch_time', 'contact', 'institute_id' ]
      self.requiredGlobalAttributes = lrdr.getSimpleList( 'globalAts.txt', bit=0 )
      self.controlledGlobalAttributes = [ 'experiment_id', 'project', 'frequency' ]
      self.globalAttributesInFn = [None,'@mip_id','model_id','experiment_id','@ensemble']
      self.requiredVarAttributes = ['long_name', 'units']
      self.drsMappings = {'variable':'@var', 'institute':'institute_id', 'product':'product', 'experiment':'experiment_id', \
                        'ensemble':'@ensemble', 'model':'model_id', 'realm':'modeling_realm', \
                        'frequency':'frequency',  'table':'@mip_id',
                        'project':'project_id'}

    elif project in [ 'ccmi2022', 'snapsi']:
      import ceda_cc.ceda_cc_config.config.table_imports as ti
      self.varTableFlavour='json_ccmi'
      self.thiscfg = ti.Ingest_cmipplus(project)
      self.requiredGlobalAttributes = self.thiscfg.required[:]
      variant_ixs = ['realization', 'initialization', 'physics', 'forcing']
      self.controlledGlobalAttributes = sorted( [ x for x,i in self.thiscfg.acvs.items() if i[0] == 'list' ] ) + \
                              ['%s_index' % x for x in variant_ixs]
      if project == 'ccmi2022':
        self.globalAttributesInFn = [None,'table_id','source_id','experiment_id','variant_label','grid_label','@variant:4:']
                  ##### o3_Amon_CMAM_refD1_r1i1p1f1_gn_196001-201812.nc
      elif project == 'snapsi':
        self.globalAttributesInFn = [None,'table_id','source_id','experiment_id',None,'grid_label','@variant:4:']
      ##ch4_Amon_SOCOL_refD1_gn_r1i1p1f1_196001-201812.nc
      self.requiredVarAttributes = ['long_name', 'units', 'standard_name']
      self.drsMappings = {'variable':'@var', 'institution_id':'institution_id', 'experiment_id':'experiment_id', \
                        'variant_label':'variant_label', 'source_id':'source_id', 'realm':'realm', \
                        'frequency':'frequency',  'table_id':'table_id', 'mip_era':'mip_era','frequency':'frequency',
                        'activity_id':'activity_id'
                        }

    elif project == 'ESA-CCI':
      lrdr = readVocab( 'esacci_vocabs/')
      self.varTables='FLAT'
      self.fNameSep = '-'
      self.checkVarType = False
      self.requiredGlobalAttributes = lrdr.getSimpleList( 'requiredGlobalAts.txt', bit=0 )
      self.controlledGlobalAttributes = ['platform','sensor','project','Conventions','institution','cdm_data_type','time_coverage_duration','spatial_resolution' ]
      self.controlledFnParts = ['level','cciProject','var','version']
      self.requiredVarAttributes = ['long_name', 'standard_name', 'units']
      self.drsMappings = {'variable':'#var','platform':'platform','sensor':'sensor','level':'#level', \
                'standard_name':'*standard_name', \
                'activity':'=CLIPC', \
                'algorithm':'$algorithm:unset', 'frequency':'$frequency', \
                'spatial_resolution':'spatial_resolution', 'ecv':'@ecv','version':'#version','convention_version':'#gdsv'}
      self.globalAttributesInFn = [None,]
    elif project == '__dummy':
      self.requiredGlobalAttributes = ['ga%s' % x for x in range(10)]
      self.controlledGlobalAttributes = [ ]
      self.globalAttributesInFn = [None,'ga2', 'ga3', 'ga4' ]
      self.requiredVarAttributes = ['long_name', 'standard_name', 'units']
      self.drsMappings = {'variable':'@var'}

# # used in checkStandardDims

    self.plevRequired = plevRequired
    self.plevValues = plevValues
    self.heightRequired = heightRequired
    self.heightValues = heightValues
    self.heightRange = heightRange

# # used in checkGrids
    self.rotatedPoleGrids = rotatedPoleGrids
    self.interpolatedGrids = interpolatedGrids
    self.doCheckGrids = self.projectV.id in ['CORDEX',]

# # used in checkFileName (freqIndex also used in checkByVar)

    if self.projectV.id == 'CORDEX':
      self.fnParts = NT_fnParts( len=[8,9], fxLen=[8,],  unfLen=[9,], checkTLen=True, ixDomain=1, ixFreq=7 )
    elif self.projectV.id == 'CMIP5':
      self.fnParts = NT_fnParts( len=[5,6], fxLen=[5,],  unfLen=[6,], checkTLen=False, ixDomain=None, ixFreq=None )
    elif self.projectV.id == 'SPECS':
      self.fnParts = lrdr.getEvalAssign( 'fnParts_sv0101.txt' )
    elif self.projectV.id == 'CCMI':
      self.fnParts = NT_fnParts( len=[5,6], fxLen=[5,],  unfLen=[6,], checkTLen=False, ixDomain=None, ixFreq=None )
    elif self.projectV.id in ['ccmi2022']:
        # ch4_Amon_SOCOL_refD1_gn_r1i1p1f1_196001-201812.nc
      self.fnParts = NT_fnParts( len=[6,7], fxLen=[6,],  unfLen=[7,], checkTLen=False, ixDomain=None, ixFreq=None )
    elif self.projectV.id in ['snapsi']:
         # epfy_6hrPtZ_CESM2-CAM6_free_s20180125_r10i1p1f1_gn_20180125-20180310.nc
       self.fnParts = NT_fnParts( len=[7,8], fxLen=[7,],  unfLen=[8,], checkTLen=False, ixDomain=None, ixFreq=None )
    elif self.projectV.id == 'ESA-CCI':
      self.fnParts = NT_fnParts( len=[7,8,9], fxLen=[0,],  unfLen=[7,8,9,], checkTLen=False, ixDomain=None, ixFreq=None )
      self.trangeType = 'ESA-CCI'
    elif self.projectV.id == '__dummy':
      self.fnParts = NT_fnParts( len=[4,5], fxLen=[4,],  unfLen=[5,], checkTLen=False, ixDomain=None, ixFreq=1 )

    self.fnPartsOkLen = self.fnParts.len
    self.fnPartsOkFixedLen = self.fnParts.fxLen
    self.fnPartsOkUnfixedLen = self.fnParts.unfLen
    self.checkTrangeLen = self.fnParts.checkTLen
    self.domainIndex = self.fnParts.ixDomain
    self.freqIndex = self.fnParts.ixFreq


    self.defaults = { 'variableDataType':'float' }
# ## used in mipVocabs
    self.legacy = True
    if self.projectV.id == 'CORDEX':
       self.mipVocabDir = op.join(CC_CONFIG_DIR, 'cordex_vocabs/mip/')
       self.mipVocabTl = ['fx','sem','mon','day','6h','3h','1h']
       self.mipVocabVgmap = {'6h':'6hr','3h':'3hr', '1h':'1hr'}
       self.mipVocabFnpat = 'CORDEX_%s'
    elif self.projectV.id == 'CMIP5':
       self.mipVocabDir = op.join(CC_CONFIG_DIR, 'cmip5_vocabs/mip/')
       self.mipVocabTl = ['fx','Oyr','Oclim','Omon','Amon','Lmon','LImon','OImon','cfMon','aero','cfDay','day','cfOff','cfSites','6hrLev','6hrPlev','3hr','cf3hr']
       self.mipVocabVgmap = {}
       self.mipVocabFnpat = 'CMIP5_%s'
       self.defaults['variableDataType'] = None 
    elif self.projectV.id == 'SPECS':
       self.mipVocabDir = op.join(CC_CONFIG_DIR, 'specs_vocabs/mip/')
       self.mipVocabTl = ['fx','Omon','Amon','Lmon','OImon','day','6hr']
       self.mipVocabVgmap = {}
       self.mipVocabFnpat = 'SPECS_%s'
    elif self.projectV.id == 'CCMI':
       self.mipVocabDir = op.join(CC_CONFIG_DIR, 'ccmi_vocabs/mip/')
       self.mipVocabTl = ['fixed','annual','monthly','daily','hourly','satdaily']
       self.mipVocabVgmap = {'fixed':'fx','annual':'yr','monthly':'mon','daily':'day','hourly':'hr','satdaily':'day'}
       self.mipVocabFnpat = 'CCMI1_%s'
    elif self.projectV.id in ['snapsi','ccmi2022']:
       self.legacy = False
       self.mipVocabDir = op.join(CC_CONFIG_DIR, '%s/Tables/' % project)
       self.mipVocabTl = self.thiscfg.acvs['table_id'][1]
       self.mipVocabVgmap = {}
       self.mipVocabFnpat =  project.upper() + '_%s.json'
    elif self.projectV.id == 'ESA-CCI':
       self.mipVocabDir = op.join(CC_CONFIG_DIR, 'esacci_vocabs/')
       self.mipVocabTl = []
       self.mipVocabVgmap = { 'ESACCI':'ESACCI' }
       self.mipVocabFnpat = 'variableInFile.txt'
    else:
       self.mipVocabDir = None
       self.mipVocabTl = ['day', 't2']
       self.mipVocabVgmap = {}
       self.mipVocabFnpat = None
    self.mipVocabPars = [self.mipVocabDir, self.mipVocabTl, self.mipVocabVgmap, self.mipVocabFnpat]

# ## used in checkByVar
    if self.project == 'CORDEX':
      self.groupIndex = 7
    elif self.project in ['CMIP5','CCMI','ccmi2022','snapsi','SPECS','__dummy']:
      self.groupIndex = 1
    elif self.project in ['ESA-CCI']:
      self.fnvdict = { 'SSTskin':{'v':'sea_surface_temperature', 'sn':'sea_surface_skin_temperature'} }
      self.fnoptions = {'groupIndex':[1,0], 'trangeIndex':[0,-2] }
      self.fnoptions['inFn'] = [[None,'*activity','*level','*project','*var','*product','*additional','*gdsv','*version'],
                                ['*activity','*project','*level','*var','*additional',None,'*version']]
      self.fnoptions['varIndex'] = [4,3]
##Indicative Date>[<Indicative Time>]-ESACCI-<Processing Level>_<CCI Project>-<Data Type>-<Product String>[- <Additional Segregator>][-v<GDS version>]-fv<File version>.nc
##ESACCI-<CCI Project>-<Processing Level>-<Data Type>-<Product String>[-<Additional Segregator>]-<IndicativeDate>[<Indicative Time>]-fv<File version>.nc

    self.trangeIndex = -1

    self.getVocabs()
    test = False
    if test:
      for k in list(self.vocabs['variable'].varcons.keys()):
        for k2 in list(self.vocabs['variable'].varcons[k].keys()):
          if "height2m" in self.vocabs['variable'].varcons[k][k2].get( '_dimension',[]):
            print('config_c4: %s , %s: %s' % (k,k2,str(self.vocabs['variable'].varcons[k][k2]['_dimension'] ) ))

    ##assert self.project != 'CCMI', 'Not completely set up for CCMI yet'

  def getExtraAtts(self):

    eafile = self.mipVocabDir + 'extraAtts.txt'
    self.extraAtts = {}
    if os.path.isfile( eafile ):
      for l in open( eafile ).readlines():
        if l[0] != '#':
          if l[0] == "@":
              p1,p2 = l[1:].split( '|' )
          else:
            p1,p2 = None, l
          ##bits = list(map( string.strip, string.split(p2,',') ))
          bits = [x.strip() for x in p2.split( ',' )]
          id = '%s.%s' % (bits[0],bits[1])
          if p1 != None:
            id += ':%s' % p1
          ee = {}
          for b in bits[2:]:
            bb = b.split('=')
            ee[bb[0]] = bb[1]
          self.extraAtts[id] = ee

  def getVocabs(self):
  ## "Returns a dictionary of vocabulary details for the project provided."
    if self.projectV.id == 'SPECS':
               ##'experiment_id':utils.PatternControl( 'experiment_id', "(?P<val>.*)[0-9]{4}", list=validSpecsExptFamilies ), \
      vocabs = { 'variable':utils.mipVocab(self), \
               'Conventions':utils.ListControl( 'Conventions', ['CF-1.6'] ), \
               'frequency':utils.ListControl( 'frequency', validSpecsFrequencies ), \
               'experiment_id':utils.ListControl( 'experiment_id', validSpecsExptFamilies ), \
               'initialization_method':utils.PatternControl( 'initialization_method', "[0-9]+" ), \
               'physics_version':utils.PatternControl( 'physics_version', "[0-9]+" ), \
               'realization':utils.PatternControl( 'realization', "[0-9]+" ), \
               'startdate':utils.PatternControl( 'startdate', "S[0-9]{8}" ), \
               ## 'associated_experiment':utils.PatternControl( 'associated_experment', "(?P<val>(N/A|(decadal|seasonal): r\*i[0-9]{1,4}p[0-9]{1,4}))" ), \
               'project_id':utils.ListControl( 'project_id', ['SPECS', 'NMME-SPECS'] ), \
               ## 'institution':utils.ListControl( 'institution', validSpecsInstitutions ), \
               'modeling_realm':utils.ListControl( 'realm', self.realm, split=True ), \
             }
    elif self.projectV.id == 'CMIP5':
               ##'experiment_id':utils.PatternControl( 'experiment_id', "(?P<val>.*)[0-9]{4}", list=validSpecsExptFamilies ), \
      lrdr = readVocab( 'cmip5_vocabs/')
      vocabs = { 'variable':utils.mipVocab(self), \
               'Conventions':utils.ListControl( 'Conventions', ['CF-1.4','CF-1.5'] ), \
               'experiment_id':utils.ListControl( 'experiment_id', lrdr.getSimpleList( 'experiments.txt' ) ), \
               'institute_id':utils.ListControl( 'institute_id', lrdr.getSimpleList( 'institutes.txt' ) ), \
               'model_id':utils.ListControl( 'model_id', lrdr.getSimpleList( 'models.txt' ) ), \
               'frequency':utils.ListControl( 'frequency', validCmip5Frequencies ), \
               'initialization_method':utils.PatternControl( 'initialization_method', "[0-9]+" ), \
               'physics_version':utils.PatternControl( 'physics_version', "[0-9]+" ), \
               'realization':utils.PatternControl( 'realization', "[0-9]+" ), \
               'project_id':utils.ListControl( 'project_id', ['CMIP5'] ), \
               ## 'institution':utils.ListControl( 'institution', validSpecsInstitutions ), \
               'modeling_realm':utils.ListControl( 'realm', ['atmos', 'ocean', 'land', 'landIce', 'seaIce', 'aerosol', 'atmosChem', 'ocnBgchem'], split=True ), \
             }
    elif self.projectV.id == 'CCMI':
    
      lrdr = readVocab( 'ccmi_vocabs/')
      vocabs = { 'variable':utils.mipVocab(self), \
               'frequency':utils.ListControl( 'frequency', validCcmiFrequencies ), \
               'experiment_id':utils.ListControl( 'experiment_id', lrdr.getSimpleList( 'ccmi_experiments.txt', bit=-1 ) ), \
## do not preserve or check relation between model and institution.
               'institution':utils.ListControl( 'institution', lrdr.getSimpleList( 'models_insts.txt', bit=1 ) ), \
               'model_id':utils.ListControl( 'model_id', lrdr.getSimpleList( 'models_insts.txt', bit=0 ) ), \
               'modeling_realm':utils.ListControl( 'realm', ['atmos', 'ocean', 'land', 'landIce', 'seaIce', 'aerosol', 'atmosChem', 'ocnBgchem'] ), \
               'project_id':utils.ListControl( 'project_id', ['CCMI'] ) }

    elif self.projectV.id in ['snapsi', 'ccmi2022']:
    
      vocabs = dict()
      for k,i in self.thiscfg.acvs.items():
          if i[0] == 'list':
              vocabs[k] = utils.ListControl( k, i[1], split= k in ['source_type'] )
      vocabs[ 'variable' ] = utils.mipVocab(self)
      variant_ixs = ['realization', 'initialization', 'physics', 'forcing']
      for x in variant_ixs:
        vocabs[ '%s_index' % x ] = utils.NumericControl( '%s_index' % x, base_class=(int, numpy.integer), min_valid=0 )

    elif self.projectV.id == 'ESA-CCI':
      lrdr = readVocab( 'esacci_vocabs/')
      cciProjectList, self.ecvMappings = lrdr.getSimpleList( 'cciProject.txt', bit=-1, options='returnMappings' )
      vocabs = { 'variable':utils.mipVocab(self), \
               'version':utils.PatternControl( 'version',  '^(fv[0-9]+(\.[0-9]+){0,1})$', examples=['fv1.1'] ), \
               'level':utils.ListControl( 'level', lrdr.getSimpleList( 'procLevel01.txt', bit=0 ) ), \
               'platform':utils.ListControl( 'platforms', lrdr.getSimpleList( 'platforms.txt', bit=0), enumeration=True, split=True, splitVal=',' ), \
               'institution':utils.ListControl( 'institution', lrdr.getSimpleList( 'institutions.txt', omt='last' ) ), \
               'Conventions':utils.PatternControl( 'Conventions', '^CF-1.[56789](,.*){0,1}$', examples=['CF-1.6'] ), \
               'sensor':utils.ListControl( 'sensors', lrdr.getSimpleList( 'sensors.txt', bit=0 ), enumeration=True, split=True, splitVal=',' ), \
               'cdm_data_type':utils.ListControl( 'cdm_data_type', lrdr.getSimpleList( 'threddsDataType.txt', bit=0 ) ), \
               'time_coverage_duration':utils.PatternControl( 'time_coverage_duration',  'ISO8601 duration', cls='ISO',examples=['P1Y'] ), \
               'spatial_resolution':utils.PatternControl( 'spatial_resolution',  '([0-9]+(.[0-9]+){0,1})[\s]*(km|m|degree).*', examples=['20km','1 km at nadir'] ), \
               'project':utils.ListControl( 'project', ['Climate Change Initiative - European Space Agency','CLIPC','ESA GlobSnow-2'] ), \
               'cciProject':utils.ListControl( 'cciproject', cciProjectList ), \
               'var':utils.ListControl( 'var', lrdr.getSimpleList( 'variables.txt', bit=-1 ) ) \
             }
    elif self.projectV.id == '__dummy':
      vocabs = { 'variable':utils.mipVocab(self,dummy=True) }
    else:
      vocabs = { 'variable':utils.mipVocab(self), \
           'driving_experiment_name':utils.ListControl( 'driving_experiment_name', validCordexExperiment ), \
           'project_id':utils.ListControl( 'project_id', ['CORDEX'] ), \
           'CORDEX_domain':utils.ListControl( 'CORDEX_domain',  validCordexDomains ), \
           'driving_model_id':utils.ListControl( 'driving_model_id',  validGcmNames ), \
           'driving_model_ensemble_member':utils.PatternControl( 'driving_model_ensemble_member',  'r[0-9]+i[0-9]+p[0-9]+' ), \
           'rcm_version_id':utils.PatternControl( 'rcm_version_id',  '[a-zA-Z0-9-]+' ), \
           'model_id':utils.ListControl( 'model_id',  validRcmNames ), \
           'institute_id':utils.ListControl( 'institute_id',  validInstNames ), \
           'frequency':utils.ListControl( 'frequency', validCordexFrequencies ) }

    self.vocabs = vocabs


  def setEsaCciFNType(self,id):
      if id in [1,2]:
        id1 = 1
      else:
        id1 = id
      self.groupIndex =  self.fnoptions['groupIndex'][id1]
      self.trangeIndex = self.fnoptions['trangeIndex'][id1]
      self.globalAttributesInFn = self.fnoptions['inFn'][id1]
      self.varIndex = self.fnoptions['varIndex'][id1]


def copy_config(dest_dir):
   """
   Copy the current default configuration directory into a separate directory.

   The directory <ceda_cc-package-dir>/config is copied to `dest_dir`.
   This is useful when ceda-cc is installed as a Python package and the user may
   not know where the config directory is stored.

   :param dest_dir: should be a path to a directory which does not yet exist.  
       The configuration directory will be copied to this path.

   """
   shutil.copytree(CC_CONFIG_DEFAULT_DIR, dest_dir)
