
# Standard library imports
import string, pkgutil

# Third party imports

#### netcdf --- currently support cdms2, python-netCDF4 and Scientific

l = pkgutil.iter_modules()
ll = map( lambda x: x[1], l )

supportedNetcdf = ['cdms2','netCDF4','Scientific']

installedSupportedNetcdf = []

for x in supportedNetcdf:
  if x in ll:
    installedSupportedNetcdf.append( x )

if len(installedSupportedNetcdf) > 0:
  try: 
    exec 'import %s' % installedSupportedNetcdf[0]
    ncLib = installedSupportedNetcdf[0]
  except:
    print 'Failed to install %s' % installedSupportedNetcdf[0]
    ncLib = None
else:
  print """No supported netcdf module found.
         Supported modules are %s.
         Execution my fail, depending on options chosen.
         """ % str(supportedNetcdf)
  ncLib = None

if ncLib == 'Scientific':
  from Scientific.IO import NetCDF as ncdf

## end of netcdf import.

class fileMetadata:

  def __init__(self,dummy=False,attributeMappingsLog=None):
     
     self.dummy = dummy
     self.atMapLog = attributeMappingsLog
     if self.atMapLog == None:
       self.atMapLog = open( '/tmp/cccc_atMapLog.txt', 'a' )

  def close(self):
    self.atMapLog.close()

  def loadNc(self,fpath):
    self.fpath = fpath
    self.fn = string.split( fpath, '/' )[-1]
    self.fparts = string.split( self.fn[:-3], '_' )
    self.ga = {}
    self.va = {}
    self.da = {}
    if self.dummy:
      self.makeDummyFileImage()
      return
    if ncLib == 'cdms2':
      self.loadNc__Cdms(fpath)
    elif ncLib == 'netCDF4':
      self.loadNc__Netcdf4(fpath)
    elif ncLib == 'Scientific':
      self.loadNc__Scientific(fpath)
    else:
      raise 'No supported netcdf module assigned'

  def loadNc__Cdms(self,fpath):
    self.nc = cdms2.open( fpath )
    for k in self.nc.attributes.keys():
      self.ga[k] = self.nc.attributes[k]
      if len( self.ga[k] ) == 1:
        self.ga[k] = self.ga[k][0]
    for v in self.nc.variables.keys():
      self.va[v] = {}
      for k in self.nc.variables[v].attributes.keys():
        x = self.nc.variables[v].attributes[k]
     ## returns a list for some scalar attributes.
        if type(x) == type([]) and len(x) == 1:
          x = x[0]
        self.va[v][k] = x
      self.va[v]['_type'] = str( self.nc.variables[v].dtype )
      if v in ['plev','plev_bnds','height']:
        x = self.nc.variables[v].getValue().tolist()
        if type(x) != type([]):
          x = [x]
        self.va[v]['_data'] = x
        ### Note: returns a scalar if data has a scalar value.

    for v in self.nc.axes.keys():
      self.da[v] = {}
      for k in self.nc.axes[v].attributes.keys():
        self.da[v][k] = self.nc.axes[v].attributes[k]
      self.da[v]['_type'] = str( self.nc.axes[v].getValue().dtype )
      self.da[v]['_data'] = self.nc.axes[v].getValue().tolist()
      
    self.nc.close()

