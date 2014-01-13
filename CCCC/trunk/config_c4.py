import string
import utils_c4 as utils

validCmip5Experiments = ['1pctCO2', 'abrupt4xCO2', 'amip', 'amip4K', 'amip4xCO2', 'amipFuture', 'aqua4K', 'aqua4xCO2', 'aquaControl', 'decadal1959', 'decadal1960', 'decadal1961', 'decadal1962', 'decadal1963', 'decadal1964', 'decadal1965', 'decadal1966', 'decadal1967', 'decadal1968', 'decadal1969', 'decadal1970', 'decadal1971', 'decadal1972', 'decadal1973', 'decadal1974', 'decadal1975', 'decadal1976', 'decadal1977', 'decadal1978', 'decadal1979', 'decadal1980', 'decadal1981', 'decadal1982', 'decadal1983', 'decadal1984', 'decadal1985', 'decadal1986', 'decadal1987', 'decadal1988', 'decadal1989', 'decadal1990', 'decadal1991', 'decadal1992', 'decadal1993', 'decadal1994', 'decadal1995', 'decadal1996', 'decadal1997', 'decadal1998', 'decadal1999', 'decadal2000', 'decadal2001', 'decadal2002', 'decadal2003', 'decadal2004', 'decadal2005', 'decadal2006', 'decadal2007', 'decadal2008', 'decadal2009', 'decadal2010', 'decadal2011', 'decadal2012', 'esmControl', 'esmFdbk1', 'esmFdbk2', 'esmFixClim1', 'esmFixClim2', 'esmHistorical', 'esmrcp85', 'historical', 'historicalExt', 'historicalGHG', 'historicalMisc', 'historicalNat', 'lgm', 'midHolocene', 'noVolc1960', 'noVolc1965', 'noVolc1970', 'noVolc1975', 'noVolc1980', 'noVolc1985', 'noVolc1990', 'noVolc1995', 'noVolc2000', 'noVolc2005', 'past1000', 'piControl', 'rcp26', 'rcp45', 'rcp60', 'rcp85', 'sst2020', 'sst2030', 'sst2090', 'sst2090rcp45', 'sstClim', 'sstClim4xCO2', 'sstClimAerosol', 'sstClimSulfate', 'volcIn2010']

validCordexExperiment = validCmip5Experiments + ['evaluation']


validCordexFrequecies = ['fx','sem','mon','day','6hr','3hr']
validSpecsFrequecies = ['fx','mon','day','6hr']
validSpecsExptFamilies = map( lambda x: string.split( x )[0], open( 'specs_vocabs/exptFamily.txt' ).readlines() )

validCordexDomainsL = [ 'SAM-44', 'CAM-44', 'NAM-44', 'EUR-44', 'AFR-44', 'WAS-44', 'EAS-44', 'CAS-44', 'AUS-44', 'ANT-44', 'ARC-44', 'MED-44']
validCordexDomainsLi = map( lambda x: x + 'i', validCordexDomainsL )
validCordexDomainsH = ['EUR-11']
validCordexDomains = validCordexDomainsL + validCordexDomainsLi + validCordexDomainsH

plevRequired = ['clh', 'clm', 'cll', 'ua850', 'va850', 'ta850', 'hus850', 'ua500', 'va500', 'ta500', 'zg500', 'ua200', 'va200', 'ta200', 'zg200']
plevBndsRequired = ['clh', 'clm', 'cll']
heightRequired = ['tas','tasmax','tasmin','huss','sfcWind','sfcWindmax','wsgsmax','uas','vas']


ii = open( 'cordex_vocabs/GCMModelName.txt' ).readlines()
validGcmNames = []
for l in ii:
  if l[0] != '#' and len( string.strip(l) ) > 0:
    validGcmNames.append( string.split(l)[0] )

ii = open( 'cordex_vocabs/RCMModelName.txt' ).readlines()
validRcmNames = []
validInstNames = []
for l in ii:
  if l[0] != '#' and len( string.strip(l) ) > 0:
    bits = string.split(l)
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

ii = open( 'cordex_vocabs/cordex_domains.csv' ).readlines()
keys = ['name','tag','res','grid_np_lon','grid_np_lat','nlon','nlat','w','e','s','n']
rotatedPoleGrids = {}
for l in ii[2:16]:
  bits = string.split(string.strip(l),',')
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
  bits = string.split(string.strip(l),',')
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

