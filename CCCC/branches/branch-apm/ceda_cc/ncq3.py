# Based on ncquick.py, by - M. Neish 2008/09/21
# ncquick.py was released as part of CCMval3.0 
# - Read-only access
#####################################################
# Extended
# June 2014, Martin Juckes: 
# Added routines to read all attributes. 
# Refactored to creat a digest of file metadata: the digest is returned as a named-tuple, containing lists
# of named-tuples. This contains al the information in a clearly defined structure, but is not very convenient to
# browse because of lots of cross-referencing by object ids.
# The "Browser" class provides one method for extracting variable information.
#####################################################
#
# Examples:
#
## import ncq3.py

## file = ncq3.open( 'test.nc' )
## file.getDigest()
## ncq3.close(file)
## b = ncq3.Broswer( file.digest )
## print b.varsum( 'time' )

##
## dependency on ctypes: may not work on windows or mac because of different naming conventions
## for C library.
##

from ctypes import *
import collections, string
scriptVersion=0.5

libnetcdf = CDLL("libnetcdf.so")

# Some codes from the netcdf library
NC_GLOBAL = -1

NC_BYTE = 1
NC_CHAR = 2
NC_SHORT = 3
NC_INT = 4
NC_LONG = NC_INT
NC_FLOAT = 5
NC_DOUBLE = 6
NC_FORMAT_CLASSIC = 1
NC_FORMAT_64BIT   = 2
NC_FORMAT_NETCDF4 = 3
NC_FORMAT_NETCDF4_CLASSIC  = 4
## values copied from /usr/include/netcdf.h
class DummyClass(object):
  def __init__(self):
    pass
ncmappings = DummyClass()
ncmappings.fmt= { NC_FORMAT_CLASSIC:'Classic', NC_FORMAT_64BIT:'64Bit',
                  NC_FORMAT_NETCDF4:'NetCDF4', NC_FORMAT_NETCDF4_CLASSIC:'NetCDF4 Classic' }
## dictionary of c-types to deal with different data types 
ncmappings.tdict = { NC_BYTE:c_byte,
      NC_SHORT:c_short,
      NC_INT:c_int,
      NC_LONG:c_long,
      NC_FLOAT:c_float,
      NC_DOUBLE:c_double }

ncmappings.tdict2 = { NC_BYTE:"byte",
      NC_SHORT:"short",
      NC_INT:"int",
      NC_LONG:"long",
      NC_FLOAT:"float",
      NC_DOUBLE:"double" }

NC_MAX_NAME = 256

class NCError (Exception):
  def __init__ (self, value): self.value = value
  def __str__ (self): return self.value

## Added Group Id (gid).
Attribute = collections.namedtuple('Attribute', ['name','gid','vid', 'id', 'type', 'len', 'value'])
VarInfo = collections.namedtuple('VarInfo', ['name', 'gid','id', 'type', 'natts', 'ndims', 'dimids'])
Variable = collections.namedtuple('Variable', ['name', 'gid','id', 'type', 'natts', 'ndims', 'dimids','data'])
Dimension = collections.namedtuple('Dimension', ['name', 'gid','id', 'len', 'isunlimited'])
Fileinfo = collections.namedtuple('Fileinfo', ['filename','ndims','nvar','ngatts','ngrp','ncformat'] )
Sysinfo = collections.namedtuple('Sysinfo',['scriptVersion','libnetcdfVersion'])
FileDigest = collections.namedtuple('FileDigest',['sysinfo','fileinfo','dimensions','variables','attributes'])

class Browser(object):
  def __init__(self, digest):
    self.digest = digest
    self.varlist = []
    self.dimlist = []
    for v in digest.variables:
      self.varlist.append(v.name)
    for d in digest.dimensions:
      self.dimlist.append(d.name)

  def varsum(self,name):
    if name not in self.varlist:
      print '%s not in %s' % (name,str(self.varlist))
      return None
    v = self.digest.variables[self.varlist.index(name)]
    assert v.name == name, 'Error in internal logic: name mismatch in varsum'
    dlist = map( lambda x: self.digest.dimensions[x], v.dimids )
    dstr = map( lambda x: '%s[%s]' % (x.name, x.len), dlist )
    return '%s[%s]' % (name,string.join( dstr, ',') )
    