###
### attributes in .__dict__ dictionary
### variables in .variables dicttionary
### dimension lengths in .dimensions
### <variable>.getValue() returns an numpy.ndarray
### data type in <variable>.getValue().dtype
### for scalar variables, <variable>.getValue().tolist() returns a scalar.
###
  def loadNc__Scientific(self,fpath):
    self.nc = ncdf.NetCDFFile( fpath, 'r' )
    for k in self.nc.__dict__.keys():
      self.ga[k] = self.nc.__dict__[k]
      ##if len( self.ga[k] ) == 1:
        ##self.ga[k] = self.ga[k][0]
    for v in self.nc.variables.keys():
      if v not in self.nc.dimensions.keys():
        self.va[v] = {}
        for k in self.nc.variables[v].__dict__.keys():
          self.va[v][k] = self.nc.variables[v].__dict__[k]
        self.va[v]['_type'] = str( self.nc.variables[v].getValue().dtype )
        if v in ['plev','plev_bnds','height']:
        ### Note: returns a scalar if data has a scalar value.
          x = self.nc.variables[v].getValue().tolist()
          if type(x) != type([]):
            x = [x]
          self.va[v]['_data'] = x

    for v in self.nc.dimensions.keys():
      self.da[v] = {}
      if v in self.nc.variables.keys():
        for k in self.nc.variables[v].__dict__.keys():
          self.da[v][k] = self.nc.variables[v].__dict__[k]
        self.da[v]['_type'] = str( self.nc.variables[v].getValue().dtype )
        self.da[v]['_data'] = self.nc.variables[v].getValue().tolist()
      else:
        self.da[v]['_type'] = 'index (no data variable)'
      
    self.nc.close()

  def loadNc__Netcdf4(self,fpath):
    self.nc = netCDF4.Dataset(fpath, 'r')
    for k in self.nc.ncattrs():
      self.ga[k] = self.nc.getncattr(k)
      if len( self.ga[k] ) == 1:
        self.ga[k] = self.ga[k][0]
    for v in self.nc.variables.keys():
      if v not in self.nc.dimensions.keys():
        self.va[v] = {}
        for k in self.nc.variables[v].ncattrs():
          self.va[v][k] = self.nc.variables[v].getncattr(k)
        self.va[v]['_type'] = str( self.nc.variables[v].datatype )
        if v in ['plev','plev_bnds','height']:
          self.va[v]['_data'] = self.nc.variables[v][:].tolist()

    for v in self.nc.dimensions.keys():
      self.da[v] = {}
      if v in self.nc.variables.keys():
        for k in self.nc.variables[v].ncattrs():
          self.da[v][k] = self.nc.variables[v].getncattr(k)
        try:
          self.da[v]['_type'] = str( self.nc.variables[v].dtype )
        except:
          self.da[v]['_type'] = str( self.nc.variables[v].datatype )

        self.da[v]['_data'] = self.nc.variables[v][:].tolist()
      else:
        self.da[v]['_type'] = 'index (no data variable)'
      
    self.nc.close()

  def makeDummyFileImage(self):
    for k in range(10):
      self.ga['ga%s' % k] =  str(k)
    for v in [self.fparts[0],]:
      self.va[v] = {}
      self.va[v]['standard_name'] = 's%s' % v
      self.va[v]['long_name'] = v
      self.va[v]['cell_methods'] = 'time: point'
      self.va[v]['units'] = '1'
      self.va[v]['_type'] = 'float32'

    for v in ['lat','lon','time']:
      self.da[v] = {}
      self.da[v]['_type'] = 'float64'
      self.da[v]['_data'] = range(5)
    dlist = ['lat','lon','time']
    svals = lambda p,q: map( lambda y,z: self.da[y].__setitem__(p, z), dlist, q )
    svals( 'standard_name', ['latitude', 'longitude','time'] )
    svals( 'long_name', ['latitude', 'longitude','time'] )
    svals( 'units', ['degrees_north', 'degrees_east','days since 19590101'] )

  def applyMap( self, mapList, globalAttributesInFn, log=None ):
    for m in mapList:
      if m[0] == 'am001':
        if m[1][0][0] == "@var":
          if m[1][0][1] in self.va.keys():
            this = self.va[m[1][0][1]]
            apThis = True
            for c in m[1][1:]:
              if c[0] not in this.keys():
                apThis = False
              elif c[1] != this[c[0]]:
                apThis = False
            if m[2][0] != '':
              targ = m[2][0]
            else:
              targ = m[1][-1][0]
            if apThis:
              if log != None:
                log.info( 'Setting %s to %s' % (targ,m[2][1]) )
              ##print 'Setting %s:%s to %s' % (m[1][0][1],targ,m[2][1])
              thisval = self.va[m[1][0][1]].get( targ, None )
              self.va[m[1][0][1]][targ] = m[2][1]
              self.atMapLog.write( '@var:"%s","%s","%s","%s","%s"\n' % (self.fpath, m[1][0][1], targ, thisval, m[2][1] ) )

        elif m[1][0][0] == "@ax":
          ##print 'checking dimension ',m[1][0][1], self.da.keys()
          if m[1][0][1] in self.da.keys():
            ##print 'checking dimension [2]',m[1][0][1]
            this = self.da[m[1][0][1]]
            apThis = True
            for c in m[1][1:]:
              if c[0] not in this.keys():
                apThis = False
              elif c[1] != this[c[0]]:
                apThis = False
            if m[2][0] != '':
              targ = m[2][0]
            else:
              targ = m[1][-1][0]
            if apThis:
              if log != None:
                log.info( 'Setting %s to %s' % (targ,m[2][1]) )
              ##print 'Setting %s:%s to %s' % (m[1][0][1],targ,m[2][1])
              thisval = self.va[m[1][0][1]].get( targ, None )
              self.da[m[1][0][1]][targ] = m[2][1]
              self.atMapLog.write( '@ax:"%s","%s","%s","%s","%s"\n' % (self.fpath, m[1][0][1], targ, thisval, m[2][1]) )
        elif m[1][0][0] == "@":
            this = self.ga
            apThis = True
## apply change where attribute absent only
            for c in m[1][1:]:
              if c[0] not in this.keys():
                if c[1] != '__absent__':
                  apThis = False
              elif c[1] == '__absent__' or c[1] != this[c[0]]:
                apThis = False
            if m[2][0] != '':
              targ = m[2][0]
            else:
              targ = m[1][-1][0]
            if apThis:
              if log != None:
                log.info( 'Setting %s to %s' % (targ,m[2][1]) )
              ##print 'Setting %s to %s' % (targ,m[2][1])
              thisval = self.ga.get( targ, None )
              self.ga[targ] = m[2][1]
              self.atMapLog.write( '@:"%s","%s","%s","%s","%s"\n' % (self.fpath, 'ga', targ, thisval, m[2][1]) )
##
              if targ in globalAttributesInFn:
                i = globalAttributesInFn.index(targ)
                thisval = self.fparts[ i ]
                self.fparts[ i ] = m[2][1]
                self.fn = string.join( self.fparts, '_' ) + '.nc'
                self.atMapLog.write( '@fn:"%s","%s","%s"\n' % (self.fpath, thisval, m[2][1]) )
        else:
          print 'Token %s not recognised' % m[1][0][0]