class readVocab:

  def __init__(self,dir):
    self.dir = dir

  def getSimpleList(self,file,bit=None):
    ii = open('%s/%s' % (self.dir,file) )
    oo = []
    for l in ii.readlines():
      if l[0] != '#':
        ll = string.strip(l)
        if bit == None:
          oo.append(ll)
        else:
          oo.append(string.split(ll)[bit])
    return oo

def getVocabs(pcfg):
  "Returns a dictionary of vocabulary details for the project provided."
  if pcfg.project == 'SPECS':
    vocabs = { 'variable':utils.mipVocab(pcfg), \
               'Conventions':utils.listControl( 'Conventions', ['CF-1.6'] ), \
               'frequency':utils.listControl( 'frequency', validSpecsFrequecies ), \
               'experiment_id':utils.patternControl( 'experiment_id', "(?P<val>.*)[0-9]{4}", list=validSpecsExptFamilies ), \
               'initialization_method':utils.patternControl( 'initialization_method', "[0-9]+" ), \
               'physics_version':utils.patternControl( 'physics_version', "[0-9]+" ), \
               'realization':utils.patternControl( 'realization', "[0-9]+" ), \
               'project_id':utils.listControl( 'project_id', ['SPECS'] ), \
               'modeling_realm':utils.listControl( 'realm', ['atmos', 'ocean', 'land', 'landIce', 'seaIce', 'aerosol', 'atmosChem', 'ocnBgchem'] ), \
               'series':utils.listControl( 'series', ['series1','series2'] ), \
             }
  elif pcfg.project == 'CCMI':
    vocabs = { 'variable':utils.mipVocab(pcfg), \
               'project_id':utils.listControl( 'project_id', ['CCMI'] ) }
  elif pcfg.project == '__dummy':
    vocabs = { 'variable':utils.mipVocab(pcfg,dummy=True) }
  else:
    vocabs = { 'variable':utils.mipVocab(pcfg), \
           'driving_experiment_name':utils.listControl( 'driving_experiment_name', validCordexExperiment ), \
           'project_id':utils.listControl( 'project_id', ['CORDEX'] ), \
           'CORDEX_domain':utils.listControl( 'CORDEX_domain',  validCordexDomains ), \
           'driving_model_id':utils.listControl( 'driving_model_id',  validGcmNames ), \
           'driving_model_ensemble_member':utils.patternControl( 'driving_model_ensemble_member',  'r[0-9]+i[0-9]+p[0-9]+' ), \
           'rcm_version_id':utils.patternControl( 'rcm_version_id',  '[a-zA-Z0-9-]+' ), \
           'model_id':utils.listControl( 'model_id',  validRcmNames ), \
           'institute_id':utils.listControl( 'institute_id',  validInstNames ), \
           'frequency':utils.listControl( 'frequency', validCordexFrequecies ) }

  return vocabs

class projectConfig:

  def __init__(self, project):
    knownProjects = ['CORDEX','SPECS','__dummy']
    assert project in knownProjects, 'Project %s not in knownProjects %s' % (project, str(knownProjects))

    self.project = project
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
      self.requiredGlobalAttributes = [ 'institute_id', 'contact', 'product', 'creation_date', 'tracking_id', \
              'experiment_id', 'series']
      self.requiredGlobalAttributes = lrdr.getSimpleList( 'globalAts.txt' )
      self.exptFamilies = lrdr.getSimpleList( 'exptFamily.txt', bit=0 )
      self.controlledGlobalAttributes = [ 'project_id','experiment_id', 'series','frequency','Conventions','modeling_realm', \
                       'initialization_method','physics_version','realization']
      self.globalAttributesInFn = [None,'@mip_id','model_id','@experiment_family','series','@ensemble']