#FileDigest = collections.namedtuple('FileDigest',['sysinfo','fileinfo','dimensions','variables','attributes'])
class Browse(object):
  def __init__(self,fileobj):
    self.nc = fileobj
    for k in range(len(self.nc.variables)):
      assert self.nc.variables[k].id == k, 'Internal error: index does not match variable id'

    self._ll = []
    self._vdict = {}
    self._ddict = {}
    for v in self.nc.variables:
      self._ll.append( [] )
    self._gal = []
    tl = None
    ti = -2
    for a in self.nc.attributes:
      if a.vid != -1:
        assert a.id == len(self._ll[a.vid]), 'Unexpected attribute id: %s -- %s' % (str(a),str(self._ll[a.vid]) )
        self._ll[a.vid].append( a )
      else:
        self._gal.append( a )
    for v in self.nc.variables:
      self._vdict[v.name] = (v,map(lambda x: x.name,self._ll[v.id]) )
    for d in self.nc.dimensions:
      self._ddict[d.name] = d
         
class File(object):
  def __init__ (self, name, id) :
    self.name = name
    self.id = id
    self.vars = None
    self.dimensions = {}
    self.dimensions_ex = {}
## use "restype" to change default handling of function return values (default is as c_int) 
    libnetcdf.nc_inq_libvers.restype = c_char_p
    self.nclibversion = libnetcdf.nc_inq_libvers()
    iformat = c_int()
    err = libnetcdf.nc_inq_format( id, byref(iformat) )
    if err != 0: raise NCError("can't read file format")
    self.fileformat = iformat.value

## extension by Martin Juckes, June 2014 ##
  def nc_int(self) :
    ndims = c_int()
    nvars = c_int()
    ngatts = c_int()
    unlimdimid = c_int()

    err = libnetcdf.nc_inq(self.id, byref(ndims), byref(nvars), byref(ngatts), byref(unlimdimid));
    if err != 0: raise NCError("can't read ndims etc in file '"+self.name+"'")
    self.ndims = ndims.value
    self.nvars = nvars.value
    self.ngatts = ngatts.value
    self.unlimdimid = unlimdimid.value
##Fileinfo = collections.namedtuple('Fileinfo', ['filename','ndims','nvar','ngatts','ngrp','ncformat'] )
    self.fileinfo = Fileinfo( self.name, ndims.value, nvars.value, ngatts.value, 0, self.fileformat )
    return self.fileinfo

  def getDigest(self,props=True, full=True):
    self.nc_int()
    self.dims()
    self.varnames(props=props, full=full)
    self.allatts()

  def dims(self):
     self.dimensions = []
     for i in range(self.ndims):
        len = c_int()
        libnetcdf.nc_inq_dimlen(self.id, i, byref(len))
        name = create_string_buffer(NC_MAX_NAME+1)
        libnetcdf.nc_inq_dimname(self.id, i, name)
        self.dimensions.append( Dimension( name.value, 0, i, len.value, i == self.unlimdimid ) )
     return self.dimensions

  def varnames(self,props=False,full=False,maxrank=2):
     l = []
     self.vars = []
     for i in range(self.nvars):
        name = create_string_buffer(NC_MAX_NAME+1)
        libnetcdf.nc_inq_varname(self.id, i, name)
        l.append( name.value )
        if props:
          type = c_int()
          libnetcdf.nc_inq_vartype(self.id, i, byref(type))
          natts = c_int()
          libnetcdf.nc_inq_varnatts(self.id, i, byref(natts));
          ndims = c_int()
          libnetcdf.nc_inq_varndims(self.id, i, byref(ndims));
          dimids = (c_int*ndims.value)()
          libnetcdf.nc_inq_vardimid (self.id, i, dimids);
          if full:
            tt = ncmappings.tdict.get( type.value, None )
            if tt == None: raise NCError("unknown data type")
            len = 1
            for d in list(dimids):
              len *= self.dimensions[d].len
            if ndims.value <= maxrank:
              data = (c_double*len)()
              err = libnetcdf.nc_get_var_double(self.id, i, data)
              self.vars.append( Variable( name.value, 0, i, ncmappings.tdict2[type.value], natts.value, ndims.value, list(dimids), data[:] ) )
            else:
              self.vars.append( Variable( name.value, 0, i, ncmappings.tdict2[type.value], natts.value, ndims.value, list(dimids), None ) )
          else:
            self.vars.append( VarInfo( name.value, 0, i, type.value, natts.value, ndims.value, list(dimids) ) )
     return self.vars

  def allatts(self):
     self.alla = []
     for aid in range(self.ngatts):
       self.alla.append(self.atts ( aid, vid=NC_GLOBAL) )
     for v in self.vars:
       for aid in range(v.natts):
         self.alla.append(self.atts ( aid, vid=v.id)) 

  def info(self):
    self.sysinfo = Sysinfo( scriptVersion, self.nclibversion )
    self.digest = FileDigest( self.sysinfo, self.fileinfo, self.dimensions, self.vars, self.alla )
##Sysinfo = collections.namedtuple('Sysinfo',['scriptVersion','libnetcdfVersion'])
#FileDigest = collections.namedtuple('FileDigest',['sysinfo','fileinfo','dimensions','variables','attributes'])

  def attnames(self,varid=NC_GLOBAL):
     l = []
     for i in range(self.ngatts):
        name = create_string_buffer(NC_MAX_NAME+1)
        libnetcdf.nc_inq_attname(self.id, varid, i, name)
        l.append( name.value )
     if varid == NC_GLOBAL:
       self.gatts = tuple(l)
     else:
       if self.vars == None:
         self.varnames()
       self.vadict[self.vars[varid]] = tuple(l)
     return tuple(l)

  def atts (self, aid, vid=NC_GLOBAL) :
    cname = create_string_buffer(NC_MAX_NAME+1)
    libnetcdf.nc_inq_attname(self.id, vid, aid, cname)
    name=cname.value
    len = c_int()
    type = c_int()
    err = libnetcdf.nc_inq_att (self.id, vid, c_char_p(name), 
                                byref(type), byref(len))
    if err != 0: raise NCError("can't find attribute '"+name+"' in var '"+str(vid)+"'")
    type = type.value
    len = len.value

    if type == NC_CHAR:
        data = create_string_buffer(len)
        err = libnetcdf.nc_get_att_text (self.id, vid,
                                     c_char_p(name), data)
        if err != 0: raise NCError("can't read char attribute")
        return Attribute( name, 0, vid, aid, type, len, data.value )

    else:
      tt = ncmappings.tdict.get( type, None )
      if tt == None: raise NCError("unknown data type")
      t2 = ncmappings.tdict2.get( type, None )
      if len > 1:
        data = (tt*len)()
        err = libnetcdf.nc_get_att(self.id, vid, c_char_p(name), data)
        if err != 0: raise NCError( 'Error reading attribute value %s, type:%s' % (name,type) )
        return Attribute( name, 0, vid, aid, t2, len, data )
      else:
        data = tt()
        err = libnetcdf.nc_get_att(self.id, vid, c_char_p(name), byref(data))
        if err != 0: raise NCError( 'Error reading attribute value %s, type:%s' % (name,type) )
        dv = data.value
        return Attribute( name, 0, vid, aid, t2, len, dv )

## end of extension ##

def open (filename) :
  fileid = c_int()
  err = libnetcdf.nc_open (c_char_p(filename), 0, byref(fileid))
  if err != 0: raise NCError("can't open file '"+filename+"'")
  return File (filename, fileid)

def close (file) :
  file.info()
  err = libnetcdf.nc_close (file.id)
  if err != 0: raise NCError("can't close file '"+file.name+"'")