## mip_id derived from global attribute Table_id (CMOR convention); experiment family derived from experiment_id, ensemble derived from rip attributes.
      self.requiredVarAttributes = ['long_name', 'standard_name', 'units']
      self.drsMappings = {'variable':'@var'}

    elif project == 'CCMI':
      lrdr = readVocab( 'ccmi_vocabs/')
      self.requiredGlobalAttributes = [ 'institute_id', 'contact', 'product', 'creation_date', 'tracking_id', \
              'experiment_id']
      self.requiredGlobalAttributes = lrdr.getSimpleList( 'globalAts.txt' )
      self.controlledGlobalAttributes = [ 'experiment_id', 'project' ]
      self.globalAttributesInFn = [None,'CORDEX_domain','driving_model_id','experiment_id','driving_model_ensemble_member','model_id','rcm_version_id']
      self.requiredVarAttributes = ['long_name', 'standard_name', 'units']
      self.drsMappings = {'variable':'@var'}

    elif project == '__dummy':
      self.requiredGlobalAttributes = map( lambda x: 'ga%s' % x, range(10) )
      self.controlledGlobalAttributes = [ ]
      self.globalAttributesInFn = [None,'ga2', 'ga3', 'ga4' ]
      self.requiredVarAttributes = ['long_name', 'standard_name', 'units']
      self.drsMappings = {'variable':'@var'}

####### used in checkStandardDims

    self.plevRequired = plevRequired
    self.plevValues = plevValues
    self.heightRequired = heightRequired
    self.heightValues = heightValues
    self.heightRange = heightRange

####### used in checkGrids
    self.rotatedPoleGrids = rotatedPoleGrids
    self.interpolatedGrids = interpolatedGrids
    self.doCheckGrids = self.project in ['CORDEX',]

####### used in checkFileName (freqIndex also used in checkByVar)

    if self.project == 'CORDEX':
      self.fnPartsOkLen = [8,9]
      self.fnPartsOkFixedLen = [8,]
      self.fnPartsOkUnfixedLen = [9,]
      self.checkTrangeLen = True
      self.domainIndex = 1
      self.freqIndex = 7
    elif self.project == 'SPECS':
      self.fnPartsOkLen = [6,7]
      self.fnPartsOkFixedLen = [6,]
      self.fnPartsOkUnfixedLen = [7,]
      self.checkTrangeLen = False
      self.domainIndex = None
      self.freqIndex = 1
    elif self.project == '__dummy':
      self.fnPartsOkLen = [4,5]
      self.fnPartsOkFixedLen = [4,]
      self.fnPartsOkUnfixedLen = [5,]
      self.checkTrangeLen = False
      self.domainIndex = None
      self.freqIndex = 1


######## used in mipVocabs
    if self.project == 'CORDEX':
       self.mipVocabDir = 'cordex_vocabs/mip/'
       self.mipVocabTl = ['fx','sem','mon','day','6h','3h']
       self.mipVocabVgmap = {'6h':'6hr','3h':'3hr'}
       self.mipVocabFnpat = 'CORDEX_%s'
    elif self.project == 'SPECS':
       self.mipVocabDir = 'specs_vocabs/mip/'
       self.mipVocabTl = ['fx','Omon','Amon','Lmon','OImon','day','6hrLev']
       self.mipVocabVgmap = {}
       self.mipVocabFnpat = 'SPECS_%s'
    elif self.project == 'CCMI':
       self.mipVocabDir = 'ccmi_vocabs/mip/'
       self.mipVocabTl = ['fixed','annual','monthly','daily','hourly']
       self.mipVocabVgmap = {'fixed':'fx','annual':'yr','monthly':'mon','daily':'day','hourly':'hr'}
       self.mipVocabFnpat = 'CCMI1_%s_comp-v2.txt'
    else:
       self.mipVocabDir = None
       self.mipVocabTl = ['day', 't2']
       self.mipVocabVgmap = {}
       self.mipVocabFnpat = None
    self.mipVocabPars = [self.mipVocabDir, self.mipVocabTl, self.mipVocabVgmap, self.mipVocabFnpat]

######## used in checkByVar
    if self.project == 'CORDEX':
      self.groupIndex = 7
    elif self.project in ['SPECS','__dummy']:
      self.groupIndex = 1

    self.vocabs = getVocabs(self)
    if self.project == 'CCMI':
      self.vocabs['experiment_id'] = lrdr.getSimpleList( 'ccmi_elist.txt', bit=0 )

    assert self.project != 'CCMI', 'Not completely set up for CCMI yet'
